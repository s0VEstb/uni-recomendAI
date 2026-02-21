from pathlib import Path
from sqlalchemy.orm import Session

from app.services.rag_bot.local_embeddings import LocalEmbeddingService
from app.services.rag_bot.text_extract import extract_text_file
from app.services.rag_bot.chunking import chunk_pages

from app.db.models.document import Document, DocumentChunk  # поправь импорт
from sqlalchemy import select, delete
from app.db.database import AsyncSession



class RagIndexer:
    def __init__(self) -> None:
        self.embedder = LocalEmbeddingService()

    def _extract_pages(self, local_path: str) -> list[dict]:
        suffix = Path(local_path).suffix.lower()
        if suffix == ".txt":
            return extract_text_file(local_path)
        raise ValueError(f"Unsupported file type for now: {suffix}")

    async def reindex_document(self, db: AsyncSession, document_id: int) -> int:
        # 1) получить документ
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise ValueError(f"Document id={document_id} not found")

        # 2) extract + chunk
        pages = self._extract_pages(doc.local_path)
        chunks = chunk_pages(pages, chunk_size=1000, overlap=150)

        # 3) удалить старые чанки документа
        await db.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == doc.id)
        )
        await db.flush()

        # 4) эмбеддинги (локально, синхронно — это ок для MVP)
        texts = [c["text"] for c in chunks]
        vectors = self.embedder.embed_texts(texts, batch_size=8) if texts else []

        # 5) вставка чанков
        created = 0
        for idx, (ch, vec) in enumerate(zip(chunks, vectors)):
            row = DocumentChunk(
                document_id=doc.id,
                page_start=ch["page_start"],
                page_end=ch["page_end"],
                text=ch["text"],
                chunk_index=idx,
                embedding_model=self.embedder.MODEL_NAME,
                embedding_vector=vec,
            )
            db.add(row)
            created += 1

        await db.commit()
        return created