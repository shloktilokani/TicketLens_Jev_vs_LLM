from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.repositories.database import DB_UNAVAILABLE_MESSAGE, is_reachable

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
def health() -> dict[str, str]:
    """Process health only; does not touch the database."""
    return {"status": "ok"}


@router.get("/ready", responses={503: {"description": "MongoDB is not reachable"}})
def ready(request: Request):
    """Database readiness: pings MongoDB."""
    if is_reachable(request.app.state.mongo):
        return {"status": "ready", "database": "ok"}
    return JSONResponse(
        status_code=503,
        content={
            "status": "unavailable",
            "database": "unavailable",
            "message": DB_UNAVAILABLE_MESSAGE,
        },
    )
