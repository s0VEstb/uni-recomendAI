from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.university import Program
from app.db.models.university import University
from app.db.models.fee_and_admission import ProgramFee, ProgramAdmission
from app.db.models.tag import ProgramTag
from app.db.enums import Language

# Год приёма для фильтрации fee и admission
ADMISSION_YEAR = 2026

# Маппинг city (enum value) -> названия городов в БД (университеты могут использовать разные варианты)
CITY_TO_DB_NAMES: dict[str, list[str]] = {
    "bishkek": ["Бишкек", "Bishkek"],
    "osh": ["Ош", "Osh"],
    "jalal_abad": ["Джалал-Абад", "Jalal-Abad"],
    "karakol": ["Каракол", "Karakol"],
    "tokmok": ["Токмок", "Tokmok"],
    "naryn": ["Нарын", "Naryn"],
    "batken": ["Баткен", "Batken"],
    "talas": ["Талас", "Talas"],
    "uzgen": ["Узген", "Uzgen"],
    "kara_balta": ["Кара-Балта", "Kara-Balta"],
    "balykchy": ["Балыкчы", "Balykchy"],
    "bazar_korgon": ["Базар-Коргон", "Bazar-Korgon"],
    "kyzyl_kiya": ["Кызыл-Кия", "Kyzyl-Kiya"],
    "tash_kumyr": ["Таш-Кумыр", "Tash-Kumyr"],
    "kant": ["Кант", "Kant"],
    "isfana": ["Исфана", "Isfana"],
    "mailuu_suu": ["Майлуу-Суу", "Mailuu-Suu"],
    "kara_suu": ["Кара-Суу", "Kara-Suu"],
}


class RecommendationRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_candidates(
        self,
        *,
        ort_score: int,
        budget_max: int | None,
        tag_ids: list[int],
        city: str | None = None,
        language: Language | None = None,
        limit: int = 50,
    ):
        # базовый query: Program + University
        if tag_ids:
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

        # только активные программы
        q = q.where(Program.is_active == True)

        # 1) фильтр по городу (city != "other")
        if city and city != "other" and city in CITY_TO_DB_NAMES:
            city_names = CITY_TO_DB_NAMES[city]
            q = q.where(University.city.in_(city_names))

        # 2) фильтр по языку обучения
        if language is not None:
            q = q.where(Program.language == language)

        # 3) фильтр по бюджету
        if budget_max is not None:
            q = (
                q.join(ProgramFee, (ProgramFee.program_id == Program.id) & (ProgramFee.year == ADMISSION_YEAR))
                .where(ProgramFee.contract_fee <= budget_max)
            )

        # 4) фильтр по ОРТ: ort_min_score IS NULL или ort_min_score <= ort_score
        q = q.outerjoin(
            ProgramAdmission,
            (ProgramAdmission.program_id == Program.id) & (ProgramAdmission.year == ADMISSION_YEAR),
        )
        q = q.where(
            or_(
                ProgramAdmission.ort_min_score.is_(None),
                ProgramAdmission.ort_min_score <= ort_score,
            )
        )

        q = q.limit(limit)

        res = await self.db.execute(q)
        rows = res.all()

        if tag_ids:
            return [(r[0], r[1], (r[2] if r[2] is not None else 1.0)) for r in rows]
        return [(r[0], r[1], 0.0) for r in rows]