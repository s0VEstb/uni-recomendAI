from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.university import Program
from app.db.models.university import University
from app.db.models.fee_and_admission import ProgramFee
from app.db.models.tag import ProgramTag
from app.db.models.user import SubmissionTag, SurveySubmission

class RecommendationRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_candidates(
        self,
        *,
        ort_score: int,
        budget_max: int | None,
        tag_ids: list[int],
        limit: int = 50,
    ):
        # базовый query: Program + University
        q = (
            select(Program, University)
            .join(University, Program.university_id == University.id)
        )

        # 1) фильтр по бюджету (если есть таблица fees)
        if budget_max is not None:
            q = (
                q.join(ProgramFee, ProgramFee.program_id == Program.id)
                .where(ProgramFee.contract_fee <= budget_max)
            )

        # 2) фильтр по тэгам (если юзер выбрал теги)
        if tag_ids:
            q = (
                q.join(ProgramTag, ProgramTag.program_id == Program.id)
                .where(ProgramTag.tag_id.in_(tag_ids))
            )

        # 3) фильтр по ОРТ (если есть поле min_ort / requirement)
        # если у тебя есть ProgramAdmission.min_ort, то добавим так:
        # q = q.join(ProgramAdmission, ProgramAdmission.program_id == Program.id)\
        #      .where(ProgramAdmission.min_ort <= ort_score)

        q = q.limit(limit)

        res = await self.db.execute(q)
        return res.all()  # list[(Program, University)]