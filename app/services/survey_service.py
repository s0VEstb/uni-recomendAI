from app.db.repositories.survey_repo import SurveyRepo

class SurveyService:
    def __init__(self, repo: SurveyRepo):
        self.repo = repo

    async def submit(self, user_id: int, data):
        sub = await self.repo.create_submission(
            user_id=user_id,
            ort_score=data.ort_score,
            budget_max=data.budget_max,
            city=data.city,
            language=data.language,
            answers=data.answers,
        )
        if data.tag_ids:
            await self.repo.attach_tags(sub.id, data.tag_ids)
        return sub

    async def latest(self, user_id: int):
        return await self.repo.get_latest_by_user(user_id)