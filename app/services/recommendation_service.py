"""
Recommendation Service — многокомпонентный скоринг программ.

Алгоритм (абсолютная шкала 0–100 баллов, независимая от других результатов):

Компонент          Макс.  Описание
─────────────────────────────────────────────────────────────────────────
ort_margin         30     Запас ОРТ над порогом (чем выше — тем лучше).
                          0  если ort_min неизвестен (нейтрально).
                          30 если student.ort ≥ ort_min + 50 (запас ≥50).
tag_match          40     Сумма весов совпавших тегов, нормализованная
                          к [0, 40]. Если тегов нет — 0.
budget_margin      20     Насколько стоимость ниже max‑бюджета студента.
                          0  если budget_max не задан или fee неизвестен.
                          20 если fee ≤ budget_max * 0.5 (программа ≤50% бюджета).
city_bonus         10     +10 если город программы совпадает с городом студента.
                          +5  если студент готов к переезду (willing_to_relocate).
─────────────────────────────────────────────────────────────────────────
Total              100

Итоговый score = Σ / 100 → float [0.0, 1.0]
"""
from __future__ import annotations

from app.schemas.recommendation import (
    ProgramRecommendationOut, RecommendationReason,
    ProgramOut, UniversityOut, UniversityTopOut
)
from app.db.repositories.recommendation_repo import RecommendationRepo
from app.core.security import ADMISSION_YEAR

# ──────────────────────────────────────────────
# Веса компонентов (сумма = 100)
# ──────────────────────────────────────────────
W_ORT = 30       # запас ОРТ
W_TAG = 40       # совпадение тегов
W_BUDGET = 20    # запас бюджета
W_CITY = 10      # город / готовность к переезду

# Порог "хорошего запаса" ОРТ (при котором выдаётся максимум)
ORT_MARGIN_MAX = 50   # запас ≥ 50 баллов → полные 30 очков

# Порог "хорошего" тегового совпадения (сумма весов)
TAG_WEIGHT_FULL = 3.0   # сумма ≥ 3.0 → полные 40 очков

# Доля бюджета, при которой выдаётся максимум бюджетного бонуса
BUDGET_RATIO_BEST = 0.5   # fee ≤ 50 % бюджета → полные 20 очков


def _ort_score(student_ort: int, ort_min: int | None) -> tuple[float, RecommendationReason]:
    """Вернуть [0..W_ORT] и reason."""
    if ort_min is None:
        # порог неизвестен — даём нейтральный средний балл (50%)
        pts = W_ORT * 0.5
        reason = RecommendationReason(
            code="ort_unknown",
            message="Минимальный балл ОРТ не указан — засчитываем нейтрально",
            meta={"ort_score": student_ort, "year": ADMISSION_YEAR, "pts": pts},
        )
        return pts, reason

    margin = student_ort - ort_min
    # margin гарантированно >= 0 (SQL-фильтр отсек лишних)
    ratio = min(margin / ORT_MARGIN_MAX, 1.0)
    pts = round(W_ORT * ratio, 2)
    reason = RecommendationReason(
        code="ort_ok",
        message=(
            f"Проходите по ОРТ с запасом {margin} баллов"
            if margin > 0 else "Ровно на пороге ОРТ"
        ),
        meta={
            "ort_score": student_ort,
            "ort_min_score": ort_min,
            "margin": margin,
            "year": ADMISSION_YEAR,
            "pts": pts,
        },
    )
    return pts, reason


def _tag_score(tag_sum: float, tag_ids: list[int]) -> tuple[float, RecommendationReason]:
    """Вернуть [0..W_TAG] и reason."""
    if not tag_ids:
        reason = RecommendationReason(
            code="tag_not_provided",
            message="Интересы не указаны",
            meta={"pts": 0.0},
        )
        return 0.0, reason

    ratio = min(tag_sum / TAG_WEIGHT_FULL, 1.0)
    pts = round(W_TAG * ratio, 2)
    reason = RecommendationReason(
        code="tag_match",
        message=f"Совпадение с интересами (суммарный вес {round(tag_sum, 2)})",
        meta={"tag_ids": tag_ids, "tag_weight_sum": round(tag_sum, 2), "pts": pts},
    )
    return pts, reason


def _budget_score(
    fee: int | None,
    budget_max: int | None,
) -> tuple[float, RecommendationReason]:
    """Вернуть [0..W_BUDGET] и reason."""
    if budget_max is None:
        reason = RecommendationReason(
            code="budget_not_provided",
            message="Бюджет не указан",
            meta={"pts": 0.0},
        )
        return 0.0, reason

    if fee is None:
        reason = RecommendationReason(
            code="fee_unknown",
            message="Стоимость контракта не указана",
            meta={"budget_max": budget_max, "year": ADMISSION_YEAR, "pts": 0.0},
        )
        return 0.0, reason

    # fee <= budget_max гарантирован SQL-фильтром
    # ratio: насколько программа дешевле бюджета
    # fee/budget_max → 0 = очень дёшево, 1 = точно в бюджет
    # pts: чем дешевле — тем выше
    cost_ratio = fee / budget_max  # [0, 1]
    # линейная функция: fee=0 → W_BUDGET, fee=budget_max → W_BUDGET/4
    pts = round(W_BUDGET * (1.0 - cost_ratio * (1 - BUDGET_RATIO_BEST)), 2)
    pts = max(0.0, min(W_BUDGET, pts))

    savings = budget_max - fee
    reason = RecommendationReason(
        code="budget_ok",
        message=f"Подходит по бюджету, экономия {savings:,} сом",
        meta={
            "budget_max": budget_max,
            "contract_fee": fee,
            "savings": savings,
            "year": ADMISSION_YEAR,
            "pts": pts,
        },
    )
    return pts, reason


def _city_score(
    uni_city: str | None,
    student_city: str | None,
    willing_to_relocate: bool | None,
) -> tuple[float, RecommendationReason]:
    """Вернуть [0..W_CITY] и reason."""
    from app.db.repositories.recommendation_repo import CITY_TO_DB_NAMES

    # Нормализуем город студента в возможные DB-значения
    student_db_cities: list[str] = []
    if student_city and student_city != "other" and student_city in CITY_TO_DB_NAMES:
        student_db_cities = CITY_TO_DB_NAMES[student_city]

    if student_db_cities and uni_city and uni_city in student_db_cities:
        pts = float(W_CITY)
        reason = RecommendationReason(
            code="city_match",
            message=f"Университет находится в вашем городе ({uni_city})",
            meta={"city": uni_city, "pts": pts},
        )
        return pts, reason

    if willing_to_relocate:
        pts = W_CITY * 0.5
        reason = RecommendationReason(
            code="willing_to_relocate",
            message="Вы готовы к переезду — учтено в рейтинге",
            meta={"pts": pts},
        )
        return pts, reason

    if not student_city or student_city == "other":
        # студент не указал город — нейтрально
        pts = W_CITY * 0.3
        reason = RecommendationReason(
            code="city_not_provided",
            message="Город не указан",
            meta={"pts": pts},
        )
        return pts, reason

    # город не совпал, переезжать не готов
    reason = RecommendationReason(
        code="city_mismatch",
        message=f"Университет в другом городе ({uni_city})",
        meta={"student_city": student_city, "uni_city": uni_city, "pts": 0.0},
    )
    return 0.0, reason


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

        # ── 1. Агрегация по program_id ──────────────────────────────────
        program_aggregates: dict[int, tuple] = {}  # pid -> (program, uni, tag_sum, fee, ort_min)

        for program, university, tag_weight, fee, ort_min in rows:
            pid = program.id
            if pid not in program_aggregates:
                program_aggregates[pid] = (program, university, 0.0, fee, ort_min)
            p, u, prev_sum, prev_fee, prev_ort = program_aggregates[pid]
            program_aggregates[pid] = (p, u, prev_sum + tag_weight, prev_fee, prev_ort)

        # ── 2. Вычисление многокомпонентного скора ──────────────────────
        recs: list[ProgramRecommendationOut] = []

        for program, university, tag_sum, fee, ort_min in program_aggregates.values():
            reasons: list[RecommendationReason] = []

            ort_pts, ort_reason = _ort_score(submission.ort_score, ort_min)
            tag_pts, tag_reason = _tag_score(tag_sum, tag_ids)
            budget_pts, budget_reason = _budget_score(fee, submission.budget_max)
            city_pts, city_reason = _city_score(
                uni_city=university.city if hasattr(university, "city") else None,
                student_city=submission.city,
                willing_to_relocate=getattr(submission, "willing_to_relocate", False),
            )

            reasons.extend([ort_reason, tag_reason, budget_reason, city_reason])

            total_pts = ort_pts + tag_pts + budget_pts + city_pts
            score_norm = round(total_pts / 100.0, 4)

            recs.append(
                ProgramRecommendationOut(
                    program=ProgramOut.model_validate(program),
                    university=UniversityOut.model_validate(university),
                    score=score_norm,
                    reasons=reasons,
                )
            )

        # ── 3. Сортировка и обрезка ──────────────────────────────────────
        recs.sort(key=lambda x: x.score, reverse=True)
        return recs[:limit]

    def build_universities_top(
        self, recs: list[ProgramRecommendationOut], limit: int = 5
    ) -> list[UniversityTopOut]:
        buckets: dict[int, dict] = {}

        for r in recs:
            uid = r.university.id
            if uid not in buckets:
                buckets[uid] = {"university": r.university, "programs": []}
            buckets[uid]["programs"].append(r)

        result: list[UniversityTopOut] = []
        for b in buckets.values():
            programs_sorted = sorted(b["programs"], key=lambda x: x.score, reverse=True)
            scores = [float(p.score) for p in programs_sorted]
            # Университет оценивается по средневзвешенному лучших программ:
            # max даёт лидерство, среднее — стабильность
            if scores:
                uni_score = round(scores[0] * 0.6 + sum(scores) / len(scores) * 0.4, 4)
            else:
                uni_score = 0.0

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
        top = universities_top[0]
        pct = round(top.score * 100)
        return (
            f"Лучшее совпадение: {top.university.name} ({pct}%). "
            f"Также рекомендуем: {', '.join(names[1:]) if len(names) > 1 else '—'}"
        )