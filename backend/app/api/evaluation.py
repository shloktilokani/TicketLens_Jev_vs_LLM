from fastapi import APIRouter

from app.api.deps import Db
from app.services import evaluation

router = APIRouter(tags=["evaluation"])


@router.get("/api/evaluation")
def get_evaluation(db: Db) -> dict:
    """Accuracy of each side's latest real run against the labelled answers, with denominators."""
    return evaluation.summary(db)
