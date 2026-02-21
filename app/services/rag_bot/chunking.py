def chunk_pages(pages: list[dict], chunk_size: int = 1000, overlap: int = 150) -> list[dict]:
    chunks: list[dict] = []

    for page_data in pages:
        page_num = page_data["page"]
        text = (page_data.get("text") or "").strip()
        if not text:
            continue

        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunk_text = text[start:end].strip()

            if len(chunk_text) >= 50:
                chunks.append({
                    "page_start": page_num,
                    "page_end": page_num,
                    "text": chunk_text,
                })

            if end == text_len:
                break
            start = max(0, end - overlap)

    return chunks