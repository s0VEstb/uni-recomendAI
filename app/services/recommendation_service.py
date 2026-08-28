"""
Recommendation scoring — многофакторная взвешенная модель.

Компоненты и веса:
  ort_proximity  35%  — насколько ОРТ студента превышает минимальный порог программы.
                         0.0 = едва проходит, 1.0 = максимальный запас.
                         Формула: (ort_score - ort_min) / (245 - ort_min)
  tag_relevance  35%  — совпадение тегов, нормализованное и ограниченное cap-ом.
                         Формула: min(tag_sum, MAX_TAG_CAP) / MAX_TAG_CAP
  budget_margin  15%  — насколько стоимость выгодна относительно бюджета.
                         0.5 = точно в бюджет, 1.0 = бесплатно, 0.0 = выше бюджета.
                         Формула: 1.0 - (fee / budget_max)
  city_match     10%  — точное совпадение города (0 или 1).
  extra          5%   — бонус за общежитие (needs_dorm) и готовность к переезду.

Итоговый score = сумма взвешенных компонентов ∈ [0.0, 1.0] — абсолютный,
не зависит от набора других кандидатов.
"""
from app.schemas.recommendation import (
    ProgramRecommendationOut, RecommendationReason,
    ProgramOut, UniversityOut, UniversityTopOut, ScoreBreakdown,
)
from app.db.repositories.recommendation_repo import RecommendationRepo, CITY_TO_DB_NAMES
from app.core.security import ADMISSION_YEAR

# ── Веса компонентов (сумма = 1.0) ──────────────────────────────────
W_ORT = 0.35       # ОРТ proximity
W_TAG = 0.35       # совпадение тегов
W_BUDGET = 0.15    # выгодность бюджета
W_CITY = 0.10      # совпадение города
W_EXTRA = 0.05     # общежитие + переезд

# Cap на сумму весов тегов (защита от переспама при большом числе тегов)
MAX_TAG_CAP = 3.0

ORT_MAX = 245  # максимальный балл ОРТ


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
        program_aggregates: dict[int, tuple] = {}  # pid -> (program, uni, tag_sum, fee, ort_min)

        for program, university, tag_weight, fee, ort_min in rows:
            pid = program.id
            if pid not in program_aggregates:
                program_aggregates[pid] = (program, university, 0.0, fee, ort_min)
            p, u, prev_sum, prev_fee, prev_ort = program_aggregates[pid]
            # суммируем веса тегов; fee/ort_min одинаковы для pid в рамках года
            program_aggregates[pid] = (p, u, prev_sum + tag_weight, prev_fee, prev_ort)

        temp = []

        for program, university, tag_sum, fee, ort_min in program_aggregates.values():
            reasons: list[RecommendationReason] = []
            breakdown = ScoreBreakdown()

            # ──────────────────────────────────────────────
            # 1. ORT PROXIMITY COMPONENT (35%)
            # ──────────────────────────────────────────────
            ort_component = 0.0
            if ort_min is None:
                # Порог не задан — программа открыта для всех, даём нейтральный балл
                ort_component = 0.5
                reasons.append(RecommendationReason(
                    code="ort_not_required",
                    message="Минимальный балл ОРТ не требуется или не указан",
                    meta={"ort_score": submission.ort_score, "year": ADMISSION_YEAR},
                ))
            else:
                gap = submission.ort_score - ort_min
                # Нормализуем запас: (score - min) / (245 - min)
                # Если min >= 245, то дать 1.0 (студент гарантированно проходит)
                denominator = ORT_MAX - ort_min
                if denominator > 0:
                    ort_component = min(gap / denominator, 1.0)
                else:
                    ort_component = 1.0

                if gap >= 30:
                    reasons.append(RecommendationReason(
                        code="ort_strong",
                        message=f"Отличный запас по ОРТ (+{gap} баллов выше порога)",
                        meta={"ort_score": submission.ort_score, "ort_min": ort_min,
                              "gap": gap, "year": ADMISSION_YEAR},
                    ))
                elif gap >= 10:
                    reasons.append(RecommendationReason(
                        code="ort_ok",
                        message=f"Проходите по ОРТ с запасом +{gap} баллов",
                        meta={"ort_score": submission.ort_score, "ort_min": ort_min,
                              "gap": gap, "year": ADMISSION_YEAR},
                    ))
                else:
                    reasons.append(RecommendationReason(
                        code="ort_marginal",
                        message=f"Проходите по ОРТ, но запас невелик (+{gap} баллов)",
                        meta={"ort_score": submission.ort_score, "ort_min": ort_min,
                              "gap": gap, "year": ADMISSION_YEAR},
                    ))

            breakdown.ort = round(ort_component * W_ORT, 4)

            # ──────────────────────────────────────────────
            # 2. TAG RELEVANCE COMPONENT (35%)
            # ──────────────────────────────────────────────
            tag_component = 0.0
            if tag_ids:
                # Ограничиваем сумму cap-ом, чтобы 20 тегов не доминировало над другими факторами
                capped_sum = min(tag_sum, MAX_TAG_CAP)
                tag_component = capped_sum / MAX_TAG_CAP
                reasons.append(RecommendationReason(
                    code="tag_match",
                    message="Совпадает с вашими интересами и сильными сторонами",
                    meta={"tag_ids": tag_ids, "tag_weight_sum": round(tag_sum, 3),
                          "capped_sum": round(capped_sum, 3)},
                ))

            breakdown.tags = round(tag_component * W_TAG, 4)

            # ──────────────────────────────────────────────
            # 3. BUDGET MARGIN COMPONENT (15%)
            # ──────────────────────────────────────────────
            budget_component = 0.0
            if submission.budget_max is not None:
                if fee is None:
                    # Стоимость неизвестна — нейтральный балл
                    budget_component = 0.4
                    reasons.append(RecommendationReason(
                        code="fee_unknown",
                        message="Стоимость контракта не указана — уточните в приёмной комиссии",
                        meta={"budget_max": submission.budget_max, "year": ADMISSION_YEAR},
                    ))
                else:
                    # Выгодность: 1.0 = бесплатно, 0.5 = точно в бюджет
                    # budget_component = 1 - (fee / budget_max) → ограничено [0.0, 1.0]
                    margin_ratio = fee / submission.budget_max
                    budget_component = max(0.0, min(1.0, 1.0 - margin_ratio))

                    savings_pct = round((1.0 - margin_ratio) * 100)
                    if savings_pct >= 30:
                        reasons.append(RecommendationReason(
                            code="budget_great",
                            message=f"Очень выгодно: стоимость на {savings_pct}% ниже вашего бюджета",
                            meta={"budget_max": submission.budget_max, "contract_fee": fee,
                                  "savings_pct": savings_pct, "year": ADMISSION_YEAR},
                        ))
                    elif savings_pct > 0:
                        reasons.append(RecommendationReason(
                            code="budget_ok",
                            message=f"Подходит по бюджету (экономия {savings_pct}%)",
                            meta={"budget_max": submission.budget_max, "contract_fee": fee,
                                  "savings_pct": savings_pct, "year": ADMISSION_YEAR},
                        ))
                    else:
                        reasons.append(RecommendationReason(
                            code="budget_tight",
                            message="Стоимость на пределе вашего бюджета",
                            meta={"budget_max": submission.budget_max, "contract_fee": fee,
                                  "year": ADMISSION_YEAR},
                        ))
            else:
                # Бюджет не указан — нейтральный балл
                budget_component = 0.5

            breakdown.budget = round(budget_component * W_BUDGET, 4)

            # ──────────────────────────────────────────────
            # 4. CITY MATCH COMPONENT (10%)
            # ──────────────────────────────────────────────
            city_component = 0.0
            if submission.city and submission.city not in ("other", None):
                db_names = CITY_TO_DB_NAMES.get(submission.city, [])
                if university.city in db_names:
                    city_component = 1.0
                    reasons.append(RecommendationReason(
                        code="city_match",
                        message="Университет находится в вашем городе",
                        meta={"city": submission.city, "university_city": university.city},
                    ))
                elif getattr(submission, "willing_to_relocate", False):
                    # Если готов к переезду, частичный балл
                    city_component = 0.3
                # else: 0 — нет совпадения и нет готовности переезжать
            else:
                # Город не указан или "other" — нейтральный
                city_component = 0.5

            breakdown.city = round(city_component * W_CITY, 4)

            # ──────────────────────────────────────────────
            # 5. EXTRA FEATURES COMPONENT (5%)
            # ──────────────────────────────────────────────
            extra_component = 0.0
            extra_count = 0
            extra_total = 2  # needs_dorm, willing_to_relocate

            needs_dorm = getattr(submission, "needs_dorm", None)
            willing_to_relocate = getattr(submission, "willing_to_relocate", None)

            if needs_dorm:
                # Бонус за факт запроса общежития (данные о наличии общаги пока нет в БД)
                extra_count += 0.5  # половинный балл — неизвестно, есть ли общежитие
                reasons.append(RecommendationReason(
                    code="dorm_needed",
                    message="Уточните наличие общежития в приёмной комиссии",
                    meta={"needs_dorm": True},
                ))
            if willing_to_relocate:
                extra_count += 1.0
                reasons.append(RecommendationReason(
                    code="relocation_ok",
                    message="Готовы к переезду — доступны программы по всей стране",
                    meta={"willing_to_relocate": True},
                ))

            extra_component = min(extra_count / extra_total, 1.0)
            breakdown.extra = round(extra_component * W_EXTRA, 4)

            # ──────────────────────────────────────────────
            # ИТОГОВЫЙ ВЗВЕШЕННЫЙ БАЛЛ [0.0 – 1.0]
            # ──────────────────────────────────────────────
            raw_score = (
                ort_component * W_ORT
                + tag_component * W_TAG
                + budget_component * W_BUDGET
                + city_component * W_CITY
                + extra_component * W_EXTRA
            )
            final_score = round(min(raw_score, 1.0), 4)
            breakdown.total = final_score

            temp.append((program, university, reasons, final_score, breakdown))

        # Сортируем по убыванию абсолютного балла
        temp.sort(key=lambda x: x[3], reverse=True)

        for program, university, reasons, score, breakdown in temp[:limit]:
            recs.append(
                ProgramRecommendationOut(
                    program=ProgramOut.model_validate(program),
                    university=UniversityOut.model_validate(university),
                    score=score,
                    reasons=reasons,
                    score_breakdown=breakdown,
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
            # Оценка университета = средневзвешенная: лучшая программа с весом 0.6,
            # средняя остальных с весом 0.4, чтобы разнообразие программ давало бонус
            scores = [float(p.score) for p in programs_sorted]
            if len(scores) == 1:
                uni_score = scores[0]
            else:
                top = scores[0]
                rest_avg = sum(scores[1:]) / len(scores[1:])
                uni_score = round(top * 0.6 + rest_avg * 0.4, 4)

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

        # Описание лучшего совпадения
        best = universities_top[0]
        pct = round(best.score * 100)
        names = [u.university.name for u in universities_top[:top_n]]

        if pct >= 80:
            quality = "отлично подходят"
        elif pct >= 60:
            quality = "хорошо подходят"
        elif pct >= 40:
            quality = "частично подходят"
        else:
            quality = "найдены"

        return (
            f"Найдено {len(universities_top)} подходящих университетов. "
            f"Лучшее совпадение: {names[0]} ({pct}%). "
            f"Вам {quality}: {', '.join(names)}."
        )