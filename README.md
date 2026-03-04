# uni-recomendAI

Сервис рекомендаций университетов и программ для учеников 9–11 классов Кыргызстана.
Система анализирует анкету абитуриента (ОРТ, бюджет, город, интересы) и выдаёт персонализированные рекомендации с объяснениями причин.

## Требования

- **Python** 3.11+
- **Node.js** 18+
- **Docker** и Docker Compose

## Quick Start

```bash
# 1. Клонировать и настроить окружение
git clone <repo-url>
cd uni-recomendAI
cp .env.example .env          # Заполните реальные значения

# 2. Поднять PostgreSQL с pgvector
docker compose up -d
# Подождать ~5 сек до готовности БД

# 3. Установить Python зависимости
pip install -r requirements.txt

# 4. Применить миграции (создаёт все таблицы + pgvector extension)
alembic upgrade head

# 5. Заполнить базу данными
python -m app.db.seed_tags          # 40+ тегов (интересы, сильные стороны, предметы)
python -m app.db.seed_full_catalog  # Университеты, программы, fees, admissions, documents

# 6. Запустить backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 7. Запустить frontend (отдельный терминал)
cd frontend && npm install && npm run dev
```

Открыть:
- **Frontend**: http://localhost:8080
- **Swagger UI**: http://localhost:8000/docs
- **Админка**: http://localhost:8000/admin

## Makefile (удобные команды)

```bash
make migrate          # alembic upgrade head
make seed-tags        # python -m app.db.seed_tags
make seed-catalog     # python -m app.db.seed_full_catalog
make seed             # seed-tags + seed-catalog
make frontend-dev     # npm install && npm run dev
make run-dev          # uvicorn (linux/mac)
```

## API

| Метод | Путь | Auth | Описание |
|-------|------|------|---------|
| GET | `/api/health` | — | Статус сервиса |
| POST | `/api/auth/register` | — | Регистрация |
| POST | `/api/auth/login` | — | Логин → JWT токен |
| POST | `/api/auth/forgot-password` | — | Запрос сброса пароля |
| POST | `/api/auth/reset-password` | — | Сброс пароля |
| GET | `/api/tags` | — | Список тегов (фильтр по `?tag_type=`) |
| POST | `/api/survey/submit` | JWT | Отправить анкету → рекомендации |
| GET | `/api/survey/latest` | JWT | Последняя анкета + рекомендации |
| GET | `/api/universities/{uid}/programs/{pid}` | — | Программа по UID и PID |
| GET | `/api/programs/{id}` | — | Программа по ID (удобнее для фронта) |
| POST | `/api/compare` | — | Сравнить 2–5 программ |
| POST | `/api/chat/` | — | RAG-чат (SSE stream) |

## Архитектура

```
┌────────────────────────────────────────────────────────┐
│  React (Vite, port 8080)                               │
│  Landing → Register → Survey → Results → Compare       │
│                         ↕ /api (Vite proxy)            │
├────────────────────────────────────────────────────────┤
│  FastAPI (uvicorn, port 8000)                          │
│  Routes: auth | tags | survey | programs | compare | chat │
│  Services: SurveyService → RecommendationService       │
│  Admin: SQLAdmin (/admin)                              │
├────────────────────────────────────────────────────────┤
│  PostgreSQL 16 + pgvector (Docker, port 5433)         │
│  10 таблиц: University, Program, Tag, ProgramTag,      │
│  ProgramFee, ProgramAdmission, User, SurveySubmission, │
│  SavedProgram, Document, DocumentChunk (Vector 384)    │
└────────────────────────────────────────────────────────┘
```

### Scoring (причины рекомендаций)

| Код | Описание |
|-----|---------|
| `budget_ok` | Программа вписывается в бюджет |
| `budget_too_low` | Бюджет ниже стоимости контракта |
| `fee_unknown` | Стоимость не указана |
| `tag_match` | Совпадение с выбранными интересами |
| `ort_ok` | Проходит по ОРТ |
| `ort_unknown_or_not_required` | Порог ОРТ не указан |
| `city_match` | Университет в выбранном городе |

## Переменные окружения

Скопируй `.env.example` → `.env` и заполни:

| Переменная | Описание |
|-----------|---------|
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASS` | PostgreSQL (порт 5433 в Docker) |
| `GEMINI_API_KEY` | Google Gemini API (для RAG-чата) |
| `JWT_SECRET` | Секрет для подписи JWT токенов |
| `MAIL_USERNAME`, `APP_PASSWORD`, `MAIL_FROM` | Email (опционально, для сброса пароля) |
