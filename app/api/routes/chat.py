import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.chat import ChatRequest
from app.db.database import get_async_session
from app.services.rag_bot.chat_service import RagChatService

router = APIRouter()

@router.post("/")
async def chat_endpoint(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_async_session),
):
    service = RagChatService()

    return StreamingResponse(
        service.ask_stream(
            db=db,
            question=payload.question,
            top_k=payload.top_k,
            university_id=payload.university_id,
            program_id=payload.program_id,
            year=payload.year, document_id=payload.document_id,), 
            media_type="text/event-stream" )