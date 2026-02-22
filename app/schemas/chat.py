from pydantic import BaseModel, Field
from typing import Optional, List


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=2)
    university_id: int | None = None
    program_id: int | None = None
    year: int | None = None
    document_id: int | None = None
    top_k: int = Field(default=5, ge=1, le=10)


class ChatSource(BaseModel):
    document_id: int
    document_title: str
    page_start: int
    page_end: int
    chunk_index: int
    source_url: Optional[str] = None
    local_path: Optional[str] = None


class ChatSnippet(BaseModel):
    source: ChatSource
    text: str


class ChatResponse(BaseModel):
    answer: str
    found: bool
    sources: List[ChatSource]
    snippets: List[ChatSnippet] = Field(default_factory=list)