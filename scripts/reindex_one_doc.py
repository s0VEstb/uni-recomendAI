from app.db.database import AsyncSessionLocal
from app.services.rag_bot.rag_indexer import RagIndexer
from pathlib import Path
import asyncio


async def main():
    document_id = 1  

    async with AsyncSessionLocal() as db:
        indexer = RagIndexer()
        count = await indexer.reindex_document(db, document_id=document_id)
        print(f"Indexed chunks: {count}")


if __name__ == "__main__":
    asyncio.run(main())

