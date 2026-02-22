from __future__ import annotations
import re
import time
import json
from typing import Any, AsyncGenerator, List, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.services.rag_bot.retrieval_service import retrieve_chunks_pgvector
from app.services.llm.llm_provider import get_llm_provider
from app.db.models import University, Program, ProgramFee, ProgramAdmission
from app.services.rag_bot.embedding_provider import get_embedder

def _normalize_optional_str(value):
    if value in (None, "", "None", "null", "NULL"):
        return None
    return value

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
        if any(m in text_l for m in bachelor_markers) and not any(m in text_l for m in master_markers):
            return False
        return any(m in text_l for m in master_markers)
    if degree_target == "bachelor":
        if any(m in text_l for m in master_markers) and not any(m in text_l for m in bachelor_markers):
            return False
        return any(m in text_l for m in bachelor_markers)
    return True

class RagChatService:
    def __init__(self) -> None:
        self.embedder = get_embedder()
        self.llm = get_llm_provider()

    @staticmethod
    def _clean_text(text: str, limit: int = 900) -> str:
        return " ".join((text or "").split())[:limit]

    async def _get_program_context(self, db: AsyncSession, program_id: int, year: int | None = None) -> dict | None:
        result = await db.execute(
            select(Program)
            .options(joinedload(Program.university))
            .where(Program.id == program_id)
        )
        program = result.scalar_one_or_none()
        if not program: return None

        target_year = year or 2026
        fee_result = await db.execute(
            select(ProgramFee)
            .where(ProgramFee.program_id == program_id)
            .order_by((ProgramFee.year == target_year).desc(), ProgramFee.year.desc())
            .limit(1)
        )
        fee = fee_result.scalar_one_or_none()

        adm_result = await db.execute(
            select(ProgramAdmission)
            .where(ProgramAdmission.program_id == program_id)
            .order_by((ProgramAdmission.year == target_year).desc(), ProgramAdmission.year.desc())
            .limit(1)
        )
        admission = adm_result.scalar_one_or_none()

        return {"program": program, "university": program.university, "fee": fee, "admission": admission}

    def _build_structured_answer(self, question: str, program_ctx: dict | None) -> tuple[str | None, list[dict]]:
        if not program_ctx: return None, []
        question_l = question.lower()
        program, uni, fee, admission = program_ctx["program"], program_ctx["university"], program_ctx["fee"], program_ctx["admission"]
        synthetic_sources = []

        # Цена
        if any(k in question_l for k in ["стоим", "цена", "контракт", "оплата", "fee", "tuition"]):
            if fee:
                ans = f"По структурированным данным «{program.name}» ({uni.name}) стоимость за {fee.year} год: {fee.contract_fee} {fee.currency}."
                if fee.source_document_id:
                    synthetic_sources.append({"document_id": fee.source_document_id, "document_title": f"Fee info {fee.year}", "page_start": 1, "page_end": 1, "chunk_index": 0})
                return ans, synthetic_sources

        # Admission
        if any(k in question_l for k in ["орт", "проход", "балл", "требован", "deadline", "дедлайн"]):
            if admission:
                parts = [f"Данные по «{program.name}» ({uni.name}) за {admission.year} год:"]
                if admission.ort_min_score: parts.append(f"ОРТ: {admission.ort_min_score}.")
                if admission.requirements: parts.append(f"Требования: {admission.requirements}.")
                answer = " ".join(parts)
                if admission.source_document_id:
                    synthetic_sources.append({"document_id": admission.source_document_id, "document_title": f"Admission info {admission.year}", "page_start": 1, "page_end": 1, "chunk_index": 0})
                return answer, synthetic_sources
        return None, []

    @staticmethod
    def _rows_to_sources_and_snippets(rows: list[tuple[Any, float]]) -> tuple[list[dict], list[dict]]:
        sources, snippets, seen = [], [], set()
        for chunk, distance in rows:
            doc = chunk.document
            source = {
                "document_id": doc.id, "document_title": doc.title,
                "page_start": chunk.page_start, "page_end": chunk.page_end,
                "chunk_index": chunk.chunk_index,
                "source_url": _normalize_optional_str(doc.source_url),
                "local_path": _normalize_optional_str(doc.local_path),
            }
            key = (source["document_id"], source["page_start"], source["chunk_index"])
            if key not in seen:
                sources.append(source)
                seen.add(key)
            snippets.append({"source": source, "text": " ".join((chunk.text or "").split())[:900], "distance": float(distance)})
        return sources, snippets

    async def ask_stream(
        self, db: AsyncSession, question: str, top_k: int = 5,
        university_id: int | None = None, program_id: int | None = None,
        year: int | None = None, document_id: int | None = None
    ) -> AsyncGenerator[str, None]:
        """
        Главный метод для API. Стримит ответ по частям.
        """
        t0 = time.perf_counter()
        
        # 1. Сначала проверяем таблицы (Program-first)
        if program_id:
            ctx = await self._get_program_context(db, program_id, year)
            if ctx:
                if university_id is None: university_id = ctx["university"].id
                s_ans, s_src = self._build_structured_answer(question, ctx)
                if s_ans:
                    yield json.dumps({"sources": s_src, "found": True}) + "\n--METADATA_END--\n"
                    yield s_ans
                    return

        # 2. RAG поиск
        qv = self.embedder.embed_text(question)
        t1 = time.perf_counter()
        
        rows = await retrieve_chunks_pgvector(db, qv, top_k, university_id, year, document_id)
        t2 = time.perf_counter()
        
        sources, snippets = self._rows_to_sources_and_snippets(rows)
        
        # Отправляем метаданные фронтенду первым куском
        yield json.dumps({"sources": sources, "found": len(rows) > 0}) + "\n--METADATA_END--\n"

        # 3. Стриминг из LLM
        if not rows:
            yield "Не найдено в источниках."
        else:
            async for chunk in self.llm.answer_from_context_stream(question, snippets):
                yield chunk
        
        t3 = time.perf_counter()
        print(f"[chat stream] embed={t1-t0:.2f}s retrieve={t2-t1:.2f}s total={t3-t0:.2f}s")