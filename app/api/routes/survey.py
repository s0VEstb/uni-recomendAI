from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session
from app.schemas.survey import SurveySubmissionIn, SurveySubmissionOut
from app.db.repositories.survey_repo import SurveyRepo
from app.services.survey_service import SurveyService
from app.api.routes.auth import get_current_user_id

router = APIRouter()

@router.post("/submit", response_model=SurveySubmissionOut)
async def submit_survey(
    payload: SurveySubmissionIn,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
):
    service = SurveyService(SurveyRepo(db))
    return await service.submit(user_id=user_id, data=payload)

@router.get("/latest", response_model=SurveySubmissionOut)
async def latest_survey(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
):
    service = SurveyService(SurveyRepo(db))
    sub = await service.latest(user_id=user_id)
    if not sub:
        raise HTTPException(status_code=404, detail="No submissions yet")
    return sub