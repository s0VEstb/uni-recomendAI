from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session
from app.db.repositories.tag_repo import TagRepo
from app.schemas.tag import TagOut
from app.db.enums import TagType

router = APIRouter()

@router.get("", response_model=list[TagOut])
async def list_tags(tag_type: TagType | None = None, db: AsyncSession = Depends(get_async_session)):
    return await TagRepo(db).list(tag_type=tag_type)