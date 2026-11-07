from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool

from app.api.deps import Db
from app.schemas.imports import ImportSummary
from app.services import csv_export
from app.services.csv_import import COLUMNS, CsvFileError, import_csv

router = APIRouter(tags=["imports and exports"])
MAX_BYTES = 5 * 1024 * 1024


def csv_download(text: str, filename: str) -> Response:
    return Response(
        content=text,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/api/imports/template")
def import_template() -> Response:
    """An empty CSV with the import columns (sample_tickets_template.csv)."""
    return csv_download(",".join(COLUMNS) + "\n", "ticketlens_import_template.csv")


@router.post(
    "/api/imports/tickets",
    response_model=ImportSummary,
    openapi_extra={
        "requestBody": {"required": True, "content": {"text/csv": {"schema": {"type": "string"}}}}
    },
)
async def import_tickets(request: Request, db: Db, dry_run: bool = False):
    """Import tickets from a CSV body. `dry_run=true` checks the file and saves nothing."""
    if int(request.headers.get("content-length") or 0) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="The file is larger than 5 MB.")
    content = await request.body()
    if len(content) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="The file is larger than 5 MB.")
    try:
        # PyMongo is synchronous; run it off the event loop.
        return await run_in_threadpool(import_csv, db, content, dry_run=dry_run)
    except CsvFileError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None


@router.get("/api/exports/{name}.csv")
def export_csv(name: Literal["tickets", "executions", "comparisons"], db: Db) -> Response:
    """Download as CSV. Payloads and secrets are never included."""
    return csv_download(csv_export.export(db, name), f"ticketlens_{name}.csv")
