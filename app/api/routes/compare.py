from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session
from app.db.models import Program, ProgramTag
from app.schemas.compare import CompareRequest, CompareResponse
from app.schemas.program import ProgramDetailOut, UniversityBriefOut, ProgramFeeOut, ProgramAdmissionOut, TagBriefOut

router = APIRouter()


@router.post("/", response_model=CompareResponse)
async def compare_programs(
    payload: CompareRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """Сравнение 2-5 программ по их ID."""
    q = (
        select(Program)
        .where(Program.id.in_(payload.program_ids))
        .options(
            selectinload(Program.university),
            selectinload(Program.fees),
            selectinload(Program.admissions),
            selectinload(Program.tag_links).selectinload(ProgramTag.tag),
        )
    )
    res = await db.execute(q)
    programs = res.scalars().all()

    if not programs:
        raise HTTPException(status_code=404, detail="Programs not found")

    # Сохраняем порядок как в запросе
    program_map = {p.id: p for p in programs}
    ordered = [program_map[pid] for pid in payload.program_ids if pid in program_map]

    result = []
    for program in ordered:
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

        result.append(ProgramDetailOut(
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
        ))

    return CompareResponse(programs=result)
