from fastapi import APIRouter

from app.core import taxonomy

router = APIRouter(prefix="/api/taxonomy", tags=["taxonomy"])


@router.get("")
def get_taxonomy() -> dict:
    """The canonical categories and enum values. The frontend reads these; it never copies them."""
    return taxonomy.as_dict()
