from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = "64ed094f2a24"
down_revision = "dd1213f4ca14"
branch_labels = None
depends_on = None


def upgrade():
    # extension на всякий случай (безопасно)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.add_column(
        "document_chunks",
        sa.Column("chunk_index", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "document_chunks",
        sa.Column("embedding_model", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "document_chunks",
        sa.Column("embedding_vector", Vector(384), nullable=True),
    )

    op.create_index(
        "ix_doc_chunks_doc_chunk_index",
        "document_chunks",
        ["document_id", "chunk_index"],
        unique=False,
    )

    # Векторный индекс (можно создать сразу)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding_vector_ivfflat
        ON document_chunks
        USING ivfflat (embedding_vector vector_cosine_ops)
        WITH (lists = 100)
    """)

    # убираем server_default после заполнения существующих строк
    op.alter_column("document_chunks", "chunk_index", server_default=None)


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding_vector_ivfflat")
    op.drop_index("ix_doc_chunks_doc_chunk_index", table_name="document_chunks")
    op.drop_column("document_chunks", "embedding_vector")
    op.drop_column("document_chunks", "embedding_model")
    op.drop_column("document_chunks", "chunk_index")