from pydantic import BaseModel


class ImportRowError(BaseModel):
    row: int  # 1-based data row number, not counting the header
    field: str | None = None
    message: str


class ImportSummary(BaseModel):
    dry_run: bool = False
    total_rows: int
    imported: int = 0  # in a dry run: rows that would be imported
    invalid: int = 0
    duplicates_skipped: int = 0
    errors: list[ImportRowError] = []
    duplicate_rows: list[int] = []
    imported_ticket_ids: list[str] = []
    preview: list[dict] = []  # dry run only: the first rows that would be imported
