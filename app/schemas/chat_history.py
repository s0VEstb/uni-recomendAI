from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ChatSessionCreate(BaseModel):
    title: str = "Новый чат"
    university_id: Optional[int] = None
    program_id: Optional[int] = None


class ChatSessionRename(BaseModel):
    title: str


class SaveMessageIn(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionOut(BaseModel):
    id: int
    title: str
    university_id: Optional[int]
    program_id: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionDetailOut(ChatSessionOut):
    messages: list[ChatMessageOut]


class ChatSessionListOut(BaseModel):
    sessions: list[ChatSessionOut]
