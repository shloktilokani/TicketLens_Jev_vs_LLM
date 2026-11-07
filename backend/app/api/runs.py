from fastapi import APIRouter, HTTPException, Request
from starlette.concurrency import run_in_threadpool

from app.api.deps import Db
from app.core.taxonomy import Provider
from app.repositories import tickets
from app.schemas.comparisons import Comparison, ComparisonCreate
from app.schemas.executions import Execution
from app.services import comparisons
from app.services.executions import run

router = APIRouter(tags=["runs and comparisons"])


@router.post("/api/tickets/{ticket_id}/runs/{provider}", response_model=Execution)
async def run_provider(ticket_id: str, provider: Provider, request: Request, db: Db):
    """Run one provider on one ticket. Every attempt is recorded, including failures."""
    ticket = tickets.get(db, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    # Provider calls block; run them off the event loop so Jev and GPT can run side by side.
    return await run_in_threadpool(run, db, ticket, provider, request.app.state.settings)


@router.post("/api/comparisons", status_code=201, response_model=Comparison)
def create_comparison(data: ComparisonCreate, db: Db):
    """Compare finished Jev and GPT runs of one ticket. Never picks a winner."""
    try:
        return comparisons.create(db, data.ticket_id, data.jev_execution_id, data.gpt_execution_id)
    except comparisons.ComparisonError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from None
