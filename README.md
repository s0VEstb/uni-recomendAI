# uni-recomendAI

Сервис рекомендаций университетов и программ для учеников 9-11 классов Кыргызстана.

Backend: FastAPI + SQLAlchemy + Alembic + PostgreSQL/pgvector.  
Frontend: React + Vite.

## Что нужно установить заранее

- Python 3.11+
- Node.js 18+
- Docker Desktop или Docker Engine с Docker Compose
- Git

## Установка с нуля

### 1. Клонировать проект

```bash
git clone <repo-url>
cd uni-recomendAition
```

Если папка в репозитории называется иначе, просто зайди в корень проекта, где лежат `main.py`, `docker-compose.yml`, `requirements.txt`.

### 2. Создать `.env`

```bash
cp .env.example .env
```

Для локального запуска значения PostgreSQL из `.env.example` уже подходят:

```env
DB_HOST=localhost
DB_PORT=5433
DB_NAME=uni
DB_USER=app
DB_PASS=app
DEBUG=true
```

Обязательно поменяй:

```env
JWT_SECRET=change-me-to-a-long-random-string
```

Для RAG-чата нужен Gemini:

```env
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.5-flash-lite
RAG_LLM_PROVIDER=gemini
```

Если ключа нет, backend и обычные рекомендации запустятся, но чат с LLM нормально отвечать не будет.

### 3. Поднять PostgreSQL с pgvector

```bash
docker compose up -d
```

Контейнер поднимает PostgreSQL 16 + pgvector на локальном порту `5433`.

Важно: текущий `docker-compose.yml` запускает только базу данных. Backend и frontend запускаются отдельными командами ниже.

### 4. Создать Python-окружение и поставить зависимости

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

На Windows:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Применить миграции

```bash
alembic upgrade head
```

Это создаст таблицы и расширение `vector` для RAG-эмбеддингов.

### 6. Заполнить базовые данные

```bash
python -m app.db.seed_tags
python -m app.db.seed_full_catalog
```

Или одной командой:

```bash
make seed
```

Сиды создают:

- теги для анкеты и программ;
- университеты;
- программы;
- стоимость обучения;
- правила поступления;
- seed-документы, на которые ссылаются fees/admissions.

### 7. Добавить локальные AUCA-документы для RAG

В репозитории уже лежат текстовые документы AUCA:

```text
docs/web/university_2/2026/
```

На чистой базе AUCA создается с `id=2`, поэтому можно выполнить:

```bash
python scripts/import_auca_local_docs.py \
  --university-id 2 \
  --year 2026 \
  --base-dir docs/web/university_2/2026
```

Если база не чистая и `id` мог измениться, проверь AUCA в админке `http://localhost:8000/admin/university/list` или SQL-запросом:

```bash
docker compose exec db psql -U app -d uni -c "select id, name from universities where website = 'https://auca.kg';"
```

### 8. Нарезать документы на чанки и построить эмбеддинги

```bash
python scripts/reindex_all_documents.py --university-id 2 --year 2026
```

Первый запуск скачает модель `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, поэтому нужен интернет. После этого в таблице `document_chunks` появятся чанки с векторами.

Если увидишь `SKIP` для `seed/2/fee_table_2026.pdf` и `seed/2/admission_rules_2026.pdf`, это нормально: это технические seed-документы без локальных файлов. Важны AUCA-документы из `docs/web/university_2/2026`.

### 9. Запустить backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Открыть:

- API health: http://localhost:8000/api/health
- Swagger UI: http://localhost:8000/docs
- Админка: http://localhost:8000/admin

В браузере открывай именно `localhost` или `127.0.0.1`, а не `0.0.0.0`. Адрес `0.0.0.0` нужен uvicorn только для прослушивания порта.

### 10. Запустить frontend

В другом терминале:

```bash
cd frontend
npm install
npm run dev
```

Открыть frontend:

```text
http://localhost:8080
```

Vite проксирует запросы `/api` на backend `http://127.0.0.1:8000`.

## Быстрый сценарий после `git clone`

```bash
cp .env.example .env
docker compose up -d

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

alembic upgrade head
python -m app.db.seed_tags
python -m app.db.seed_full_catalog

python scripts/import_auca_local_docs.py --university-id 2 --year 2026 --base-dir docs/web/university_2/2026
python scripts/reindex_all_documents.py --university-id 2 --year 2026

uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Второй терминал:

```bash
cd frontend
npm install
npm run dev
```

## Удобные команды Makefile

```bash
make venv          # создать venv и установить Python-зависимости
make install       # установить Python-зависимости в существующий venv
make migrate       # alembic upgrade head
make seed-tags     # заполнить теги
make seed-catalog  # заполнить каталог университетов и программ
make seed          # seed-tags + seed-catalog
make run-dev       # запустить backend через venv/bin/uvicorn
make frontend-dev  # npm install + npm run dev в frontend
```

Важно: `make run-dev` ожидает, что папка `venv` уже создана.

## Как работать с данными в админке

Админка доступна по адресу:

```text
http://localhost:8000/admin
```

Основные разделы:

- `University` - университеты.
- `Program` - программы.
- `ProgramFee` - стоимость программ.
- `ProgramAdmission` - правила поступления и минимальные баллы.
- `Document` - документы-источники.
- `DocumentChunk` - чанки документов для RAG.
- `Tag` и `ProgramTag` - теги и связь тегов с программами.

Если добавляешь новый документ через админку:

1. Создай или обнови запись в `Document`.
2. Заполни `university_id`, `title`, `doc_type`, `year`, `local_path`.
3. Положи текстовый файл по указанному `local_path` относительно корня проекта.
4. Запусти переиндексацию:

```bash
python scripts/reindex_all_documents.py --university-id <ID> --year <YEAR>
```

Для одного документа можно использовать `scripts/reindex_one_doc.py`, но в нем сейчас `document_id` прописан внутри файла, поэтому перед запуском нужно поменять значение в скрипте.

## API

| Метод | Путь | Auth | Описание |
| --- | --- | --- | --- |
| GET | `/api/health` | - | Статус сервиса |
| POST | `/api/auth/register` | - | Регистрация |
| POST | `/api/auth/login` | - | Логин, возвращает JWT |
| POST | `/api/auth/forgot-password` | - | Запрос сброса пароля |
| POST | `/api/auth/reset-password` | - | Сброс пароля |
| GET | `/api/tags` | - | Список тегов |
| POST | `/api/survey/submit` | JWT | Отправить анкету и получить рекомендации |
| GET | `/api/survey/latest` | JWT | Последняя анкета пользователя |
| GET | `/api/programs/{id}` | - | Программа по ID |
| POST | `/api/compare` | - | Сравнить 2-5 программ |
| POST | `/api/chat/` | - | RAG-чат через SSE stream |

## Проверка, что все поднялось

Backend:

```bash
curl http://localhost:8000/api/health
```

База:

```bash
docker compose exec db psql -U app -d uni -c "select count(*) from universities;"
docker compose exec db psql -U app -d uni -c "select count(*) from documents;"
docker compose exec db psql -U app -d uni -c "select count(*) from document_chunks;"
```

Если `document_chunks = 0`, RAG-документы еще не переиндексированы.

## Частые проблемы

### `connection refused` к PostgreSQL

Проверь, что контейнер запущен:

```bash
docker compose ps
```

Если не запущен:

```bash
docker compose up -d
```

### Swagger показывает `TypeError: Load failed`

Обычно это значит, что браузер не смог достучаться до backend.

Проверь, что uvicorn запущен в отдельном терминале:

```bash
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Потом проверь health напрямую:

```bash
curl http://localhost:8000/api/health
```

Ожидаемый ответ:

```json
{"status":"ok"}
```

Если `curl` пишет, что не может подключиться к `localhost:8000`, значит backend не запущен или упал при старте. Смотри ошибки в терминале, где запущен `uvicorn`; `docker compose logs` в этом проекте покажет только PostgreSQL.

Если frontend пишет `connect ECONNREFUSED ::1:8000`, это IPv6-вариант той же проблемы: Vite/Node попытался сходить на IPv6 `localhost`. В `frontend/vite.config.ts` proxy должен смотреть на `http://127.0.0.1:8000`.

### `GEMINI_API_KEY is not set`

В `.env` либо добавь ключ Gemini, либо временно поставь:

```env
RAG_LLM_PROVIDER=none
```

Тогда LLM-ответы в чате будут отключены, но остальная часть проекта сможет запускаться.

### Первый reindex работает долго

Это нормально: `sentence-transformers` скачивает модель и считает эмбеддинги локально.

### AUCA-документы не находятся

Проверь, что:

- сид каталога был запущен;
- `university_id` действительно принадлежит AUCA;
- путь `docs/web/university_2/2026` существует;
- после импорта документов был запущен `scripts/reindex_all_documents.py`.
