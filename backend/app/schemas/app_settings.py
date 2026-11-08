from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.core.taxonomy import Provider

# Letters, digits and . _ : / - only, so a saved name can never smuggle anything into a request.
ModelName = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*(/[A-Za-z0-9._:-]+)*$", max_length=128),
]
Label = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]


class Strict(BaseModel):
    # Unknown fields are refused, so API keys and connection details can never be set this way.
    model_config = ConfigDict(extra="forbid")


class SettingsUpdate(Strict):
    jev_model: ModelName = None
    llm_model: ModelName = None
    jev_escalation_threshold: float = Field(default=None, ge=0, le=1)
    bulk_concurrency: int = Field(default=None, ge=1, le=10)

    @model_validator(mode="after")
    def _not_empty(self):
        if not self.model_fields_set:
            raise ValueError("Nothing to update")
        return self


class PromptUpdate(Strict):
    instructions: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)
    ]


class TaxonomyUpdate(Strict):
    categories: dict[Label, list[Label]]

    @model_validator(mode="after")
    def _within_limits(self):
        # 2 to 16 at each level: Jev's choice questions accept no more and no fewer.
        if not 2 <= len(self.categories) <= 16:
            raise ValueError("Keep between 2 and 16 categories.")
        names = [sub for subs in self.categories.values() for sub in subs]
        for category, subs in self.categories.items():
            if not 2 <= len(subs) <= 16:
                raise ValueError(f"{category}: keep between 2 and 16 subcategories.")
        repeated = sorted({sub for sub in names if names.count(sub) > 1})
        if repeated:
            raise ValueError(f"Subcategories must be unique: {', '.join(repeated)}")
        return self


class PricingEntry(Strict):
    provider: Provider
    model: ModelName
    input_per_million: Decimal = Field(ge=0, max_digits=12, decimal_places=6)
    output_per_million: Decimal = Field(ge=0, max_digits=12, decimal_places=6)


class PricingUpdate(Strict):
    entries: list[PricingEntry] = Field(max_length=100)

    @model_validator(mode="after")
    def _once_each(self):
        keys = [(e.provider, e.model) for e in self.entries]
        if len(keys) != len(set(keys)):
            raise ValueError("Each provider and model can have only one set of rates.")
        return self
