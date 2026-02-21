from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session
from app.schemas.recommendation import SurveySubmitOut
from app.schemas.survey import SurveySubmissionIn, SurveySubmissionOut
from app.db.repositories.survey_repo import SurveyRepo
from app.services.survey_service import SurveyService
from app.api.routes.auth import get_current_user_id

router = APIRouter()

@router.post("/submit", response_model=SurveySubmitOut)
async def submit_survey(
    payload: SurveySubmissionIn,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
):
    service = SurveyService(db, SurveyRepo(db))
    submission, recommendations = await service.submit(user_id=user_id, data=payload)

    universities_top = service.rec_service.build_universities_top(recommendations, limit=5)
    message = service.rec_service.build_message(universities_top, top_n=3)

    submission_out = SurveySubmissionOut(
        id=submission.id,
        user_id=submission.user_id,
        ort_score=submission.ort_score,
        budget_max=submission.budget_max,
        city=submission.city,
        language=submission.language,
        notes=submission.notes,
        needs_dorm=submission.needs_dorm,
        willing_to_relocate=submission.willing_to_relocate,
        answers=submission.answers or {},
        tag_ids=payload.tag_ids,
    )

    return SurveySubmitOut(
        message=message,
        submission=submission_out,
        universities_top=universities_top
    )

@router.get("/latest", response_model=SurveySubmitOut)
async def latest_survey(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
):
    service = SurveyService(db, SurveyRepo(db))
    result = await service.latest_with_recommendations(user_id=user_id)
    if not result:
        raise HTTPException(status_code=404, detail="No submissions yet")
    return result