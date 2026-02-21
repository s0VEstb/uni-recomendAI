from __future__ import annotations

from typing import Any
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.services.rag_bot.local_embeddings import LocalEmbeddingService
from app.services.rag_bot.retrieval_service import retrieve_chunks_pgvector

# поправь импорты под вашу структуру
from app.db.models import University, Program, ProgramFee, ProgramAdmission
from app.services.rag_bot.embedding_provider import get_embedder

def _normalize_optional_str(value):
    if value in (None, "", "None", "null", "NULL"):
        return None
    return value

import re

def _detect_degree_target(q: str) -> str | None:
    q = q.lower()
    if any(k in q for k in ["mba", "магист", "магистр", "master"]):
        return "master"
    if any(k in q for k in ["бакалавр", "бакалавриат", "undergrad", "bachelor"]):
        return "bachelor"
    return None


def _chunk_matches_degree(text_l: str, degree_target: str | None) -> bool:
    if degree_target is None:
        return True

    master_markers = ["mba", "магист", "магистр", "master", "graduate"]
    bachelor_markers = ["бакалавр", "бакалавриат", "bachelor", "undergrad", "freshman"]

    if degree_target == "master":
        # если явно бакалавриат и нет маркеров магистратуры — не подходит
        if any(m in text_l for m in bachelor_markers) and not any(m in text_l for m in master_markers):
            return False
        # лучше требовать явный маркер магистратуры
        return any(m in text_l for m in master_markers)

    if degree_target == "bachelor":
        if any(m in text_l for m in master_markers) and not any(m in text_l for m in bachelor_markers):
            return False
        return any(m in text_l for m in bachelor_markers)

    return True


class RagChatService:
    def __init__(self) -> None:
        self.embedder = get_embedder()

    @staticmethod
    def _clean_text(text: str, limit: int = 700) -> str:
        return " ".join((text or "").split())[:limit]

    async def _get_program_context(
        self,
        db: AsyncSession,
        program_id: int,
        year: int | None = None,
    ) -> dict | None:
        # Загружаем программу + вуз
        result = await db.execute(
            select(Program)
            .options(joinedload(Program.university))
            .where(Program.id == program_id)
        )
        program = result.scalar_one_or_none()
        if not program:
            return None

        # Выбор года
        target_year = year or 2026  # можно позже заменить на current cycle

        # Fee (предпочитаем указанный год, иначе последний доступный)
        fee_result = await db.execute(
            select(ProgramFee)
            .where(ProgramFee.program_id == program_id)
            .order_by(
                (ProgramFee.year == target_year).desc(),
                ProgramFee.year.desc(),
            )
            .limit(1)
        )
        fee = fee_result.scalar_one_or_none()

        # Admission
        adm_result = await db.execute(
            select(ProgramAdmission)
            .where(ProgramAdmission.program_id == program_id)
            .order_by(
                (ProgramAdmission.year == target_year).desc(),
                ProgramAdmission.year.desc(),
            )
            .limit(1)
        )
        admission = adm_result.scalar_one_or_none()

        return {
            "program": program,
            "university": program.university,
            "fee": fee,
            "admission": admission,
        }

    def _build_structured_answer(
        self,
        question: str,
        program_ctx: dict | None,
    ) -> tuple[str | None, list[dict]]:
        """
        Пытаемся ответить из структурированных таблиц.
        Возвращает (answer_or_none, synthetic_sources).
        """
        if not program_ctx:
            return None, []

        question_l = question.lower()
        program = program_ctx["program"]
        uni = program_ctx["university"]
        fee = program_ctx["fee"]
        admission = program_ctx["admission"]

        synthetic_sources: list[dict] = []

        # Вопросы про стоимость
        price_keywords = ["стоим", "цена", "контракт", "оплата", "fee", "tuition"]
        if any(k in question_l for k in price_keywords):
            if fee:
                answer = (
                    f"По структурированным данным для программы «{program.name}» "
                    f"({uni.name}) стоимость за {fee.year} год: "
                    f"{fee.contract_fee} {fee.currency.value if hasattr(fee.currency, 'value') else fee.currency}."
                )
                if fee.source_document_id:
                    synthetic_sources.append({
                        "document_id": fee.source_document_id,
                        "document_title": f"Source document for ProgramFee ({fee.year})",
                        "page_start": fee.source_page_start or 1,
                        "page_end": fee.source_page_end or fee.source_page_start or 1,
                        "chunk_index": 0,
                        "source_url": None,
                        "local_path": None,
                    })
                return answer, synthetic_sources

        # Вопросы про проходной / требования / дедлайны
        admission_keywords = ["орт", "проход", "балл", "требован", "deadline", "дедлайн", "срок"]
        if any(k in question_l for k in admission_keywords):
            if admission:
                parts = [
                    f"По структурированным данным для программы «{program.name}» ({uni.name}) за {admission.year} год:"
                ]
                if admission.ort_min_score is not None:
                    parts.append(f"минимальный ОРТ: {admission.ort_min_score}.")
                if admission.requirements:
                    parts.append(f"требования: {admission.requirements}.")
                if admission.deadlines:
                    parts.append(f"дедлайны: {admission.deadlines}.")
                answer = " ".join(parts)

                if admission.source_document_id:
                    synthetic_sources.append({
                        "document_id": admission.source_document_id,
                        "document_title": f"Source document for ProgramAdmission ({admission.year})",
                        "page_start": admission.source_page_start or 1,
                        "page_end": admission.source_page_end or admission.source_page_start or 1,
                        "chunk_index": 0,
                        "source_url": None,
                        "local_path": None,
                    })
                return answer, synthetic_sources

        return None, []

    @staticmethod
    def _rows_to_sources_and_snippets(rows: list[tuple[Any, float]]) -> tuple[list[dict], list[dict]]:
        sources: list[dict] = []
        snippets: list[dict] = []
        seen = set()

        for chunk, distance in rows:
            doc = chunk.document
            source = {
                "document_id": doc.id,
                "document_title": doc.title,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "chunk_index": chunk.chunk_index,
                "source_url": _normalize_optional_str(doc.source_url),
                "local_path": _normalize_optional_str(doc.local_path),
            }

            key = (
                source["document_id"],
                source["page_start"],
                source["page_end"],
                source["chunk_index"],
            )
            if key not in seen:
                sources.append(source)
                seen.add(key)

            snippets.append({
                "source": source,
                "text": " ".join((chunk.text or "").split())[:700],
                "distance": float(distance),
            })

        return sources, snippets
    

    def _stub_answer_from_retrieval(self, question: str, rows):
        if not rows:
            return "Не найдено в источниках.", False

        top_chunk, top_distance = rows[0]
        if float(top_distance) > 0.45:
            return "Не найдено в источниках.", False

        q = question.lower()

        # Вопрос про стоимость
        if any(k in q for k in ["стоим", "стоит", "цена", "контракт", "оплата", "tuition", "fee"]):
            degree_target = _detect_degree_target(q)

            # Ищем цену в нескольких чанках, а не только в top-1
            for chunk, distance in rows:
                text = " ".join((chunk.text or "").split())
                text_l = text.lower()

                if not _chunk_matches_degree(text_l, degree_target):
                    continue

                # чуть шире regex на сумму
                m = re.search(r'(\$\s?\d[\d,]*)\s*(?:в\s*год|per\s*year)?', text, re.IGNORECASE)
                if m:
                    if degree_target == "master":
                        return f"По найденному источнику стоимость MBA/магистратуры: {m.group(1)}.", True
                    if degree_target == "bachelor":
                        return f"По найденному источнику стоимость бакалавриата: {m.group(1)} в год.", True
                    return f"По найденному источнику стоимость: {m.group(1)}.", True

            # Цена в источниках есть, но не для нужного уровня/программы
            return "Не найдено в источниках.", False

        # (опционально) можно вернуть сюда старые ветки про экзамены/и т.д.

        # ВАЖНО: финальный fallback, чтобы функция никогда не возвращала None
        return "Не найдено в источниках.", False


    async def ask(
        self, 
        db: AsyncSession,
        question: str,
        top_k: int = 5,
        university_id: int | None = None,
        program_id: int | None = None,
        year: int | None = None,
        document_id: int | None = None,
    ) -> dict:
        # 1) Program-first: пытаемся ответить по структурированным данным
        program_ctx = None
        if program_id is not None:
            program_ctx = await self._get_program_context(db, program_id=program_id, year=year)

            # если university_id не передали, берем из программы
            if university_id is None and program_ctx:
                university_id = program_ctx["university"].id

            structured_answer, structured_sources = self._build_structured_answer(question, program_ctx)
            if structured_answer:
                return {
                    "answer": structured_answer,
                    "found": True,
                    "sources": structured_sources,
                    "snippets": [],
                }

        # 2) RAG по документам университета (fallback / дополнение)
        qv = self.embedder.embed_text(question)
        rows = await retrieve_chunks_pgvector(
            db=db,
            query_vector=qv,
            top_k=top_k,
            university_id=university_id,
            year=year,
            document_id=document_id,
        )

        answer, found = self._stub_answer_from_retrieval(question,rows)
        sources, snippets = self._rows_to_sources_and_snippets(rows)

        # Убираем distance из публичного ответа
        snippets_public = [{"source": s["source"], "text": s["text"]} for s in snippets]

        return {
            "answer": answer,
            "found": found,
            "sources": sources,
            "snippets": snippets_public,
        }