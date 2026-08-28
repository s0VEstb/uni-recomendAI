from pydantic import BaseModel, Field
from typing import Any

from app.schemas.survey import SurveySubmissionOut


class RecommendationReason(BaseModel):
    code: str
    message: str
    meta: dict[str, Any] = Field(default_factory=dict)


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

class UniversityTopOut(BaseModel):
    university: UniversityOut
    score: float
    programs_count: int
    programs: list[ProgramRecommendationOut]

class SurveySubmitOut(BaseModel):
    message: str
    submission: SurveySubmissionOut
    universities_top: list[UniversityTopOut]