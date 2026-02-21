from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.models.document import Document, DocumentChunk


async def retrieve_chunks_pgvector(
    db: AsyncSession,
    query_vector: list[float],
    top_k: int = 5,
    university_id: int | None = None,
    year: int | None = None,
    document_id: int | None = None,
):
    distance_expr = DocumentChunk.embedding_vector.cosine_distance(query_vector).label("distance")

    stmt = (
        select(DocumentChunk, distance_expr)
        .join(Document, Document.id == DocumentChunk.document_id)
        .options(joinedload(DocumentChunk.document))
        .where(DocumentChunk.embedding_vector.isnot(None))
    )

    if university_id is not None:
        stmt = stmt.where(Document.university_id == university_id)

    if year is not None:
        stmt = stmt.where(Document.year == year)

    if document_id is not None:
        stmt = stmt.where(DocumentChunk.document_id == document_id)

    stmt = stmt.order_by(distance_expr).limit(top_k)

    result = await db.execute(stmt)
    return result.all()  # [(DocumentChunk, distance), ...]