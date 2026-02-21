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
            raw_start = start
            raw_end = min(start + chunk_size, text_len)

            # Подравниваем начало чанка: если попали в середину слова — сдвигаем вправо до пробела
            chunk_start = raw_start
            if chunk_start > 0 and chunk_start < text_len:
                if not text[chunk_start - 1].isspace():
                    while chunk_start < raw_end and not text[chunk_start].isspace():
                        chunk_start += 1
                    # пропускаем сами пробелы
                    while chunk_start < raw_end and text[chunk_start].isspace():
                        chunk_start += 1

            # Подравниваем конец чанка: если попали в середину слова — сдвигаем вправо до пробела
            chunk_end = raw_end
            if chunk_end < text_len and not text[chunk_end - 1].isspace():
                while chunk_end < text_len and not text[chunk_end].isspace():
                    chunk_end += 1

            # Фолбэк, если границы "съехали" слишком сильно
            if chunk_start >= chunk_end:
                chunk_start = raw_start
                chunk_end = raw_end

            chunk_text = text[chunk_start:chunk_end].strip()

            if len(chunk_text) >= 50:
                chunks.append({
                    "page_start": page_num,
                    "page_end": page_num,
                    "text": chunk_text,
                })

            if raw_end == text_len:
                break

            # Важно: прогресс цикла считаем от RAW-границы, чтобы не поймать зацикливание
            start = max(0, raw_end - overlap)

    return chunks