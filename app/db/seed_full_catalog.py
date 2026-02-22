import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal

from app.db.enums import Language, StudyForm, Currency, DocumentType
from app.db.models.university import University, Program
from app.db.models.document import Document
from app.db.models.tag import Tag, ProgramTag
from app.db.models.fee_and_admission import ProgramFee, ProgramAdmission

YEAR = 2026

# 10 университетов Кыргызстана
UNIS = [
    {"name": "Кыргызский государственный технический университет им. И. Раззакова", "city": "Бишкек", "website": "https://kstu.kg", "contacts": {}},
    {"name": "Американский университет в Центральной Азии", "city": "Бишкек", "website": "https://auca.kg", "contacts": {}},
    {"name": "Ошский государственный университет", "city": "Ош", "website": "https://oshsu.kg", "contacts": {}},
    {"name": "Бишкекский государственный университет", "city": "Бишкек", "website": "https://bsu.kg", "contacts": {}},
    {"name": "Кыргызский национальный университет им. Ж. Баласагына", "city": "Бишкек", "website": "https://knu.kg", "contacts": {}},
    {"name": "Кыргызский государственный университет строительства, транспорта и архитектуры", "city": "Бишкек", "website": "https://ksucta.kg", "contacts": {}},
    {"name": "Джалал-Абадский государственный университет", "city": "Джалал-Абад", "website": "https://jasu.kg", "contacts": {}},
    {"name": "Баткенский государственный университет", "city": "Баткен", "website": "https://basu.kg", "contacts": {}},
    {"name": "Нарынский государственный университет", "city": "Нарын", "website": "https://nsu.kg", "contacts": {}},
    {"name": "Иссык-Кульский государственный университет им. К. Тыныстанова", "city": "Каракол", "website": "https://iksu.kg", "contacts": {}},
    {"name": "Кыргызско-Турецкий университет «Манас»", "city": "Бишкек", "website": "https://manas.edu.kg", "contacts": {}},
    {"name": "Кыргызско-Российский Славянский университет", "city": "Бишкек", "website": "https://krsu.edu.kg", "contacts": {}},
    {"name": "Ошский технологический университет", "city": "Ош", "website": "https://ostu.kg", "contacts": {}},
    {"name": "Кыргызская государственная медицинская академия им. И. Ахунбаева", "city": "Бишкек", "website": "https://kgma.kg", "contacts": {}},
    {"name": "Университет Центральной Азии", "city": "Нарын", "website": "https://ucentralasia.org", "contacts": {}},
]

# Программы с весами тегов: [(slug, weight), ...] — чем выше weight, тем больше вклад в score.
# raw_score = budget_ok(1.0) + tag_sum + ort(1.0). Макс. программа = 100%, остальные — % от неё.
PROGRAMS = [
    # KSTU — 4 программы
    {"uni_website": "https://kstu.kg", "name": "Программная инженерия", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://kstu.kg/prog/se", "fee": 55000, "currency": Currency.KGS, "ort_min": 150, "tag_slugs": [("programming", 1.2), ("computer_science", 1.0), ("mathematics", 0.8)]},
    {"uni_website": "https://kstu.kg", "name": "Информационные системы", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://kstu.kg/prog/is", "fee": 50000, "currency": Currency.KGS, "ort_min": 145, "tag_slugs": [("programming", 1.0), ("computer_science", 1.0)]},
    {"uni_website": "https://kstu.kg", "name": "Автоматизация и управление", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://kstu.kg/prog/au", "fee": 48000, "currency": Currency.KGS, "ort_min": 140, "tag_slugs": [("physics", 0.6), ("mathematics", 1.0)]},
    {"uni_website": "https://kstu.kg", "name": "Строительство", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://kstu.kg/prog/st", "fee": 42000, "currency": Currency.KGS, "ort_min": 135, "tag_slugs": [("mathematics", 0.8)]},
    # AUCA — 4 программы
    {"uni_website": "https://auca.kg", "name": "Computer Science", "language": Language.en, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://auca.kg/cs", "fee": 120000, "currency": Currency.KGS, "ort_min": 165, "tag_slugs": [("programming", 1.5), ("computer_science", 1.0), ("mathematics", 1.0)]},
    {"uni_website": "https://auca.kg", "name": "Applied Mathematics", "language": Language.en, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://auca.kg/math", "fee": 110000, "currency": Currency.KGS, "ort_min": 160, "tag_slugs": [("mathematics", 1.0)]},
    {"uni_website": "https://auca.kg", "name": "Business Administration", "language": Language.en, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://auca.kg/ba", "fee": 115000, "currency": Currency.KGS, "ort_min": 155, "tag_slugs": [("business", 1.0), ("economics", 1.0)]},
    {"uni_website": "https://auca.kg", "name": "Psychology", "language": Language.en, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://auca.kg/psy", "fee": 105000, "currency": Currency.KGS, "ort_min": 150, "tag_slugs": [("psychology", 1.0), ("psychology_subject", 0.8)]},
    # Osh SU — 3 программы
    {"uni_website": "https://oshsu.kg", "name": "Компьютерная инженерия", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://oshsu.kg/ce", "fee": 45000, "currency": Currency.KGS, "ort_min": 140, "tag_slugs": [("programming", 1.0), ("computer_science", 1.0)]},
    {"uni_website": "https://oshsu.kg", "name": "Медицина", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 6, "official_url": "https://oshsu.kg/med", "fee": 65000, "currency": Currency.KGS, "ort_min": 155, "tag_slugs": [("medicine", 1.0), ("biology", 1.0)]},
    {"uni_website": "https://oshsu.kg", "name": "Экономика", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://oshsu.kg/eco", "fee": 40000, "currency": Currency.KGS, "ort_min": 130, "tag_slugs": [("economics", 1.0)]},
    # BSU — 3 программы
    {"uni_website": "https://bsu.kg", "name": "Программирование", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://bsu.kg/prog", "fee": 52000, "currency": Currency.KGS, "ort_min": 150, "tag_slugs": [("programming", 1.2), ("computer_science", 0.8)]},
    {"uni_website": "https://bsu.kg", "name": "Дизайн", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://bsu.kg/design", "fee": 48000, "currency": Currency.KGS, "ort_min": 140, "tag_slugs": [("design", 1.0), ("creativity", 0.8)]},
    {"uni_website": "https://bsu.kg", "name": "Журналистика", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://bsu.kg/jour", "fee": 44000, "currency": Currency.KGS, "ort_min": 135, "tag_slugs": [("writing", 1.0), ("communication", 0.6)]},
    # KNU — 4 программы
    {"uni_website": "https://knu.kg", "name": "Информатика", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://knu.kg/inf", "fee": 58000, "currency": Currency.KGS, "ort_min": 155, "tag_slugs": [("computer_science", 1.0), ("mathematics", 1.0)]},
    {"uni_website": "https://knu.kg", "name": "Математика", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://knu.kg/math", "fee": 50000, "currency": Currency.KGS, "ort_min": 160, "tag_slugs": [("mathematics", 1.0)]},
    {"uni_website": "https://knu.kg", "name": "История", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://knu.kg/hist", "fee": 42000, "currency": Currency.KGS, "ort_min": 140, "tag_slugs": [("history", 1.0), ("history_subject", 0.8)]},
    {"uni_website": "https://knu.kg", "name": "Филология", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://knu.kg/phil", "fee": 45000, "currency": Currency.KGS, "ort_min": 145, "tag_slugs": [("literature", 0.8), ("foreign_languages", 0.8)]},
    # KSUCTA — 3 программы
    {"uni_website": "https://ksucta.kg", "name": "Архитектура", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 5, "official_url": "https://ksucta.kg/arch", "fee": 62000, "currency": Currency.KGS, "ort_min": 150, "tag_slugs": [("design", 1.0), ("creativity", 0.8), ("art", 0.6)]},
    {"uni_website": "https://ksucta.kg", "name": "Строительство", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://ksucta.kg/build", "fee": 50000, "currency": Currency.KGS, "ort_min": 140, "tag_slugs": [("mathematics", 0.8)]},
    {"uni_website": "https://ksucta.kg", "name": "Транспорт", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://ksucta.kg/trans", "fee": 48000, "currency": Currency.KGS, "ort_min": 135, "tag_slugs": [("physics", 0.6)]},
    # JASU — 3 программы
    {"uni_website": "https://jasu.kg", "name": "Программирование", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://jasu.kg/prog", "fee": 38000, "currency": Currency.KGS, "ort_min": 150, "tag_slugs": [("programming", 1.0), ("computer_science", 0.8)]},
    {"uni_website": "https://jasu.kg", "name": "Педагогика", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://jasu.kg/ped", "fee": 32000, "currency": Currency.KGS, "ort_min": 130, "tag_slugs": [("communication", 0.8)]},
    {"uni_website": "https://jasu.kg", "name": "Агрономия", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://jasu.kg/agro", "fee": 35000, "currency": Currency.KGS, "ort_min": 125, "tag_slugs": [("biology", 0.8)]},
    # BASU — 2 программы
    {"uni_website": "https://basu.kg", "name": "Программирование", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://basu.kg/prog", "fee": 35000, "currency": Currency.KGS, "ort_min": 140, "tag_slugs": [("programming", 0.8), ("computer_science", 0.8)]},
    {"uni_website": "https://basu.kg", "name": "Экономика", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://basu.kg/eco", "fee": 32000, "currency": Currency.KGS, "ort_min": 125, "tag_slugs": [("economics", 0.8)]},
    # NSU — 2 программы
    {"uni_website": "https://nsu.kg", "name": "Программирование", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://nsu.kg/prog", "fee": 36000, "currency": Currency.KGS, "ort_min": 135, "tag_slugs": [("programming", 0.8), ("computer_science", 0.6)]},
    {"uni_website": "https://nsu.kg", "name": "Педагогика", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://nsu.kg/ped", "fee": 30000, "currency": Currency.KGS, "ort_min": 120, "tag_slugs": [("communication", 0.6)]},
    # IKSU — 3 программы
    {"uni_website": "https://iksu.kg", "name": "Туризм", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://iksu.kg/tour", "fee": 42000, "currency": Currency.KGS, "ort_min": 130, "tag_slugs": [("travel", 1.0), ("languages", 0.6)]},
    {"uni_website": "https://iksu.kg", "name": "Экология", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://iksu.kg/eco", "fee": 40000, "currency": Currency.KGS, "ort_min": 135, "tag_slugs": [("biology", 0.8), ("chemistry", 0.6)]},
    {"uni_website": "https://iksu.kg", "name": "Экономика", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://iksu.kg/econ", "fee": 38000, "currency": Currency.KGS, "ort_min": 128, "tag_slugs": [("economics", 0.8)]},
    # КТУ Манас — 4 программы (турецкий/русский)
    {"uni_website": "https://manas.edu.kg", "name": "Программная инженерия", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://manas.edu.kg/se", "fee": 65000, "currency": Currency.KGS, "ort_min": 155, "tag_slugs": [("programming", 1.2), ("computer_science", 1.0), ("mathematics", 0.8)]},
    {"uni_website": "https://manas.edu.kg", "name": "Международные отношения", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://manas.edu.kg/ir", "fee": 60000, "currency": Currency.KGS, "ort_min": 150, "tag_slugs": [("history", 0.8), ("foreign_languages", 1.0)]},
    {"uni_website": "https://manas.edu.kg", "name": "Турецкий язык и литература", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://manas.edu.kg/turk", "fee": 55000, "currency": Currency.KGS, "ort_min": 145, "tag_slugs": [("foreign_languages", 1.0), ("literature", 0.8)]},
    {"uni_website": "https://manas.edu.kg", "name": "Экономика", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://manas.edu.kg/eco", "fee": 58000, "currency": Currency.KGS, "ort_min": 148, "tag_slugs": [("economics", 1.0), ("business", 0.8)]},
    # КРСУ — 3 программы
    {"uni_website": "https://krsu.edu.kg", "name": "Информатика и вычислительная техника", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://krsu.edu.kg/ivt", "fee": 60000, "currency": Currency.KGS, "ort_min": 155, "tag_slugs": [("programming", 1.0), ("computer_science", 1.0), ("mathematics", 0.8)]},
    {"uni_website": "https://krsu.edu.kg", "name": "Юриспруденция", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://krsu.edu.kg/law", "fee": 55000, "currency": Currency.KGS, "ort_min": 150, "tag_slugs": [("critical_thinking", 0.8), ("communication", 0.6)]},
    {"uni_website": "https://krsu.edu.kg", "name": "Журналистика", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://krsu.edu.kg/jour", "fee": 50000, "currency": Currency.KGS, "ort_min": 145, "tag_slugs": [("writing", 1.0), ("communication", 0.8)]},
    # ОшТУ — 3 программы
    {"uni_website": "https://ostu.kg", "name": "Программирование", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://ostu.kg/prog", "fee": 42000, "currency": Currency.KGS, "ort_min": 145, "tag_slugs": [("programming", 1.0), ("computer_science", 0.8)]},
    {"uni_website": "https://ostu.kg", "name": "Пищевые технологии", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://ostu.kg/food", "fee": 38000, "currency": Currency.KGS, "ort_min": 130, "tag_slugs": [("chemistry", 0.8), ("cooking", 0.6)]},
    {"uni_website": "https://ostu.kg", "name": "Строительство", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://ostu.kg/build", "fee": 40000, "currency": Currency.KGS, "ort_min": 135, "tag_slugs": [("mathematics", 0.8)]},
    # КГМА — 3 программы
    {"uni_website": "https://kgma.kg", "name": "Лечебное дело", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 6, "official_url": "https://kgma.kg/med", "fee": 85000, "currency": Currency.KGS, "ort_min": 170, "tag_slugs": [("medicine", 1.2), ("biology", 1.0), ("chemistry", 0.8)]},
    {"uni_website": "https://kgma.kg", "name": "Стоматология", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 5, "official_url": "https://kgma.kg/dent", "fee": 90000, "currency": Currency.KGS, "ort_min": 168, "tag_slugs": [("medicine", 1.0), ("biology", 1.0)]},
    {"uni_website": "https://kgma.kg", "name": "Фармация", "language": Language.ru, "study_form": StudyForm.full_time, "duration_years": 5, "official_url": "https://kgma.kg/pharm", "fee": 75000, "currency": Currency.KGS, "ort_min": 160, "tag_slugs": [("chemistry", 1.0), ("biology", 0.8)]},
    # UCA — 3 программы (англ.)
    {"uni_website": "https://ucentralasia.org", "name": "Computer Science", "language": Language.en, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://ucentralasia.org/cs", "fee": 95000, "currency": Currency.KGS, "ort_min": 160, "tag_slugs": [("programming", 1.2), ("computer_science", 1.0), ("mathematics", 0.8)]},
    {"uni_website": "https://ucentralasia.org", "name": "Economics", "language": Language.en, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://ucentralasia.org/econ", "fee": 90000, "currency": Currency.KGS, "ort_min": 155, "tag_slugs": [("economics", 1.0), ("business", 0.8)]},
    {"uni_website": "https://ucentralasia.org", "name": "Communications and Media", "language": Language.en, "study_form": StudyForm.full_time, "duration_years": 4, "official_url": "https://ucentralasia.org/comm", "fee": 85000, "currency": Currency.KGS, "ort_min": 150, "tag_slugs": [("communication", 1.0), ("writing", 0.8)]},
]


def _photo_url_for_uni(website: str) -> str:
    """Placeholder: уникальное фото по website (можно заменить на реальные URL)."""
    seed = hash(website) % 1000
    return f"https://picsum.photos/seed/uni{seed}/160/120"

async def upsert_universities(db: AsyncSession) -> dict[str, University]:
    res = await db.execute(select(University))
    existing = {u.website: u for u in res.scalars().all()}

    for u in UNIS:
        website = u["website"]
        photo_url = u.get("photo_url") or _photo_url_for_uni(website)
        if website in existing:
            uni = existing[website]
            uni.name = u["name"]
            uni.city = u["city"]
            uni.contacts = u.get("contacts", {})
            uni.photo_url = photo_url
        else:
            uni = University(**u, photo_url=photo_url)
            db.add(uni)
            existing[website] = uni

    await db.commit()
    for uni in existing.values():
        if uni.id is None:
            await db.refresh(uni)
    return existing


async def get_or_create_document(
    db: AsyncSession,
    *,
    university_id: int,
    doc_type: DocumentType,
    year: int,
) -> Document:
    q = select(Document).where(
        Document.university_id == university_id,
        Document.doc_type == doc_type,
        Document.year == year,
    )
    doc = (await db.execute(q)).scalar_one_or_none()
    if doc:
        return doc

    title = f"Seed {doc_type.value} {year}"
    local_path = f"seed/{university_id}/{doc_type.value}_{year}.pdf"
    doc = Document(
        university_id=university_id,
        title=title,
        doc_type=doc_type,
        year=year,
        local_path=local_path,
        source_url=None,
        received_from="seed",
        checksum=None,
    )
    db.add(doc)
    await db.flush()
    return doc


async def upsert_program(
    db: AsyncSession,
    uni_id: int,
    p: dict,
) -> Program:
    q = select(Program).where(Program.university_id == uni_id, Program.name == p["name"])
    program = (await db.execute(q)).scalar_one_or_none()
    if program:
        program.language = p["language"]
        program.study_form = p["study_form"]
        program.duration_years = p["duration_years"]
        program.official_url = p["official_url"]
        program.is_active = True
        return program

    program = Program(
        university_id=uni_id,
        name=p["name"],
        language=p["language"],
        study_form=p["study_form"],
        duration_years=p["duration_years"],
        official_url=p["official_url"],
        is_active=True,
    )
    db.add(program)
    await db.flush()
    return program


async def upsert_fee(
    db: AsyncSession,
    *,
    program_id: int,
    year: int,
    fee: int,
    currency: Currency,
    source_document_id: int,
) -> None:
    q = select(ProgramFee).where(
        ProgramFee.program_id == program_id,
        ProgramFee.year == year,
        ProgramFee.name == "Contract",
    )
    pf = (await db.execute(q)).scalar_one_or_none()
    if not pf:
        pf = ProgramFee(
            program_id=program_id,
            name="Contract",
            year=year,
            contract_fee=int(fee),
            currency=currency,
            source_document_id=source_document_id,
            source_page_start=1,
            source_page_end=1,
        )
        db.add(pf)
    else:
        pf.contract_fee = int(fee)
        pf.currency = currency
        pf.source_document_id = source_document_id
        pf.source_page_start = 1
        pf.source_page_end = 1


async def upsert_admission(
    db: AsyncSession,
    *,
    program_id: int,
    year: int,
    ort_min: int | None,
    source_document_id: int,
) -> None:
    q = select(ProgramAdmission).where(
        ProgramAdmission.program_id == program_id,
        ProgramAdmission.year == year,
    )
    adm = (await db.execute(q)).scalar_one_or_none()
    if not adm:
        adm = ProgramAdmission(
            program_id=program_id,
            year=year,
            ort_min_score=ort_min,
            requirements={"seed": True},
            deadlines={"seed": True},
            source_document_id=source_document_id,
            source_page_start=1,
            source_page_end=1,
        )
        db.add(adm)
    else:
        adm.ort_min_score = ort_min
        adm.source_document_id = source_document_id
        adm.source_page_start = 1
        adm.source_page_end = 1


def _normalize_tag_slugs(slugs: list[str] | list[tuple[str, float]]) -> list[tuple[str, float]]:
    """Превращает [slug, ...] или [(slug, weight), ...] в [(slug, weight), ...]"""
    if not slugs:
        return []
    out: list[tuple[str, float]] = []
    for item in slugs:
        if isinstance(item, str):
            out.append((item, 1.0))
        else:
            out.append((item[0], float(item[1])))
    return out


async def ensure_program_tags(db: AsyncSession, program_id: int, slugs: list[str] | list[tuple[str, float]]) -> None:
    items = _normalize_tag_slugs(slugs)
    if not items:
        return

    slugs_list = [s for s, _ in items]
    tags = (await db.execute(select(Tag).where(Tag.slug.in_(slugs_list)))).scalars().all()
    tags_by_slug = {t.slug: t for t in tags}

    missing = [s for s in slugs_list if s not in tags_by_slug]
    if missing:
        raise RuntimeError(f"Missing tags in DB (run seed_tags first): {missing}")

    for slug, weight in items:
        tag = tags_by_slug[slug]
        q = select(ProgramTag).where(ProgramTag.program_id == program_id, ProgramTag.tag_id == tag.id)
        link = (await db.execute(q)).scalar_one_or_none()
        if not link:
            db.add(ProgramTag(program_id=program_id, tag_id=tag.id, weight=weight))
        else:
            link.weight = weight


async def seed(db: AsyncSession) -> None:
    # 0) проверим что теги уже есть
    any_tag = (await db.execute(select(Tag.id).limit(1))).scalar_one_or_none()
    if not any_tag:
        raise RuntimeError("Tags table is empty. Run: python -m app.db.seed_tags")

    unis = await upsert_universities(db)

    # 1) для каждого университета создадим по 2 документа
    fee_docs: dict[int, Document] = {}
    adm_docs: dict[int, Document] = {}

    for uni in unis.values():
        fee_docs[uni.id] = await get_or_create_document(
            db, university_id=uni.id, doc_type=DocumentType.fee_table, year=YEAR
        )
        adm_docs[uni.id] = await get_or_create_document(
            db, university_id=uni.id, doc_type=DocumentType.admission_rules, year=YEAR
        )

    # 2) программы + fee/admission + tags
    with db.no_autoflush:
        for p in PROGRAMS:
            uni = unis[p["uni_website"]]
            program = await upsert_program(db, uni.id, p)

            await upsert_fee(
                db,
                program_id=program.id,
                year=YEAR,
                fee=p["fee"],
                currency=p["currency"],
                source_document_id=fee_docs[uni.id].id,
            )

            await upsert_admission(
                db,
                program_id=program.id,
                year=YEAR,
                ort_min=p.get("ort_min"),
                source_document_id=adm_docs[uni.id].id,
            )

            await ensure_program_tags(db, program.id, p.get("tag_slugs", []))  # [(slug, weight), ...]

    await db.commit()


async def main() -> None:
    async with AsyncSessionLocal() as db:
        try:
            await seed(db)
        except Exception:
            await db.rollback()
            raise
    print("✅ Full catalog seeded (unis/programs/docs/fees/admissions/program_tags)")


if __name__ == "__main__":
    asyncio.run(main())