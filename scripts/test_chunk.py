# scripts/test_retrieve.py
import asyncio
from app.db.database import AsyncSessionLocal
from app.services.rag_bot.local_embeddings import LocalEmbeddingService
from app.services.rag_bot.retrieval_service import retrieve_chunks_pgvector

async def main():
    q = "Какие минимальные баллы нужны для Software Engineering в AUCA?"
    embedder = LocalEmbeddingService()
    qv = embedder.embed_text(q)

    async with AsyncSessionLocal() as db:
        rows = await retrieve_chunks_pgvector(
            db=db,
            query_vector=qv,
            top_k=12,                 # увеличь
            university_id=2,
            year=2026,
            document_id=None,
        )
        print("FOUND", len(rows))
        for i, (chunk, dist) in enumerate(rows, 1):
            print(f"\n#{i} dist={float(dist):.4f} doc={chunk.document.title} idx={chunk.chunk_index}")
            print(chunk.text[:500])

if __name__ == "__main__":
    asyncio.run(main())