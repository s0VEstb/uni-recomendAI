from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.chat import ChatRequest, ChatResponse
from app.db.database import get_async_session
from app.services.rag_bot.chat_service import RagChatService

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_async_session),
):
    service = RagChatService()

    result = await service.ask(
        db=db,
        question=payload.question,
        top_k=payload.top_k,
        university_id=payload.university_id,
        program_id=payload.program_id,
        year=payload.year,
        document_id=payload.document_id,
    )
    return ChatResponse(**result)