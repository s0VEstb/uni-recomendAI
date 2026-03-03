from sqladmin import ModelView
from app.db.models.chat import ChatSession, ChatMessage


class ChatSessionAdmin(ModelView, model=ChatSession):
    name = "Chat Session"
    name_plural = "Chat Sessions"
    icon = "fa-solid fa-comments"
    column_list = [
        ChatSession.id,
        ChatSession.user_id,
        ChatSession.title,
        ChatSession.is_active,
        ChatSession.university_id,
        ChatSession.created_at,
        ChatSession.updated_at,
    ]
    column_searchable_list = [ChatSession.title]
    column_sortable_list = [ChatSession.id, ChatSession.created_at, ChatSession.updated_at]
    column_default_sort = [(ChatSession.updated_at, True)]


class ChatMessageAdmin(ModelView, model=ChatMessage):
    name = "Chat Message"
    name_plural = "Chat Messages"
    icon = "fa-solid fa-message"
    column_list = [
        ChatMessage.id,
        ChatMessage.session_id,
        ChatMessage.role,
        ChatMessage.created_at,
    ]
    column_sortable_list = [ChatMessage.id, ChatMessage.session_id, ChatMessage.created_at]
    column_default_sort = [(ChatMessage.id, True)]
