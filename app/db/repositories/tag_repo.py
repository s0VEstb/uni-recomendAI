from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.tag import Tag
from app.db.enums import TagType

class TagRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self, tag_type: TagType | None = None) -> list[Tag]:
        q = select(Tag).where(Tag.is_active == True)  # noqa: E712
        if tag_type:
            q = q.where(Tag.type == tag_type)
        res = await self.db.execute(q)
        return list(res.scalars().all())