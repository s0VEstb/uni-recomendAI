# FastAPI Microservice Template 🚀

Базовый шаблон для создания микросервисов в экосистеме RideTrip.
Включает в себя настроенный Docker, асинхронную работу с БД (SQLAlchemy + AsyncPG), миграции (Alembic) и структурированное логирование (Structlog).

## 📋 Чек-лист при создании нового сервиса

Как только вы создали репозиторий из этого шаблона, выполните следующие шаги:

1.  **Переименование:**
    * В `app/core/config.py` измените `APP_NAME` на имя вашего сервиса.
    * В `pyproject.toml` (или `requirements.txt`) обновите название проекта.
2.  **Очистка:**
    * Удалите папку `.git` и инициализируйте новую (если не использовали кнопку "Use this template").
3.  **Зависимости:**
    * Добавьте специфичные для сервиса библиотеки (например, `fastapi-users` для Auth или `stripe` для платежей).

---

## 🏗 Структура проекта (Куда писать код?)

Мы используем слоистую архитектуру. Код разносится по папкам в зависимости от ответственности:

| Папка | Зачем нужна? | Пример |
| :--- | :--- | :--- |
| **`app/routes`** | **Точки входа (API).** Только обработка HTTP, валидация входных данных и вызов сервисов. Минимум логики. | `POST /users`, `GET /tours/{id}` |
| **`app/schemas`** | **Pydantic модели.** Валидация данных "на вход" и "на выход". | `UserCreate`, `TourResponse` |
| **`app/services`** | **Бизнес-логика.** Основной "мозг" сервиса. Здесь принимаются решения, происходят вычисления. | `calculate_price()`, `register_user()` |
| **`app/crud`** | **Работа с БД.** Только прямые запросы к базе (Create, Read, Update, Delete). Никакой бизнес-логики. | `get_user_by_email()`, `create_order()` |
| **`app/db`** | **Модели данных.** SQLAlchemy модели (таблицы БД). | `class User(Base): ...` |
| **`app/middleware`** | **Middleware.** Перехват запросов (логирование, заголовки, CORS). | `ProcessTimeMiddleware` |
| **`app/utils`** | **Утилиты.** Вспомогательные функции. | Логгер, форматтеры дат и т.д. |

---

## 🚀 Как запустить

### Через Docker (Рекомендуется)
Сервис полностью готов к запуску в контейнере. Переменные окружения должны передаваться извне (docker-compose или k8s).



# 1) Чек-лист “новый проект на FastAPI (шаблон) + Postgres + Alembic”

## A. Клон и окружение

```bash
git clone <REPO_URL>
cd <project>

# создать .env (важно: Makefile может include .env)
printf '%s\n' \
'DB_HOST=localhost' \
'DB_PORT=5433' \
'DB_NAME=uni' \
'DB_USER=app' \
'DB_PASS=app' \
'DEBUG=true' \
'APP_NAME=uni-reco' \
> .env

# venv и зависимости (если в Makefile venv)
make venv
```

> Почему DB_PORT=5433? Потому что на маке часто уже занят 5432 локальным Postgres.

---

## B. Поднять Postgres в Docker (без docker-compose)

```bash
docker run --name uni-pg \
  -e POSTGRES_USER=app \
  -e POSTGRES_PASSWORD=app \
  -e POSTGRES_DB=uni \
  -p 5433:5432 \
  -d postgres:16
```

Проверка:

```bash
docker ps
```

---

## C. Активировать окружение (чтобы не вызывать системный python)

```bash
source venv/bin/activate
```

---

## D. Проверить коннект к БД (убивает 90% проблем)

```bash
python -c "import asyncio, asyncpg
async def main():
  conn = await asyncpg.connect('postgresql://app:app@localhost:5433/uni')
  row = await conn.fetchrow('select current_user, current_database()')
  print(dict(row))
  await conn.close()
asyncio.run(main())"
```

---

## E. Alembic миграции (первый раз)

Если в шаблоне **нет** готовых миграций — создаём “init”:

```bash
alembic revision -m "init"
alembic upgrade head
alembic current
```

---

## F. Запуск сервиса

```bash
make run-dev
```

Открыть:

* `http://127.0.0.1:8000/docs`

---

## G. Типовые фиксы, которые мы делали

### 1) `.env: missing separator`

Причина: make читает `.env` как makefile, там должны быть только строки вида `KEY=VALUE`, без мусора.
Фикс: пересоздать `.env` через `printf` (как выше).

### 2) `make migrate: alembic: No such file or directory`

Причина: Makefile зовёт системный `alembic`, а он в venv.
Фикс: либо запускать `alembic ...` в активированном venv, либо починить Makefile:

Добавить:

```make
ALEMBIC = $(VENV)/bin/alembic
```

И заменить `alembic ...` на `$(ALEMBIC) ...`.

### 3) `role "app" does not exist`

Причина: подключались не к тому Postgres (у тебя локальный висел на 5432).
Фикс: сменить порт контейнера на 5433 и в `.env` тоже.

---
