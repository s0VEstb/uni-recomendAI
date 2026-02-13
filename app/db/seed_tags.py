from __future__ import annotations
import asyncio
from dataclasses import dataclass
from typing import Iterable
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from config import settings
from app.db.models.tag import Tag
from app.db.enums import TagType


@dataclass(frozen=True)
class TagSeed:
    slug: str
    title: str
    type: TagType
    is_active: bool = True


DEFAULT_TAGS: list[TagSeed] = [
    # interests
    TagSeed("programming", "Программирование", TagType.interest),
    TagSeed("design", "Дизайн", TagType.interest),
    TagSeed("business", "Бизнес", TagType.interest),
    TagSeed("medicine", "Медицина", TagType.interest),
    TagSeed("art", "Искусство", TagType.interest),
    TagSeed("sports", "Спорт", TagType.interest),
    TagSeed("literature", "Литература", TagType.interest),
    TagSeed("history", "История", TagType.interest),
    TagSeed("music", "Музыка", TagType.interest),
    TagSeed("travel", "Путешествия", TagType.interest),
    TagSeed("cooking", "Кулинария", TagType.interest),
    TagSeed("gaming", "Игры", TagType.interest),
    TagSeed("photography", "Фотография", TagType.interest),
    TagSeed("writing", "Письмо", TagType.interest),
    TagSeed("psychology", "Психология", TagType.interest),
    TagSeed("finance", "Финансы", TagType.interest),
    TagSeed("languages", "Языки", TagType.interest),

    # strengths
    TagSeed("logic", "Логика", TagType.strength),
    TagSeed("communication", "Коммуникация", TagType.strength),
    TagSeed("creativity", "Креативность", TagType.strength),
    TagSeed("empathy", "Эмпатия", TagType.strength),
    TagSeed("leadership", "Лидерство", TagType.strength),
    TagSeed("organization", "Организованность", TagType.strength),
    TagSeed("adaptability", "Адаптивность", TagType.strength),
    TagSeed("critical_thinking", "Критическое мышление", TagType.strength),
    TagSeed("problem_solving", "Решение проблем", TagType.strength),
    TagSeed("teamwork", "Работа в команде", TagType.strength),

    # subjects
    TagSeed("physics", "Физика", TagType.subject),
    TagSeed("biology", "Биология", TagType.subject),
    TagSeed("chemistry", "Химия", TagType.subject),
    TagSeed("literature_subject", "Литература", TagType.subject),
    TagSeed("history_subject", "История", TagType.subject),
    TagSeed("computer_science", "Информатика", TagType.subject),
    TagSeed("economics", "Экономика", TagType.subject),
    TagSeed("psychology_subject", "Психология", TagType.subject),
    TagSeed("philosophy", "Философия", TagType.subject),
    TagSeed("art_subject", "Искусство", TagType.subject),
    TagSeed("music_subject", "Музыка", TagType.subject),
    TagSeed("foreign_languages", "Иностранные языки", TagType.subject),
    TagSeed("mathematics", "Математика", TagType.subject),
]


def make_engine() -> AsyncEngine:
    return create_async_engine(settings.DATABASE_URL, echo=False, future=True)


async def seed_tags(tags: Iterable[TagSeed]) -> None:
    engine = make_engine()
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    created = 0
    updated = 0

    async with async_session() as session:
        # Считываем существующие slug -> Tag
        existing = await session.execute(select(Tag))
        existing_tags = {t.slug: t for t in existing.scalars().all()}

        for item in tags:
            if item.slug in existing_tags:
                # Мягкое обновление: если поменялся title/type/is_active — обновим
                t = existing_tags[item.slug]
                changed = False

                if t.title != item.title:
                    t.title = item.title
                    changed = True
                if t.type != item.type:
                    t.type = item.type
                    changed = True
                if t.is_active != item.is_active:
                    t.is_active = item.is_active
                    changed = True

                if changed:
                    updated += 1
            else:
                session.add(
                    Tag(
                        slug=item.slug,
                        title=item.title,
                        type=item.type,
                        is_active=item.is_active,
                    )
                )
                created += 1

        await session.commit()

    await engine.dispose()
    print(f"Seed complete: created={created}, updated={updated}, total_input={len(list(tags))}")


async def main() -> None:
    # Важно: DEFAULT_TAGS — список. Передаём как есть
    await seed_tags(DEFAULT_TAGS)


if __name__ == "__main__":
    asyncio.run(main())
