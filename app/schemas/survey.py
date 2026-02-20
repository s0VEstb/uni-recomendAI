from pydantic import BaseModel, field_validator, Field
from typing import Any
from app.db.enums import Language

MAP = {"ru": "russian", "kg": "kyrgyz", "en": "english", "tr": "turkish"}

class SurveySubmissionIn(BaseModel):
    ort_score: int
    budget_max: int | None = None
    city: str | None = None
    language: Language | None = None

    answers: dict[str, Any] = Field(default_factory=dict)
    tag_ids: list[int] = Field(default_factory=list)

    @field_validator("language", mode="before")
    @classmethod
    def normalize_language(cls, v):
        if isinstance(v, str):
            v = MAP.get(v, v)
        return v

class SurveySubmissionOut(BaseModel):
    id: int
    user_id: int
    ort_score: int
    budget_max: int | None
    city: str | None
    language: Language | None
    answers: dict

    model_config = {"from_attributes": True}