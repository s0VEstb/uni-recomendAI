from __future__ import annotations

from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer


class LocalEmbeddingService:
    """
    Локальные эмбеддинги для RAG.
    Модель: paraphrase-multilingual-MiniLM-L12-v2 (384 dim)
    """

    MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    VECTOR_DIM = 384

    def __init__(self) -> None:
        self.model = SentenceTransformer(self.MODEL_NAME)

    @staticmethod
    def _normalize_text(text: str) -> str:
        text = (text or "").replace("\xa0", " ")
        text = " ".join(text.split())
        return text.strip()

    def embed_text(self, text: str) -> list[float]:
        norm_text = self._normalize_text(text)
        if not norm_text:
            return [0.0] * self.VECTOR_DIM

        vec = self.model.encode(
            norm_text,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vec.astype(np.float32).tolist()

    def embed_texts(self, texts: List[str], batch_size: int = 8) -> list[list[float]]:
        clean_texts = [self._normalize_text(t) for t in texts]
        if not clean_texts:
            return []

        vectors = self.model.encode(
            clean_texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        return [v.astype(np.float32).tolist() for v in vectors]