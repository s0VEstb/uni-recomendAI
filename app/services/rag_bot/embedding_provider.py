from app.services.rag_bot.local_embeddings import LocalEmbeddingService

_embedder_instance: LocalEmbeddingService | None = None


def get_embedder() -> LocalEmbeddingService:
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = LocalEmbeddingService()
    return _embedder_instance