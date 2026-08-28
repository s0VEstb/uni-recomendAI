from pydantic import BaseModel, Field
from typing import Any

from app.schemas.survey import SurveySubmissionOut


class RecommendationReason(BaseModel):
    code: str
    message: str
    meta: dict[str, Any] = Field(default_factory=dict)


class ScoreBreakdown(BaseModel):
    """Разбивка финального скора по компонентам (каждый = компонент * вес)."""
    ort: float = 0.0     # вклад ОРТ proximity (max 0.35)
    tags: float = 0.0    # вклад тегов (max 0.35)
    budget: float = 0.0  # вклад бюджета (max 0.15)
    city: float = 0.0    # вклад города (max 0.10)
    extra: float = 0.0   # вклад доп. факторов (max 0.05)
    total: float = 0.0   # итоговый балл [0.0 – 1.0]


class ProgramOut(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class UniversityOut(BaseModel):
    id: int
    name: str
    city: str | None = None
    photo_url: str | None = None
    model_config = {"from_attributes": True}


class ProgramRecommendationOut(BaseModel):
    program: ProgramOut
    university: UniversityOut
    score: float
    reasons: list[RecommendationReason]
    score_breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)


class UniversityTopOut(BaseModel):
    university: UniversityOut
    score: float
    programs_count: int
    programs: list[ProgramRecommendationOut]


class SurveySubmitOut(BaseModel):
    message: str
    submission: SurveySubmissionOut
    universities_top: list[UniversityTopOut]