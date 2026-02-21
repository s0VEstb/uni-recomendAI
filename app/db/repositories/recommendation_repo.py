from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.university import Program
from app.db.models.university import University
from app.db.models.fee_and_admission import ProgramFee
from app.db.models.tag import ProgramTag


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
        if tag_ids:
            # С JOIN по тегам — возвращаем вес каждого совпавшего тега
            q = (
                select(Program, University, ProgramTag.weight)
                .join(University, Program.university_id == University.id)
                .join(ProgramTag, ProgramTag.program_id == Program.id)
                .where(ProgramTag.tag_id.in_(tag_ids))
            )
        else:
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

        q = q.limit(limit)

        res = await self.db.execute(q)
        rows = res.all()

        if tag_ids:
            # (Program, University, weight | None)
            return [(r[0], r[1], (r[2] if r[2] is not None else 1.0)) for r in rows]
        # (Program, University, 0.0) — без тегов
        return [(r[0], r[1], 0.0) for r in rows]