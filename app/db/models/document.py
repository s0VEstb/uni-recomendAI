from sqlalchemy import Integer, String, ForeignKey, Enum, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin
from sqlalchemy.types import JSON
from typing import Optional, List
from datetime import datetime
from sqlalchemy import DateTime, func
from app.db.enums import DocumentType
from pgvector.sqlalchemy import Vector


class Document(TimestampMixin, Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    university_id: Mapped[int] = mapped_column(
        ForeignKey("universities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    doc_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Where it is stored on server / storage key (required for re-processing)
    local_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    source_url: Mapped[str] = mapped_column(String(1024), nullable=True)
    received_from: Mapped[str] = mapped_column(String(255), nullable=True)
    # Versioning / dedup
    checksum: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)

    # Business timestamp: when we obtained it (useful for admin/audit)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    university: Mapped["University"] = relationship(back_populates="documents")

    chunks: Mapped[List["DocumentChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self):
        return f"{self.title} ({self.year})"


class DocumentChunk(TimestampMixin, Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    page_start: Mapped[int] = mapped_column(Integer, nullable=False)
    page_end: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # NEW: порядок чанка в документе
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)

    # NEW: какой моделью посчитан эмбеддинг
    embedding_model: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # NEW: pgvector (384 размерность для paraphrase-multilingual-MiniLM-L12-v2)
    embedding_vector: Mapped[Optional[list[float]]] = mapped_column(Vector(384), nullable=True)

    # Старое поле можно оставить на время перехода (опционально)
    embedding: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    document: Mapped["Document"] = relationship(back_populates="chunks")

    __table_args__ = (
        Index("ix_doc_chunks_doc_pages", "document_id", "page_start", "page_end"),
        Index("ix_doc_chunks_doc_chunk_index", "document_id", "chunk_index"),
    )

    def __repr__(self):
        return f"Chunk of {self.document.title} (pages {self.page_start}-{self.page_end})"
