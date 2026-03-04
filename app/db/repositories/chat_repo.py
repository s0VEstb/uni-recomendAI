from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.chat import ChatSession, ChatMessage


class ChatRepo:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Sessions ────────────────────────────────────────────────

    async def list_sessions(self, user_id: int, limit: int = 50) -> list[ChatSession]:
        result = await self.db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id, ChatSession.is_active == True)
            .order_by(ChatSession.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_session(self, session_id: int, user_id: int) -> Optional[ChatSession]:
        result = await self.db.execute(
            select(ChatSession)
            .where(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id,
                ChatSession.is_active == True,
            )
            .options(selectinload(ChatSession.messages))
        )
        return result.scalar_one_or_none()

    async def create_session(
        self,
        user_id: int,
        title: str = "Новый чат",
        university_id: Optional[int] = None,
        program_id: Optional[int] = None,
    ) -> ChatSession:
        session = ChatSession(
            user_id=user_id,
            title=title,
            university_id=university_id,
            program_id=program_id,
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def update_title(
        self, session_id: int, user_id: int, title: str
    ) -> Optional[ChatSession]:
        result = await self.db.execute(
            update(ChatSession)
            .where(ChatSession.id == session_id, ChatSession.user_id == user_id)
            .values(title=title)
            .returning(ChatSession)
        )
        row = result.scalar_one_or_none()
        if row:
            await self.db.commit()
        return row

    async def delete_session(self, session_id: int, user_id: int) -> bool:
        """Soft-delete: set is_active=False."""
        result = await self.db.execute(
            update(ChatSession)
            .where(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id,
                ChatSession.is_active == True,
            )
            .values(is_active=False)
            .returning(ChatSession.id)
        )
        deleted = result.scalar_one_or_none()
        if deleted:
            await self.db.commit()
        return deleted is not None

    # ── Messages ─────────────────────────────────────────────────

    async def add_message(
        self, session_id: int, role: str, content: str
    ) -> ChatMessage:
        msg = ChatMessage(session_id=session_id, role=role, content=content)
        self.db.add(msg)
        # bump session.updated_at via touch
        await self.db.execute(
            update(ChatSession)
            .where(ChatSession.id == session_id)
            .values(updated_at=ChatSession.updated_at)  # trigger onupdate
        )
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def get_messages(self, session_id: int, user_id: int) -> list[ChatMessage]:
        # verify ownership first
        session = await self.db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id,
                ChatSession.is_active == True,
            )
        )
        if not session.scalar_one_or_none():
            return []
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
        )
        return list(result.scalars().all())
