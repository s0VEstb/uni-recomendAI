from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.database import get_async_session
from app.schemas.recommendation import SurveySubmitOut
from app.schemas.survey import SurveySubmissionIn, SurveySubmissionOut
from app.db.repositories.survey_repo import SurveyRepo
from app.services.survey_service import SurveyService
from app.api.routes.auth import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/submit", response_model=SurveySubmitOut)
async def submit_survey(
    payload: SurveySubmissionIn,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
):
    logger.info(
        f"📋 Survey submit from user {user_id}: "
        f"ort_score={payload.ort_score}, budget_max={payload.budget_max}, "
        f"city={payload.city}, language={payload.language}, "
        f"tag_ids={payload.tag_ids or []}"
    )

    service = SurveyService(db, SurveyRepo(db))
    submission, recommendations = await service.submit(user_id=user_id, data=payload)

    logger.info(f"✅ Recommendations found: {len(recommendations)}")
    if recommendations:
        for i, rec in enumerate(recommendations[:3]):
            logger.info(
                f"   [{i+1}] {rec.university.name} — {rec.program.name} "
                f"(score={rec.score}, reasons={[r.code for r in rec.reasons]})"
            )
    else:
        logger.warning(
            f"❌ No recommendations! Params: ort={payload.ort_score}, "
            f"budget={payload.budget_max}, city={payload.city}, "
            f"language={payload.language}, tags={payload.tag_ids}"
        )

    universities_top = service.rec_service.build_universities_top(recommendations, limit=10)
    message = service.rec_service.build_message(universities_top, top_n=4)

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