from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import Db
from app.core.taxonomy import ExecutionStatus, Provider
from app.repositories import executions
from app.schemas.executions import Execution

router = APIRouter(prefix="/api/executions", tags=["executions"])


@router.get("")
def list_executions(
    db: Db,
    provider: Provider | None = None,
    status: ExecutionStatus | None = None,
    ticket_id: Annotated[str | None, Query(max_length=50)] = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict:
    """Every AI attempt, including failures, newest first. Payloads are on the detail route."""
    items, total = executions.search(
        db,
        filters={"provider": provider, "status": status, "ticket_id": ticket_id},
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{execution_id}", response_model=Execution)
def get_execution(execution_id: str, db: Db):
    """One attempt in full: input, redacted payloads, result, usage, rates and any error."""
    execution = executions.get(db, execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution
