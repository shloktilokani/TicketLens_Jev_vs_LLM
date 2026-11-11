from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import Db
from app.services import dashboard

router = APIRouter(tags=["dashboard"])


@router.get("/api/dashboard")
def get_dashboard(db: Db) -> dict:
    """Ticket counts and Jev-vs-LLM metrics from stored real runs. Fake runs are excluded."""
    return dashboard.summary(db)


@router.get("/api/comparisons")
def list_comparisons(
    db: Db, limit: Annotated[int, Query(ge=1, le=1000)] = 100, ticket_id: str | None = None
) -> dict:
    """Stored comparisons, newest first, optionally for one ticket."""
    return dashboard.list_comparisons(db, limit, ticket_id)


@router.get("/api/comparisons/{comparison_id}")
def get_comparison(comparison_id: str, db: Db) -> dict:
    """One stored comparison with its ticket and both runs."""
    row = dashboard.detail(db, comparison_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Comparison not found")
    return row
