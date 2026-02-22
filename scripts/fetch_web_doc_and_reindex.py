import asyncio
import hashlib
import re
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.db.models.document import Document  # если у тебя экспортируется иначе, поправь импорт
from app.services.rag_bot.rag_indexer import RagIndexer


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
)


def slugify(value: str, max_len: int = 80) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    value = re.sub(r"[-\s]+", "_", value).strip("_")
    return (value or "document")[:max_len]


import re

def postprocess_extracted_text(text: str) -> str:
    if not text:
        return text

    # 1) Склеить разрыв слова переносом: "D\nOCUMENTS" -> "DOCUMENTS"
    # Работает, когда по обе стороны буквы
    text = re.sub(r'(?<=[A-Za-zА-Яа-я])\n(?=[A-Za-zА-Яа-я])', '', text)

    # 2) Убрать переносы вокруг скобок
    text = re.sub(r'\(\s*\n\s*', '(', text)
    text = re.sub(r'\s*\n\s*\)', ')', text)

    # 3) Схлопнуть пробелы внутри строк
    lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.splitlines()]

    # 4) Убрать подряд много пустых строк
    cleaned_lines = []
    empty_streak = 0
    for line in lines:
        if not line:
            empty_streak += 1
            if empty_streak <= 1:
                cleaned_lines.append("")
        else:
            empty_streak = 0
            cleaned_lines.append(line)

    text = "\n".join(cleaned_lines).strip()

    return text

def clean_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # Удаляем шум
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    # Пытаемся взять основной контент, если есть
    root = (
        soup.find("main")
        or soup.find("article")
        or soup.find("div", class_=re.compile(r"content|main|post|entry", re.I))
        or soup.body
        or soup
    )

    text = root.get_text("\n", strip=True)

    # 1) Склеиваем только очень вероятный разрыв внутри слова:
    #    пример: "D\nOCUMENTS" -> "DOCUMENTS"
    #    (слева одна буква как отдельный фрагмент, справа продолжение слова)
    text = re.sub(r'(?<=\b[A-Za-zА-Яа-я])\n(?=[A-Za-zА-Яа-я]{2,}\b)', '', text)

    # 2) Нормализация пробелов/пустых строк
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if line]

    result = "\n".join(lines)

    # 3) Подчистим артефакты со скобками
    result = re.sub(r"\(\s+", "(", result)
    result = re.sub(r"\s+\)", ")", result)

    return result


async def fetch_url_text(url: str, timeout_sec: int = 30) -> tuple[str, str]:
    """
    Возвращает (html, extracted_text)
    """
    headers = {"User-Agent": USER_AGENT}
    async with httpx.AsyncClient(
        headers=headers,
        timeout=timeout_sec,
        follow_redirects=True,
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()

        # httpx сам обычно определяет encoding, но на всякий случай:
        html = resp.text
        text = clean_text_from_html(html)
        return html, text


async def run(document_id: int) -> None:
    async with AsyncSessionLocal() as db:
        # 1) Найти документ
        result = await db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalar_one_or_none()

        if not doc:
            raise ValueError(f"Document id={document_id} не найден")

        if not doc.source_url:
            raise ValueError(f"У Document id={document_id} пустой source_url")

        print(f"[INFO] Document: id={doc.id}, title={doc.title}")
        print(f"[INFO] Source URL: {doc.source_url}")

        # 2) Скачать и извлечь текст
        html, extracted_text = await fetch_url_text(doc.source_url)

        if not extracted_text or len(extracted_text.strip()) < 50:
            raise ValueError("Извлечённый текст слишком короткий / пустой")

        # 3) Подготовить пути
        # Сохраняем TXT (т.к. текущий indexer умеет .txt)
        # Можно хранить рядом и html позже, но сейчас достаточно txt.
        title_slug = slugify(doc.title)
        rel_dir = Path("docs") / "web" / f"university_{doc.university_id}" / str(doc.year)
        abs_dir = Path.cwd() / rel_dir
        abs_dir.mkdir(parents=True, exist_ok=True)

        txt_filename = f"doc_{doc.id}_{title_slug}.txt"
        rel_txt_path = rel_dir / txt_filename
        abs_txt_path = Path.cwd() / rel_txt_path

        # 4) Сохранить текст
        abs_txt_path.write_text(extracted_text, encoding="utf-8")

        # 5) Обновить метаданные документа
        checksum = hashlib.sha256(extracted_text.encode("utf-8")).hexdigest()
        doc.local_path = str(rel_txt_path)  # относительный путь, как у тебя сейчас
        doc.checksum = checksum

        await db.commit()
        print(f"[INFO] Saved text -> {doc.local_path}")
        print(f"[INFO] checksum={checksum[:12]}...")

        # 6) Переиндексация
        indexer = RagIndexer()
        created = await indexer.reindex_document(db=db, document_id=doc.id)

        print(f"[OK] Reindexed document_id={doc.id}, created_chunks={created}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch web page from Document.source_url and reindex it")
    parser.add_argument("document_id", type=int, help="ID документа в таблице documents")
    args = parser.parse_args()

    asyncio.run(run(args.document_id))