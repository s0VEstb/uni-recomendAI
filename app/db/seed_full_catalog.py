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

UNIS = [
    {
        "name": "Kyrgyz State Technical University",
        "city": "Bishkek",
        "website": "https://kstu.kg",
        "contacts": {},
    },
    {
        "name": "American University of Central Asia",
        "city": "Bishkek",
        "website": "https://auca.kg",
        "contacts": {},
    },
    {
        "name": "Osh State University",
        "city": "Osh",
        "website": "https://oshsu.kg",
        "contacts": {},
    },
]

PROGRAMS = [
    {
        "uni_website": "https://kstu.kg",
        "name": "Software Engineering",
        "language": Language.ru,
        "study_form": StudyForm.full_time,
        "duration_years": 4,
        "official_url": "https://kstu.kg/programs/software-engineering",
        "fee": 55000,
        "currency": Currency.KGS,
        "ort_min": 150,
        "tag_slugs": ["programming", "computer_science"],
    },
    {
        "uni_website": "https://kstu.kg",
        "name": "Information Systems",
        "language": Language.ru,
        "study_form": StudyForm.full_time,
        "duration_years": 4,
        "official_url": "https://kstu.kg/programs/information-systems",
        "fee": 50000,
        "currency": Currency.KGS,
        "ort_min": 145,
        "tag_slugs": ["programming", "computer_science"],
    },
    {
        "uni_website": "https://auca.kg",
        "name": "Computer Science",
        "language": Language.en,
        "study_form": StudyForm.full_time,
        "duration_years": 4,
        "official_url": "https://auca.kg/en/academics/cs",
        "fee": 120000,
        "currency": Currency.KGS,
        "ort_min": 160,
        "tag_slugs": ["programming", "computer_science", "mathematics"],
    },
    {
        "uni_website": "https://auca.kg",
        "name": "Applied Mathematics",
        "language": Language.en,
        "study_form": StudyForm.full_time,
        "duration_years": 4,
        "official_url": "https://auca.kg/en/academics/applied-math",
        "fee": 110000,
        "currency": Currency.KGS,
        "ort_min": 155,
        "tag_slugs": ["mathematics"],
    },
    {
        "uni_website": "https://oshsu.kg",
        "name": "Computer Engineering",
        "language": Language.ru,
        "study_form": StudyForm.full_time,
        "duration_years": 4,
        "official_url": "https://oshsu.kg/programs/computer-engineering",
        "fee": 45000,
        "currency": Currency.KGS,
        "ort_min": 140,
        "tag_slugs": ["programming", "computer_science"],
    },
]


async def upsert_universities(db: AsyncSession) -> dict[str, University]:
    res = await db.execute(select(University))
    existing = {u.website: u for u in res.scalars().all()}

    for u in UNIS:
        website = u["website"]
        if website in existing:
            uni = existing[website]
            uni.name = u["name"]
            uni.city = u["city"]
            uni.contacts = u.get("contacts", {})
        else:
            uni = University(**u)
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