import asyncio

from app.db.database import AsyncSessionLocal
from app.services.rag_bot.local_embeddings import LocalEmbeddingService
from app.services.rag_bot.retrieval_service import retrieve_chunks_pgvector


async def main():
    # Подставь id твоего main-документа (тот, который индексировал)
    document_id = 1

    question = "Сколько стоит бакалавриат в AUCA?"

    embedder = LocalEmbeddingService()
    qv = embedder.embed_text(question)

    async with AsyncSessionLocal() as db:
        rows = await retrieve_chunks_pgvector(
            db=db,
            query_vector=qv,
            top_k=5,
            document_id=document_id,  # сначала ограничим одним документом для чистого теста
        )

        print(f"QUESTION: {question}")
        print(f"FOUND: {len(rows)} chunks")

        for i, row in enumerate(rows, 1):
            doc = row.document
            print(f"\n#{i} | doc_id={doc.id} | {doc.title} | pages={row.page_start}-{row.page_end} | chunk_index={row.chunk_index}")
            print("-" * 100)
            print(row.text[:700])


if __name__ == "__main__":
    asyncio.run(main())