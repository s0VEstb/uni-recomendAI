from app.db.repositories.survey_repo import SurveyRepo
from app.db.repositories.recommendation_repo import RecommendationRepo
from app.services.recommendation_service import RecommendationService
from app.schemas.recommendation import SurveySubmitOut
from app.schemas.survey import SurveySubmissionOut


class SurveyService:
    def __init__(self, db, survey_repo: SurveyRepo):
        self.db = db
        self.survey_repo = survey_repo
        self.rec_service = RecommendationService(RecommendationRepo(db))

    async def submit(self, user_id: int, data):
        sub = await self.survey_repo.create_submission(
            user_id=user_id,
            ort_score=data.ort_score,
            budget_max=data.budget_max,
            city=data.city,
            language=data.language,
            answers=data.answers,
        )
        # теги анкеты
        if data.tag_ids:
            await self.survey_repo.attach_tags(sub.id, data.tag_ids)

        # рекомендации
        recs = await self.rec_service.recommend(submission=sub, tag_ids=data.tag_ids, limit=20)

        return sub, recs

    async def latest(self, user_id: int):
        return await self.survey_repo.get_latest_by_user(user_id)

    async def latest_with_recommendations(self, user_id: int) -> SurveySubmitOut | None:
        sub = await self.survey_repo.get_latest_by_user(user_id)
        if not sub:
            return None
        tag_ids = [tl.tag_id for tl in sub.tag_links]
        recs = await self.rec_service.recommend(submission=sub, tag_ids=tag_ids, limit=20)
        universities_top = self.rec_service.build_universities_top(recs, limit=5)
        message = self.rec_service.build_message(universities_top, top_n=3)
        return SurveySubmitOut(
            message=message,
            submission=SurveySubmissionOut.model_validate(sub),
            universities_top=universities_top,
        )