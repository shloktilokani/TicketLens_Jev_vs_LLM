from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request

from app.api.deps import Db
from app.jobs import bulk
from app.repositories import bulk_jobs
from app.schemas.bulk_jobs import BulkJob, BulkJobCreate, BulkJobList

router = APIRouter(prefix="/api/bulk-jobs", tags=["bulk runs"])


@router.post("", status_code=202, response_model=BulkJob)
def create_bulk_job(data: BulkJobCreate, background: BackgroundTasks, request: Request, db: Db):
    """Start a bulk run. Poll GET /api/bulk-jobs/{job_id} for progress."""
    try:
        job = bulk.create(db, data)
    except bulk.BulkError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from None
    background.add_task(bulk.run_job, db, job["job_id"], request.app.state.settings)
    return job


@router.get("", response_model=BulkJobList)
def list_bulk_jobs(db: Db, limit: Annotated[int, Query(ge=1, le=200)] = 50):
    """Bulk runs, newest first."""
    return {"items": bulk_jobs.newest_first(db, limit), "total": bulk_jobs.count(db)}


@router.get("/{job_id}", response_model=BulkJob)
def get_bulk_job(job_id: str, db: Db):
    job = bulk_jobs.get(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Bulk run not found")
    return job
