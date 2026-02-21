from app.schemas.recommendation import (
    ProgramRecommendationOut, RecommendationReason,
    ProgramOut, UniversityOut, UniversityTopOut
)
from app.db.repositories.recommendation_repo import RecommendationRepo

# Максимальный балл программы (budget_ok + tag_match + ort_considered)
MAX_PROGRAM_SCORE = 3.5


class RecommendationService:
    def __init__(self, repo: RecommendationRepo):
        self.repo = repo

    async def recommend(self, *, submission, tag_ids: list[int], limit: int = 20):
        rows = await self.repo.find_candidates(
            ort_score=submission.ort_score,
            budget_max=submission.budget_max,
            tag_ids=tag_ids,
            city=submission.city,
            language=submission.language,
            limit=limit * 15,  # запас на дубли из JOIN (fees, tags)
        )

        recs: list[ProgramRecommendationOut] = []
        program_aggregates: dict[int, tuple] = {}  # pid -> (program, uni, tag_sum)

        for program, university, tag_weight in rows:
            pid = program.id
            if pid not in program_aggregates:
                program_aggregates[pid] = (program, university, 0.0)
            _, _, prev_sum = program_aggregates[pid]
            program_aggregates[pid] = (program, university, prev_sum + tag_weight)

        temp: list[tuple[object, object, list[RecommendationReason], float]] = []

        for program, university, tag_sum in program_aggregates.values():
            reasons: list[RecommendationReason] = []
            raw_score = 0.0

            if submission.budget_max is not None:
                reasons.append(RecommendationReason(
                    code="budget_ok",
                    message="Подходит по бюджету",
                    meta={"budget_max": submission.budget_max},
                ))
                raw_score += 1.0

            if tag_ids:
                reasons.append(RecommendationReason(
                    code="tag_match",
                    message="Совпадает с выбранными интересами",
                    meta={"tag_ids": tag_ids, "tag_weight_sum": tag_sum},
                ))
                raw_score += tag_sum

            reasons.append(RecommendationReason(
                code="ort_considered",
                message="ОРТ учтён при подборе",
                meta={"ort_score": submission.ort_score},
            ))
            raw_score += 1.0

            temp.append((program, university, reasons, raw_score))

        temp.sort(key=lambda x: x[3], reverse=True)
        max_raw = temp[0][3] if temp else 0.0

        for program, university, reasons, raw in temp[:limit]:
            score_norm = round(raw / max_raw, 4) if max_raw > 0 else 0.0
            recs.append(
                ProgramRecommendationOut(
                    program=ProgramOut.model_validate(program),
                    university=UniversityOut.model_validate(university),
                    score=score_norm,
                    reasons=reasons,
                )
            )

        return recs

    def build_universities_top(self, recs: list[ProgramRecommendationOut], limit: int = 5) -> list[UniversityTopOut]:
        buckets: dict[int, dict] = {}

        for r in recs:
            uid = r.university.id
            if uid not in buckets:
                buckets[uid] = {
                    "university": r.university,
                    "programs": [],
                }

            buckets[uid]["programs"].append(r)

        result: list[UniversityTopOut] = []
        for b in buckets.values():
            programs_sorted = sorted(b["programs"], key=lambda x: x.score, reverse=True)
            # Университет: макс. % среди программ (топ по лучшей программе)
            scores = [float(p.score) for p in programs_sorted]
            uni_score = round(max(scores), 4) if scores else 0.0

            result.append(
                UniversityTopOut(
                    university=b["university"],
                    score=uni_score,
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