from sqladmin import Admin, ModelView
from app.db.database import sync_engine
from app.db.models import (
    Document, DocumentChunk
)


class DocumentAdmin(ModelView, model=Document):
    column_list = [Document.id, Document.university_id, Document.title, Document.doc_type, Document.year, Document.received_at]
    column_searchable_list = [Document.title]
    #column_filters = [Document.doc_type, Document.year]


class DocumentChunkAdmin(ModelView, model=DocumentChunk):
    column_list = [DocumentChunk.id, DocumentChunk.document_id, DocumentChunk.page_start, DocumentChunk.page_end]
    #column_filters = [DocumentChunk.document_id]