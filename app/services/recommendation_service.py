from app.schemas.recommendation import (
    ProgramRecommendationOut, RecommendationReason,
    ProgramOut, UniversityOut, UniversityTopOut
)
from app.db.repositories.recommendation_repo import RecommendationRepo


class RecommendationService:
    def __init__(self, repo: RecommendationRepo):
        self.repo = repo

    async def recommend(self, *, submission, tag_ids: list[int], limit: int = 20):
        rows = await self.repo.find_candidates(
            ort_score=submission.ort_score,
            budget_max=submission.budget_max,
            tag_ids=tag_ids,
            limit=limit * 3,
        )

        recs: list[ProgramRecommendationOut] = []

        for program, university in rows:
            reasons: list[RecommendationReason] = []
            score = 0.0

            if submission.budget_max is not None:
                reasons.append(RecommendationReason(
                    code="budget_ok",
                    message="Подходит по бюджету",
                    meta={"budget_max": submission.budget_max},
                ))
                score += 1.0

            if tag_ids:
                reasons.append(RecommendationReason(
                    code="tag_match",
                    message="Совпадает с выбранными интересами",
                    meta={"tag_ids": tag_ids},
                ))
                score += 1.5

            reasons.append(RecommendationReason(
                code="ort_considered",
                message="ОРТ учтён при подборе",
                meta={"ort_score": submission.ort_score},
            ))
            score += 1.0

            recs.append(
                ProgramRecommendationOut(
                    program=ProgramOut.model_validate(program),
                    university=UniversityOut.model_validate(university),
                    score=score,
                    reasons=reasons,
                )
            )

        recs.sort(key=lambda x: x.score, reverse=True)
        return recs[:limit]

    def build_universities_top(self, recs: list[ProgramRecommendationOut], limit: int = 5) -> list[UniversityTopOut]:
        buckets: dict[int, dict] = {}

        for r in recs:
            uid = r.university.id
            if uid not in buckets:
                buckets[uid] = {
                    "university": r.university,
                    "score": 0.0,
                    "programs": [],
                }

            buckets[uid]["score"] += float(r.score)
            buckets[uid]["programs"].append(r)

        result: list[UniversityTopOut] = []
        for b in buckets.values():
            programs_sorted = sorted(b["programs"], key=lambda x: x.score, reverse=True)
            result.append(
                UniversityTopOut(
                    university=b["university"],
                    score=round(b["score"], 2),
                    programs_count=len(programs_sorted),
                    programs=programs_sorted,
                )
            )

        result.sort(key=lambda x: x.score, reverse=True)
        return result[:limit]

    def build_message(self, universities_top: list[UniversityTopOut], top_n: int = 3) -> str:
        if not universities_top:
            return "Пока не нашли подходящие программы. Попробуйте увеличить бюджет или изменить интересы."
        names = [u.university.name for u in universities_top[:top_n]]
        return "Вам больше всего подходят эти университеты: " + ", ".join(names)