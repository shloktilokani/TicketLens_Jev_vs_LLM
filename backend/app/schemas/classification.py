from datetime import datetime

from pydantic import BaseModel, model_validator

from app.core.taxonomy import TAXONOMY_VERSION, Category, Priority, Sentiment, is_valid_pair


class Classification(BaseModel):
    """The five fields both providers are compared on."""

    category: Category
    subcategory: str
    priority: Priority
    sentiment: Sentiment
    escalation_required: bool

    @model_validator(mode="after")
    def _check_pair(self):
        # Reject, never rewrite: an inconsistent pair must surface (requirements.md section 4).
        if not is_valid_pair(self.category, self.subcategory):
            raise ValueError(f"'{self.subcategory}' is not a subcategory of '{self.category}'")
        return self


class FinalClassification(Classification):
    """The operator's chosen answer. Only ever set by an explicit operator action."""

    selected_from_execution_id: str | None = None
    manually_edited: bool = False
    taxonomy_version: str = TAXONOMY_VERSION
    updated_at: datetime | None = None


class NormalizedResult(Classification):
    """One provider's validated output, in the shape the UI sees."""

    confidence: dict[str, float] = {}
    summary: str | None = None
    suggested_resolution: str | None = None
    unsupported_fields: list[str] = []
    warnings: list[str] = []
