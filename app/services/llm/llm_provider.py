from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, AsyncGenerator

# Гарантируем загрузку .env даже если uvicorn запущен не через main.py
try:
    from dotenv import load_dotenv as _load_dotenv
    _load_dotenv(Path(__file__).resolve().parents[3] / ".env", override=True)
except ImportError:
    pass  # python-dotenv не установлен — переменные должны быть в os.environ


class BaseLLMProvider:
    async def answer_from_context(self, question: str, snippets: List[Dict[str, Any]]) -> Optional[str]:
        raise NotImplementedError
    
    async def answer_from_context_stream(self, question: str, snippets: List[Dict[str, Any]]) -> AsyncGenerator[str, None]:
        yield "Streaming not supported"


class NullLLMProvider(BaseLLMProvider):
    async def answer_from_context(self, question: str, snippets: List[Dict[str, Any]]) -> Optional[str]:
        return None
    
    async def answer_from_context_stream(self, question: str, snippets: List[Dict[str, Any]]) -> AsyncGenerator[str, None]:
        yield "Provider not configured"


class GeminiLLMProvider(BaseLLMProvider):
    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY")
        # Можно писать просто 'gemini-3.5-flash-lite' — префикс 'models/' добавится автоматически
        raw_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
        self.model = raw_model if raw_model.startswith("models/") else f"models/{raw_model}"

        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not set in .env")



        # Базовые настройки контекста (можешь подкрутить через env)
        self.max_snippets_default = int(os.getenv("RAG_LLM_MAX_SNIPPETS", "4"))
        self.max_chars_default = int(os.getenv("RAG_LLM_MAX_CHARS", "600"))
        self.max_chars_numeric = int(os.getenv("RAG_LLM_MAX_CHARS_NUMERIC", "900"))  # для баллов/таблиц

        from google import genai
        self.client = genai.Client(api_key=self.api_key)

    # ------------------------------
    # Heuristics
    # ------------------------------
    @staticmethod
    def _is_score_question(question: str) -> bool:
        q = (question or "").lower()
        markers = [
            "балл", "баллы", "проход", "проходной", "минимальн", "минимум",
            "score", "scores", "scoring", "minimum", "cutoff", "cut-off",
            "sat", "act", "орт", "ort"
        ]
        return any(m in q for m in markers)

    @staticmethod
    def _is_registration_question(question: str) -> bool:
        q = (question or "").lower()
        markers = ["регистрац", "register", "registration", "документ", "requirements", "required"]
        return any(m in q for m in markers)

    @staticmethod
    def _count_numbers(text: str) -> int:
        return len(re.findall(r"\b\d{1,4}\b", text or ""))

    def _snippet_bonus(self, question: str, sn: Dict[str, Any]) -> int:
        q = (question or "").lower()
        src = sn.get("source", {}) or {}
        title = (src.get("document_title") or "").lower()
        text = (sn.get("text") or "").lower()

        bonus = 0

        # Бонусы для вопросов про баллы
        if self._is_score_question(question):
            if any(k in title for k in ["балл", "scoring", "score", "scores"]):
                bonus += 120
            if any(k in title for k in ["admission", "exam", "freshman"]):
                bonus += 15

            # Ключевые признаки числовой таблицы/эквивалентов
            if any(k in text for k in ["sat", "act", "essay", "math", "орт", "ort", "балл", "score"]):
                bonus += 30

            # Чем больше чисел, тем вероятнее, что это нужный кусок для "минимальных баллов"
            bonus += min(self._count_numbers(text), 20) * 2

        # Бонусы для вопросов про регистрацию
        if self._is_registration_question(question):
            if any(k in title for k in ["register", "registration", "aae", "exam"]):
                bonus += 80
            if any(k in text for k in ["passport", "fee", "сом", "photo", "форма", "document", "регистрац"]):
                bonus += 20

        # Лёгкий бонус за прямое вхождение слов из вопроса в title/text
        for token in re.findall(r"[a-zA-Zа-яА-ЯёЁ]{4,}", q):
            if token in title:
                bonus += 5
            elif token in text:
                bonus += 1

        return bonus

    def _select_snippets_for_prompt(
        self,
        question: str,
        snippets: List[Dict[str, Any]],
        max_snippets: int,
    ) -> List[Dict[str, Any]]:
        """
        Умный отбор вместо snippets[:max_snippets]:
        - бонусы по title/text под тип вопроса
        - дедуп по document_id
        - fallback добор, если не хватает
        """
        if not snippets:
            return []

        ranked = []
        for sn in snippets:
            dist = float(sn.get("distance", 999.0))  # меньше = лучше
            bonus = self._snippet_bonus(question, sn)
            # сортировка: bonus ↑, distance ↓(т.е. -dist ↑)
            ranked.append((bonus, -dist, sn))

        ranked.sort(
            key=lambda t: (int(t[0] or 0), float(t[1] or -9999.0)),
            reverse=True
        )   

        selected: List[Dict[str, Any]] = []
        seen_docs = set()

        # 1) Сначала стараемся взять разные документы
        for bonus, neg_dist, sn in ranked:
            doc_id = (sn.get("source") or {}).get("document_id")
            if doc_id in seen_docs:
                continue
            selected.append(sn)
            if doc_id is not None:
                seen_docs.add(doc_id)
            if len(selected) >= max_snippets:
                return selected

        # 2) Если не хватило (редкий случай) — добираем без дедупа
        if len(selected) < max_snippets:
            selected_ids = {id(x) for x in selected}
            for _, _, sn in ranked:
                if id(sn) in selected_ids:
                    continue
                selected.append(sn)
                if len(selected) >= max_snippets:
                    break

        return selected

    def _chars_limit_for_snippet(self, question: str, sn: Dict[str, Any]) -> int:
        """
        Для табличных/числовых вопросов даём больше символов, особенно если чанк похож на scoring/score.
        """
        base = self.max_chars_default
        if not self._is_score_question(question):
            return base

        src = sn.get("source", {}) or {}
        title = (src.get("document_title") or "").lower()
        text = (sn.get("text") or "").lower()

        if any(k in title for k in ["балл", "scoring", "score", "scores"]):
            return self.max_chars_numeric
        if any(k in text for k in ["sat", "act", "essay", "math", "орт", "ort", "балл", "score"]):
            return self.max_chars_numeric
        return base

    def _build_context(self, question: str, snippets: List[Dict[str, Any]]) -> str:
        max_snippets = self.max_snippets_default

        selected = self._select_snippets_for_prompt(
            question=question,
            snippets=snippets,
            max_snippets=max_snippets,
        )
        
        debug_titles = [
            (sn.get("source", {}) or {}).get("document_title", "Unknown")
            for sn in selected
        ]
        print(f"[llm-context] selected_titles={debug_titles}")

        blocks = []
        for i, sn in enumerate(selected, start=1):
            src = sn.get("source", {}) or {}
            title = src.get("document_title", "Unknown document")
            text = (sn.get("text") or "").strip()
            char_limit = self._chars_limit_for_snippet(question, sn)
            text = text[:char_limit]
            blocks.append(f"[SOURCE {i}] {title}\n{text}")

        return "\n\n".join(blocks)

    def _get_prompt(self, question: str, context: str) -> str:
        # Можно слегка ужесточить краткость, чтобы уменьшить total
        return f"""
Ты — помощник по поступлению в университеты.

Правила ответа:
1) Отвечай ТОЛЬКО по контексту из источников ниже.
2) Если точного ответа в контексте нет, ответь ровно: Не найдено в источниках.
3) Не придумывай факты.
4) Отвечай по факту, как оно есть, можешь более детально раскрыть, но не нужно делать длинные рассуждения или уходить в общие фразы.
5) Если вопрос про баллы/минимум/проходной — обязательно укажи конкретные числа, если они есть в контексте.
6) Отвечай структурировано (списком)

Вопрос:
{question}

Контекст:
{context}
""".strip()

    async def answer_from_context_stream(self, question: str, snippets: List[Dict[str, Any]]) -> AsyncGenerator[str, None]:
        if not snippets:
            yield "Не найдено в источниках."
            return

        context = self._build_context(question, snippets)
        prompt = self._get_prompt(question, context)

        try:
            response = self.client.models.generate_content_stream(
                model=self.model,
                contents=prompt,
            )

            found_any = False
            for chunk in response:
                text = getattr(chunk, "text", None)
                if text:
                    found_any = True
                    yield text

            if not found_any:
                yield "Не найдено в источниках."
        except Exception as e:
            yield f"Ошибка генерации: {str(e)}"

    async def answer_from_context(self, question: str, snippets: List[Dict[str, Any]]) -> Optional[str]:
        full_text = []
        async for part in self.answer_from_context_stream(question, snippets):
            full_text.append(part)
        return "".join(full_text)


def get_llm_provider() -> BaseLLMProvider:
    provider = (os.getenv("RAG_LLM_PROVIDER") or "none").lower()
    if provider == "gemini":
        return GeminiLLMProvider()
    return NullLLMProvider()