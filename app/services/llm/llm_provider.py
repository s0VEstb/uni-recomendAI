from __future__ import annotations

import os
from typing import Optional, List, Dict, Any, AsyncGenerator


class BaseLLMProvider:
    async def answer_from_context(self, question: str, snippets: List[Dict[str, Any]]) -> Optional[str]:
        raise NotImplementedError
    
    # Добавляем метод для стриминга
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
        self.model = os.getenv("GEMINI_MODEL")

        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")

        from google import genai 
        self.client = genai.Client(api_key=self.api_key)

    @staticmethod
    def _build_context(snippets: List[Dict[str, Any]], max_snippets: int = 4, max_chars_each: int = 800) -> str:
        blocks = []
        for i, sn in enumerate(snippets[:max_snippets], start=1):
            src = sn.get("source", {})
            title = src.get("document_title", "Unknown document")
            text = (sn.get("text") or "").strip()[:max_chars_each]
            blocks.append(f"[SOURCE {i}] {title}\n{text}")
        return "\n\n".join(blocks)

    def _get_prompt(self, question: str, context: str) -> str:
        return f"""
Ты — помощник по поступлению в университеты.

Правила ответа:
1) Отвечай ТОЛЬКО по контексту из источников ниже.
2) Если точного ответа в контексте нет, ответь ровно: Не найдено в источниках.
3) Не придумывай факты.
4) Отвечай по факту, как оно есть.

Вопрос:
{question}

Контекст:
{context}
""".strip()

    async def answer_from_context_stream(self, question: str, snippets: List[Dict[str, Any]]) -> AsyncGenerator[str, None]:
        """Нативная поддержка потоковой передачи текста."""
        if not snippets:
            yield "Не найдено в источниках."
            return

        context = self._build_context(snippets)
        prompt = self._get_prompt(question, context)

        # Используем асинхронный генератор из SDK
        try:
            # Метод для стриминга в новом google-genai SDK
            response = self.client.models.generate_content_stream(
                model=self.model,
                contents=prompt,
            )
            
            found_any = False
            for chunk in response:
                if chunk.text:
                    found_any = True
                    yield chunk.text
            
            if not found_any:
                yield "Не найдено в источниках."
        except Exception as e:
            yield f"Ошибка генерации: {str(e)}"

    async def answer_from_context(self, question: str, snippets: List[Dict[str, Any]]) -> Optional[str]:
        """Обычный метод, если стриминг не нужен (собирает поток в строку)."""
        full_text = []
        async for part in self.answer_from_context_stream(question, snippets):
            full_text.append(part)
        return "".join(full_text)


def get_llm_provider() -> BaseLLMProvider:
    provider = (os.getenv("RAG_LLM_PROVIDER") or "none").lower()
    if provider == "gemini":
        return GeminiLLMProvider()
    return NullLLMProvider()