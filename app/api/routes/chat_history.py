from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session
from app.api.routes.auth import get_current_user_id
from app.db.repositories.chat_repo import ChatRepo
from app.schemas.chat_history import (
    ChatSessionCreate,
    ChatSessionRename,
    SaveMessageIn,
    ChatSessionOut,
    ChatSessionDetailOut,
    ChatSessionListOut,
    ChatMessageOut,
)

router = APIRouter()


def _get_repo(db: AsyncSession = Depends(get_async_session)) -> ChatRepo:
    return ChatRepo(db)


# ── List sessions ─────────────────────────────────────────────

@router.get("/sessions", response_model=ChatSessionListOut, tags=["Chat History"])
async def list_sessions(
    user_id: int = Depends(get_current_user_id),
    repo: ChatRepo = Depends(_get_repo),
):
    sessions = await repo.list_sessions(user_id)
    return ChatSessionListOut(sessions=sessions)


# ── Create session ────────────────────────────────────────────

@router.post("/sessions", response_model=ChatSessionOut, status_code=status.HTTP_201_CREATED, tags=["Chat History"])
async def create_session(
    payload: ChatSessionCreate,
    user_id: int = Depends(get_current_user_id),
    repo: ChatRepo = Depends(_get_repo),
):
    session = await repo.create_session(
        user_id=user_id,
        title=payload.title,
        university_id=payload.university_id,
        program_id=payload.program_id,
    )
    return session


# ── Get session + messages ────────────────────────────────────

@router.get("/sessions/{session_id}", response_model=ChatSessionDetailOut, tags=["Chat History"])
async def get_session(
    session_id: int,
    user_id: int = Depends(get_current_user_id),
    repo: ChatRepo = Depends(_get_repo),
):
    session = await repo.get_session(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


# ── Rename session ────────────────────────────────────────────

@router.patch("/sessions/{session_id}", response_model=ChatSessionOut, tags=["Chat History"])
async def rename_session(
    session_id: int,
    payload: ChatSessionRename,
    user_id: int = Depends(get_current_user_id),
    repo: ChatRepo = Depends(_get_repo),
):
    session = await repo.update_title(session_id, user_id, payload.title)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


# ── Delete session ────────────────────────────────────────────

@router.delete("/sessions/{session_id}", tags=["Chat History"])
async def delete_session(
    session_id: int,
    user_id: int = Depends(get_current_user_id),
    repo: ChatRepo = Depends(_get_repo),
):
    ok = await repo.delete_session(session_id, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"ok": True}


# ── Add message ───────────────────────────────────────────────

@router.post(
    "/sessions/{session_id}/messages",
    response_model=ChatMessageOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Chat History"],
)
async def add_message(
    session_id: int,
    payload: SaveMessageIn,
    user_id: int = Depends(get_current_user_id),
    repo: ChatRepo = Depends(_get_repo),
):
    # Verify ownership
    session = await repo.get_session(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if payload.role not in ("user", "assistant"):
        raise HTTPException(status_code=422, detail="role must be 'user' or 'assistant'")
    msg = await repo.add_message(session_id, payload.role, payload.content)
    return msg
