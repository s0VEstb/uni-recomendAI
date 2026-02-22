def extract_text_file(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    return [{"page": 1, "text": text}]