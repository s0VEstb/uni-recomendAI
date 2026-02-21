from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.user import SurveySubmission, SubmissionTag

class SurveyRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_submission(
        self,
        user_id: int,
        ort_score: int,
        budget_max: int | None,
        city: str | None,
        language,
        answers: dict,
        notes: str | None = None,
        needs_dorm: bool | None = None,
        willing_to_relocate: bool | None = None,
    ) -> SurveySubmission:
        s = SurveySubmission(
            user_id=user_id,
            ort_score=ort_score,
            budget_max=budget_max,
            city=city,
            language=language,
            answers=answers or {},
            notes=notes,
            needs_dorm=needs_dorm,
            willing_to_relocate=willing_to_relocate,
        )
        self.db.add(s)
        await self.db.commit()
        await self.db.refresh(s)
        return s

    async def attach_tags(self, submission_id: int, tag_ids: list[int]) -> None:
        # удалить старые
        await self.db.execute(delete(SubmissionTag).where(SubmissionTag.submission_id == submission_id))
        # добавить новые
        for tid in tag_ids:
            self.db.add(SubmissionTag(submission_id=submission_id, tag_id=tid, weight=1.0)) #Позже исправить вес тега
        await self.db.commit()

    async def get_latest_by_user(self, user_id: int) -> SurveySubmission | None:
        q = (
            select(SurveySubmission)
            .where(SurveySubmission.user_id == user_id)
            .order_by(SurveySubmission.created_at.desc())
            .limit(1)
        )
        res = await self.db.execute(q)
        return res.scalar_one_or_none()

    async def update_submission(
        self,
        submission_id: int,
        user_id: int,
        ort_score: int,
        budget_max: int | None,
        city: str | None,
        language,
        answers: dict,
        notes: str | None = None,
        needs_dorm: bool | None = None,
        willing_to_relocate: bool | None = None,
    ) -> SurveySubmission | None:
        q = (
            select(SurveySubmission)
            .where(SurveySubmission.id == submission_id, SurveySubmission.user_id == user_id)
        )
        res = await self.db.execute(q)
        sub = res.scalar_one_or_none()
        if not sub:
            return None
        sub.ort_score = ort_score
        sub.budget_max = budget_max
        sub.city = city
        sub.language = language
        sub.answers = answers or {}
        sub.notes = notes
        sub.needs_dorm = needs_dorm
        sub.willing_to_relocate = willing_to_relocate
        await self.db.commit()
        await self.db.refresh(sub)
        return sub