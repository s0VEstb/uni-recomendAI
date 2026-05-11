"""
Диагностический скрипт для проверки данных в БД и логики рекомендаций.
Запуск: python -m app.db.diagnose
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal
from app.db.models.university import Program, University
from app.db.models.fee_and_admission import ProgramFee, ProgramAdmission
from app.db.models.tag import Tag, ProgramTag
from app.db.repositories.recommendation_repo import RecommendationRepo


async def diagnose():
    async with AsyncSessionLocal() as db:
        print("=" * 60)
        print("ДИАГНОСТИКА БАЗЫ ДАННЫХ")
        print("=" * 60)

        # 1. Общее количество записей
        uni_count = (await db.execute(select(func.count(University.id)))).scalar()
        prog_count = (await db.execute(select(func.count(Program.id)))).scalar()
        tag_count = (await db.execute(select(func.count(Tag.id)))).scalar()
        fee_count = (await db.execute(select(func.count(ProgramFee.id)))).scalar()
        adm_count = (await db.execute(select(func.count(ProgramAdmission.id)))).scalar()
        from sqlalchemy import select as sa_select
        prog_tag_count = (await db.execute(sa_select(func.count('*')).select_from(ProgramTag))).scalar()

        print(f"\n📊 Общее количество записей:")
        print(f"   Университеты: {uni_count}")
        print(f"   Программы: {prog_count}")
        print(f"   Теги: {tag_count}")
        print(f"   ProgramFee (стоимость): {fee_count}")
        print(f"   ProgramAdmission (ОРТ пороги): {adm_count}")
        print(f"   ProgramTag (связи программа-тег): {prog_tag_count}")

        # 2. Проверим isActive программ
        active_count = (await db.execute(select(func.count(Program.id)).where(Program.is_active == True))).scalar()
        inactive_count = (await db.execute(select(func.count(Program.id)).where(Program.is_active == False))).scalar()
        print(f"\n✅ Активные программы: {active_count}")
        print(f"❌ Неактивные программы: {inactive_count}")

        # 3. Примеры программ с ценами и ОРТ
        print(f"\n💰 Примеры программ со стоимостью (ProgramFee):")
        res = await db.execute(
            select(Program.id, Program.name, University.name.label("uni_name"), ProgramFee.contract_fee, ProgramFee.year)
            .join(University, Program.university_id == University.id)
            .join(ProgramFee, ProgramFee.program_id == Program.id)
            .limit(5)
        )
        for row in res.all():
            print(f"   ID={row[0]}, '{row[1]}' ({row.uni_name}), fee={row[3]}, year={row[4]}")

        print(f"\n📝 Примеры программ с ОРТ порогами (ProgramAdmission):")
        res = await db.execute(
            select(Program.id, Program.name, University.name.label("uni_name"), ProgramAdmission.ort_min_score, ProgramAdmission.year)
            .join(University, Program.university_id == University.id)
            .join(ProgramAdmission, ProgramAdmission.program_id == Program.id)
            .limit(5)
        )
        for row in res.all():
            print(f"   ID={row[0]}, '{row[1]}' ({row.uni_name}), ort_min={row[3]}, year={row[4]}")

        # 4. Примеры тегов программ
        print(f"\n🏷️  Примеры ProgramTag (программа-тег):")
        res = await db.execute(
            select(Program.id, Program.name.label("prog_name"), Tag.title.label("tag_title"), ProgramTag.weight)
            .join(ProgramTag, ProgramTag.program_id == Program.id)
            .join(Tag, ProgramTag.tag_id == Tag.id)
            .limit(5)
        )
        for row in res.all():
            print(f"   Program ID={row[0]}, '{row.prog_name}', Tag='{row.tag_title}', weight={row[3]}")

        # 5. Города университетов
        print(f"\n🌍 Города университетов:")
        res = await db.execute(select(University.city, func.count(University.id)).group_by(University.city))
        for row in res.all():
            print(f"   {row[0] or 'NULL'}: {row[1]}")

        # 6. Языки программ
        print(f"\n🗣️  Языки программ:")
        res = await db.execute(select(Program.language, func.count(Program.id)).group_by(Program.language))
        for row in res.all():
            print(f"   {row[0] or 'NULL'}: {row[1]}")

        # 7. Тестовый запрос рекомендаций с разными параметрами
        print(f"\n" + "=" * 60)
        print("ТЕСТИРОВАНИЕ РЕКОМЕНДАЦИЙ")
        print("=" * 60)

        test_cases = [
            {"ort_score": 200, "budget_max": None, "tag_ids": [], "city": None, "language": None, "desc": "Без фильтров (орт=200, без бюджета, без тегов)"},
            {"ort_score": 200, "budget_max": 1000000, "tag_ids": [], "city": None, "language": None, "desc": "Бюджет=1,000,000"},
            {"ort_score": 100, "budget_max": 100000, "tag_ids": [], "city": None, "language": None, "desc": "Бюджет=100,000, ОРТ=100"},
        ]

        # Получим первые tag_ids для теста
        res_tags = await db.execute(select(Tag.id, Tag.title).limit(5))
        sample_tags = res_tags.all()
        if sample_tags:
            tag_ids = [t[0] for t in sample_tags[:3]]
            test_cases.append({
                "ort_score": 200, "budget_max": None, "tag_ids": tag_ids,
                "city": None, "language": None,
                "desc": f"С тегами {tag_ids} ({', '.join(t[1] for t in sample_tags[:3])})"
            })

        repo = RecommendationRepo(db)
        for tc in test_cases:
            print(f"\n🔍 Тест: {tc['desc']}")
            try:
                rows = await repo.find_candidates(
                    ort_score=tc["ort_score"],
                    budget_max=tc["budget_max"],
                    tag_ids=tc["tag_ids"],
                    city=tc["city"],
                    language=tc["language"],
                    limit=100,
                )
                print(f"   ✅ Найдено программ: {len(rows)}")
                if rows:
                    for r in rows[:3]:
                        prog, uni, tag_w, fee, ort_min = r
                        print(f"      - '{prog.name}' ({uni.name}), fee={fee}, ort_min={ort_min}, tag_weight={tag_w}")
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")

        # 8. Проверим ADMISSION_YEAR
        from app.core.security import ADMISSION_YEAR
        print(f"\n📅 ADMISSION_YEAR = {ADMISSION_YEAR}")
        res_years = await db.execute(select(ProgramFee.year, func.count(ProgramFee.id)).group_by(ProgramFee.year))
        years_data = res_years.all()
        if years_data:
            print(f"   Годы в ProgramFee: {[(r[0], r[1]) for r in years_data]}")
        res_years2 = await db.execute(select(ProgramAdmission.year, func.count(ProgramAdmission.id)).group_by(ProgramAdmission.year))
        years_adm = res_years2.all()
        if years_adm:
            print(f"   Годы в ProgramAdmission: {[(r[0], r[1]) for r in years_adm]}")

        print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(diagnose())
