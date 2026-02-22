from app.services.rag_bot.local_embeddings import LocalEmbeddingService


def main():
    svc = LocalEmbeddingService()

    q = "Сколько стоит бакалавриат в AUCA?"
    t = "Программа бакалавриата на 2025–2026 учебный год: $7150 в год."

    v1 = svc.embed_text(q)
    v2 = svc.embed_text(t)

    print("len(v1):", len(v1))
    print("len(v2):", len(v2))
    print("first 5:", v1[:5])


if __name__ == "__main__":
    main()