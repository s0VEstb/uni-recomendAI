import asyncio
import sys
from pathlib import Path
from typing import Optional

from sqlalchemy import select

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.database import AsyncSessionLocal
from app.db.models.document import Document
from app.services.rag_bot.rag_indexer import RagIndexer


async def reindex_all_documents(
    university_id: Optional[int] = None,
    year: Optional[int] = None,
    only_with_local_path: bool = True,
) -> None:
    indexer = RagIndexer()

    async with AsyncSessionLocal() as db:
        stmt = select(Document).order_by(Document.id)

        if university_id is not None:
            stmt = stmt.where(Document.university_id == university_id)
        if year is not None:
            stmt = stmt.where(Document.year == year)

        result = await db.execute(stmt)
        docs = result.scalars().all()

        if not docs:
            print("[WARN] Документы не найдены в БД")
            return

        print(f"[INFO] Найдено документов: {len(docs)}")

        ok = failed = skipped = 0

        for i, doc in enumerate(docs, start=1):
            try:
                print(f"\n[{i}/{len(docs)}] document_id={doc.id} | {doc.title}")

                if only_with_local_path:
                    if not doc.local_path:
                        print("  [SKIP] local_path пустой")
                        skipped += 1
                        continue

                    abs_path = Path.cwd() / doc.local_path
                    if not abs_path.exists():
                        print(f"  [SKIP] Файл не найден: {abs_path}")
                        skipped += 1
                        continue

                created = await indexer.reindex_document(db=db, document_id=doc.id)
                print(f"  [OK] created_chunks={created}")
                ok += 1

            except Exception as e:
                print(f"  [ERR] document_id={doc.id}: {e}")
                failed += 1
                await db.rollback()

        print("\n========== DONE ==========")
        print(f"OK: {ok}")
        print(f"SKIPPED: {skipped}")
        print(f"FAILED: {failed}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Reindex all documents into chunks")
    parser.add_argument("--university-id", type=int, default=None)
    parser.add_argument("--year", type=int, default=None)
    parser.add_argument("--include-missing-local-path", action="store_true")
    args = parser.parse_args()

    asyncio.run(
        reindex_all_documents(
            university_id=args.university_id,
            year=args.year,
            only_with_local_path=not args.include_missing_local_path,
        )
    )
