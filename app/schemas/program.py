from pydantic import BaseModel
from typing import Any


class UniversityBriefOut(BaseModel):
    id: int
    name: str
    city: str
    website: str
    photo_url: str | None = None

    model_config = {"from_attributes": True}


class ProgramFeeOut(BaseModel):
    id: int
    name: str
    year: int
    contract_fee: int
    currency: str

    model_config = {"from_attributes": True}


class ProgramAdmissionOut(BaseModel):
    id: int
    year: int
    ort_min_score: int | None
    requirements: dict[str, Any]
    deadlines: dict[str, Any]

    model_config = {"from_attributes": True}


class TagBriefOut(BaseModel):
    id: int
    slug: str
    title: str

    model_config = {"from_attributes": True}


class ProgramDetailOut(BaseModel):
    id: int
    name: str
    language: str
    study_form: str
    duration_years: int
    official_url: str | None
    university: UniversityBriefOut
    fees: list[ProgramFeeOut]
    admissions: list[ProgramAdmissionOut]
    tags: list[TagBriefOut]

    model_config = {"from_attributes": True}
