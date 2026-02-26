import asyncio
import re
import hashlib
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.db.models.document import Document


def parse_main_links(text: str):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    out = []
    i = 0
    while i < len(lines):
        m = re.match(r"^(\d+)\)\s*(.*)$", lines[i])
        if m and i + 1 < len(lines) and lines[i + 1].startswith("http"):
            idx = int(m.group(1))
            title = m.group(2).strip()
            url = lines[i + 1].strip()
            out.append((idx, title, url))
            i += 2
        else:
            i += 1
    return out


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def slug_from_url(url: str) -> str:
    p = urlparse(url)
    parts = p.path.strip("/").split("/")
    return parts[-1] if parts else "document"


def filename_for_url(url: str) -> str:
    slug = slug_from_url(url)

    # ты оставил один scoring файл
    if slug == "auca_exams_scoring":
        return "auca_exams_scoring.txt"

    # normal case
    return f"{slug}.txt"


async def upsert_doc(db, *, university_id: int, year: int, doc_type: str, title: str, url: str | None, local_path: str | None, checksum: str | None):
    # уникальность по (uni, year, source_url) если url есть, иначе по title (для main_text)
    if url:
        stmt = select(Document).where(
            Document.university_id == university_id,
            Document.year == year,
            Document.source_url == url,
        )
    else:
        stmt = select(Document).where(
            Document.university_id == university_id,
            Document.year == year,
            Document.title == title,
        )

    res = await db.execute(stmt)
    doc = res.scalars().first()

    if not doc:
        doc = Document(
            university_id=university_id,
            year=year,
            doc_type=doc_type,
            title=title,
            source_url=url,
            local_path=local_path,
            checksum=checksum,
        )
        db.add(doc)
        await db.flush()
        return doc, True

    doc.title = title
    doc.doc_type = doc_type
    doc.source_url = url or doc.source_url
    doc.local_path = local_path or doc.local_path
    doc.checksum = checksum or doc.checksum
    await db.flush()
    return doc, False


async def main(*, university_id: int, year: int, base_dir: str, doc_type: str = "admission_rules"):
    base = Path(base_dir)
    links_path = base / "main_links.txt"
    main_text_path = base / "main_text.txt"

    if not links_path.exists():
        raise FileNotFoundError(f"main_links not found: {links_path}")

    items = parse_main_links(links_path.read_text(encoding="utf-8"))
    if not items:
        print("[WARN] main_links parsed empty")
        return

    async with AsyncSessionLocal() as db:
        created = updated = missing = 0

        # main_text (чат) как отдельный документ
        if main_text_path.exists():
            checksum = sha256_file(main_text_path)
            doc, is_created = await upsert_doc(
                db,
                university_id=university_id,
                year=year,
                doc_type=doc_type,  # чтобы не падать на enum
                title="AUCA: main_text (чат/сводка)",
                url=None,
                local_path=str(main_text_path.as_posix()),
                checksum=checksum,
            )
            print(f"[OK] main_text doc_id={doc.id} file={main_text_path.name}")
            created += int(is_created)
            updated += int(not is_created)

        # документы из main_links
        for idx, title, url in items:
            fname = filename_for_url(url)
            txt_path = base / fname

            local_path = None
            checksum = None
            if txt_path.exists():
                local_path = str(txt_path.as_posix())
                checksum = sha256_file(txt_path)
            else:
                print(f"[MISS] #{idx} {title} -> expected {fname}")
                missing += 1

            doc, is_created = await upsert_doc(
                db,
                university_id=university_id,
                year=year,
                doc_type=doc_type,
                title=title,
                url=url,
                local_path=local_path,
                checksum=checksum,
            )
            print(f"[OK] doc_id={doc.id} | #{idx} {title} | file={txt_path.name if local_path else 'NONE'}")

            created += int(is_created)
            updated += int(not is_created)

        await db.commit()

    print("\nDONE")
    print(f"created={created} updated={updated} missing_files={missing}")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--university-id", type=int, required=True)
    p.add_argument("--year", type=int, default=2026)
    p.add_argument("--base-dir", type=str, required=True)
    args = p.parse_args()

    asyncio.run(main(
        university_id=args.university_id,
        year=args.year,
        base_dir=args.base_dir,
    ))