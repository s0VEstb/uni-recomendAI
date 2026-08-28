from pydantic import BaseModel, field_validator, Field
from typing import Any
from app.db.enums import Language, City

MAP = {"ru": "russian", "kg": "kyrgyz", "en": "english", "tr": "turkish"}

class SurveySubmissionIn(BaseModel):
    ort_score: int = Field(ge=0, le=245)
    budget_max: int | None = Field(default=None, ge=0)
    city: City | None = None
    language: Language | None = None

    notes: str | None = None
    needs_dorm: bool | None = None
    willing_to_relocate: bool | None = None

    answers: dict[str, Any] = Field(default_factory=dict)
    tag_ids: list[int] = Field(default_factory=list)

    @field_validator("language", mode="before")
    @classmethod
    def normalize_language(cls, v):
        if isinstance(v, str):
            v = MAP.get(v, v)
        return v

    @field_validator("city", mode="before")
    @classmethod
    def normalize_city(cls, v):
        if v is None or v == "":
            return None
        if isinstance(v, str) and v in [c.value for c in City]:
            return City(v)
        return v

class SurveySubmissionOut(BaseModel):
    id: int
    user_id: int
    ort_score: int
    budget_max: int | None
    city: str | None
    language: Language | None
    notes: str | None
    needs_dorm: bool | None
    willing_to_relocate: bool | None
    answers: dict
    tag_ids: list[int] = Field(default_factory=list)

    model_config = {"from_attributes": True}