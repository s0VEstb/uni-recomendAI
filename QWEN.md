# uni-recomendAI — Контекст проекта

## Обзор проекта

**uni-recomendAI** — сервис рекомендаций университетов и образовательных программ для учеников 9–11 классов Кыргызстана. Система анализирует анкету абитуриента (ОРТ, бюджет, город, интересы) и выдаёт персонализированные рекомендации с объяснениями причин.

### Архитектура

```
┌────────────────────────────────────────────────────────┐
│  React (Vite, TypeScript, port 8080)                   │
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

### Технологический стек

**Backend:**
- Python 3.11+, FastAPI, SQLAlchemy 2.0 (async)
- Alembic (миграции БД)
- pgvector (векторный поиск для RAG)
- sentence-transformers (эмбеддинги)
- Google Gemini API (LLM для RAG-чата)
- JWT аутентификация (python-jose)
- Argon2 (хеширование паролей)
- structlog (логирование)
- SQLAdmin (админ-панель)

**Frontend:**
- React 18 + TypeScript
- Vite (сборка, dev-сервер)
- react-router-dom (маршрутизация)

**Инфраструктура:**
- Docker + Docker Compose (PostgreSQL с pgvector)
- Makefile (удобные команды)

## Структура проекта

```
uni-recomendAition/
├── main.py                     # Точка входа FastAPI
├── app/
│   ├── api/routes/             # API эндпоинты
│   │   ├── auth.py             # Регистрация, логин, сброс пароля
│   │   ├── chat.py             # RAG-чат (SSE stream)
│   │   ├── chat_history.py     # История чатов
│   │   ├── compare.py          # Сравнение программ
│   │   ├── health.py           # Health check
│   │   ├── programs.py         # Программы обучения
│   │   ├── survey.py           # Опросник → рекомендации
│   │   └── tags.py             # Теги (интересы, предметы)
│   ├── core/
│   │   └── config.py           # Настройки (pydantic-settings)
│   ├── crud/                   # CRUD-операции
│   ├── db/
│   │   ├── models/             # SQLAlchemy модели
│   │   │   ├── university.py   # Университеты
│   │   │   ├── tag.py          # Теги
│   │   │   ├── fee_and_admission.py  # Стоимость и поступление
│   │   │   ├── document.py     # Документы
│   │   │   ├── user.py         # Пользователи
│   │   │   └── chat.py         # Чат/сообщения
│   │   ├── repositories/       # Репозитории (data access layer)
│   │   ├── seed_tags.py        # Сид тегов (40+)
│   │   ├── seed_full_catalog.py # Сид каталога (университеты, программы)
│   │   └── database.py         # Подключение к БД
│   ├── services/
│   │   ├── auth_service.py     # Аутентификация
│   │   ├── email_service.py    # Email (сброс пароля)
│   │   ├── survey_service.py   # Обработка опросов
│   │   ├── recommendation_service.py # Рекомендации + scoring
│   │   ├── llm/                # LLM провайдер (Gemini)
│   │   └── rag_bot/            # RAG-система
│   │       ├── retrieval_service.py  # Векторный поиск
│   │       ├── rag_indexer.py        # Индексация документов
│   │       ├── embedding_provider.py # Эмбеддинги
│   │       ├── chunking.py           # Чанкинг документов
│   │       └── text_extract.py       # Извлечение текста
│   ├── admin/                  # SQLAdmin панель
│   ├── schemas/                # Pydantic схемы
│   ├── middleware/             # Middleware
│   └── utils/                  # Утилиты
├── frontend/                   # React фронтенд
│   ├── src/
│   └── package.json
├── alembic/                    # Миграции БД
├── docker-compose.yml          # PostgreSQL + pgvector
├── Makefile                    # Команды разработки
└── requirements.txt            # Python зависимости
```

## Сборка и запуск

### Предварительные требования

- Python 3.11+
- Node.js 18+
- Docker и Docker Compose

### Быстрый старт

```bash
# 1. Клонировать и настроить окружение
cp .env.example .env          # Заполните реальные значения

# 2. Поднять PostgreSQL с pgvector
docker compose up -d
# Подождать ~5 сек до готовности БД

# 3. Создать виртуальное окружение и установить зависимости
make venv                      # или: python3 -m venv venv && pip install -r requirements.txt

# 4. Применить миграции (создаёт все таблицы + pgvector extension)
make migrate                   # или: alembic upgrade head

# 5. Заполнить базу данными
make seed                      # seed-tags + seed-catalog

# 6. Запустить backend
make run-dev                   # uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 7. Запустить frontend (отдельный терминал)
make frontend-dev              # cd frontend && npm install && npm run dev
```

**Доступ:**
- Frontend: http://localhost:8080
- Swagger UI (API docs): http://localhost:8000/docs
- Админка: http://localhost:8000/admin

### Основные команды Makefile

| Команда | Описание |
|---------|----------|
| `make venv` | Создать виртуальное окружение |
| `make install` | Установить зависимости |
| `make run-dev` | Запустить backend (uvicorn --reload) |
| `make migrate` | Применить миграции |
| `make makemigrations m="msg"` | Создать миграцию |
| `make downgrade` | Откатить последнюю миграцию |
| `make seed-tags` | Заполнить теги |
| `make seed-catalog` | Заполнить каталог |
| `make seed` | Заполнить всё (теги + каталог) |
| `make frontend-dev` | Запустить frontend |

## API Reference

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
| GET | `/api/programs/{id}` | — | Программа по ID |
| POST | `/api/compare` | — | Сравнить 2–5 программ |
| POST | `/api/chat/` | — | RAG-чат (SSE stream) |

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
| `GEMINI_MODEL` | Модель Gemini (по умолчанию: gemini-2.5-flash-lite) |
| `RAG_LLM_PROVIDER` | LLM провайдер (по умолчанию: gemini) |
| `JWT_SECRET` | Секрет для подписи JWT токенов |
| `MAIL_USERNAME`, `APP_PASSWORD`, `MAIL_FROM` | Email (опционально, для сброса пароля) |
| `DEBUG` | Режим отладки |
| `APP_NAME` | Имя приложения |

## Особенности разработки

### Backend

- **Async-first**: используется async/await с SQLAlchemy async engine
- **Repository pattern**: доступ к БД через репозитории в `app/db/repositories/`
- **Service layer**: бизнес-логика в `app/services/`
- **Pydantic v2**: схемы валидации в `app/schemas/`
- **JWT auth**: токены через python-jose с Argon2 хешированием паролей

### Frontend

- React 18 + TypeScript, маршрутизация через react-router-dom
- Vite dev сервер на порту 8080 с прокси `/api` → `localhost:8000`
- Маршруты: `/login`, `/register`, `/survey`, `/results`

### База данных

- PostgreSQL 16 с расширением pgvector
- Векторные эмбеддинги (384 dim) для RAG поиска по документам
- Alembic для миграций

### RAG-чат

- Документы чанкаются, эмбеддируются (sentence-transformers) и индексируются в pgvector
- Поиск релевантных чанков → Gemini генерирует ответ с контекстом
- SSE (Server-Sent Events) для потоковой отдачи ответов
