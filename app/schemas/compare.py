from pydantic import BaseModel, Field
from app.schemas.program import ProgramDetailOut


class CompareRequest(BaseModel):
    program_ids: list[int] = Field(..., min_length=2, max_length=5)


class CompareResponse(BaseModel):
    programs: list[ProgramDetailOut]
