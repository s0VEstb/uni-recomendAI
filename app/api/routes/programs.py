from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session
from app.db.models import University, Program, ProgramFee, ProgramAdmission, ProgramTag, Tag
from app.schemas.program import ProgramDetailOut, UniversityBriefOut, ProgramFeeOut, ProgramAdmissionOut, TagBriefOut

router = APIRouter()


@router.get("/universities/{university_id}/programs/{program_id}", response_model=ProgramDetailOut)
async def get_program_detail(
    university_id: int,
    program_id: int,
    db: AsyncSession = Depends(get_async_session),
):
    q = (
        select(Program)
        .where(Program.id == program_id, Program.university_id == university_id)
        .options(
            selectinload(Program.university),
            selectinload(Program.fees),
            selectinload(Program.admissions),
            selectinload(Program.tag_links).selectinload(ProgramTag.tag),
        )
    )
    res = await db.execute(q)
    program = res.scalar_one_or_none()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")

    uni = program.university
    fees = [
        ProgramFeeOut(
            id=f.id,
            name=f.name,
            year=f.year,
            contract_fee=f.contract_fee,
            currency=f.currency.value,
        )
        for f in program.fees
    ]
    admissions = [ProgramAdmissionOut.model_validate(a) for a in program.admissions]
    tags = [TagBriefOut.model_validate(link.tag) for link in program.tag_links if link.tag]

    return ProgramDetailOut(
        id=program.id,
        name=program.name,
        language=program.language.value,
        study_form=program.study_form.value,
        duration_years=program.duration_years,
        official_url=program.official_url,
        university=UniversityBriefOut.model_validate(uni),
        fees=fees,
        admissions=admissions,
        tags=tags,
    )
