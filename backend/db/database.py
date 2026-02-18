"""
Асинхронное подключение к SQLite через SQLAlchemy + aiosqlite.
- Создание таблиц
- Фабрика сессий
- Начальные данные (seed)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import event, select, func
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.config import settings
from backend.db.models import (
    AgentModel,
    Base,
    EventModel,
    GoalModel,
    MemoryModel,
    RelationshipModel,
)

logger = logging.getLogger(__name__)

# ─── Engine & Session ────────────────────────────────────────────────

engine = create_async_engine(
    settings.db_url,
    echo=False,
    connect_args={"check_same_thread": False},
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Включаем foreign keys для SQLite (обязательно для каждого соединения)
@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# ─── Инициализация БД ───────────────────────────────────────────────

async def init_db() -> None:
    """Создать таблицы и заполнить начальными данными, если БД пуста."""
    # Убедиться, что каталог для файла БД существует
    db_file = Path(settings.db_url.replace("sqlite+aiosqlite:///", ""))
    db_file.parent.mkdir(parents=True, exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Проверяем, есть ли уже данные
    async with async_session() as session:
        count = (await session.execute(select(func.count(AgentModel.id)))).scalar() or 0
        if count == 0:
            await _seed_data(session)
            logger.info("База данных заполнена начальными данными (seed)")


# ─── Seed-данные ─────────────────────────────────────────────────────

async def _seed_data(session: AsyncSession) -> None:
    """Вставить начальных персонажей, отношения, воспоминания, цели и первое событие."""

    # --- Агенты ---
    agents_raw = [
        {
            "name": "Мо",
            "mood": "счастлив",
            "personality_type": "ISFP",
            "personality_title": "мечтатель",
            "description": "Панда Мо любит тишину и ручьи.",
            "background": "Живёт у ручья, любит ягоды",
            "avatar_emoji": "🐼",
            "mood_value": 60,
        },
        {
            "name": "Роки",
            "mood": "грустный",
            "personality_type": "ENTP",
            "personality_title": "изобретатель",
            "description": "Лис Роки придумывает рискованные идеи.",
            "background": "Всегда ищет приключения",
            "avatar_emoji": "🦊",
            "mood_value": -30,
        },
        {
            "name": "Фыр",
            "mood": "злой",
            "personality_type": "ISTJ",
            "personality_title": "хранитель",
            "description": "Ежик Фыр защищает свои границы.",
            "background": "Живёт в норе под дубом",
            "avatar_emoji": "🦔",
            "mood_value": -50,
        },
        {
            "name": "Лея",
            "mood": "нейтральный",
            "personality_type": "INTJ",
            "personality_title": "стратег",
            "description": "Змея Лея анализирует каждую ситуацию.",
            "background": "Обитает в пещере",
            "avatar_emoji": "🐍",
            "mood_value": 0,
        },
        {
            "name": "Феликс",
            "mood": "напуган",
            "personality_type": "INFJ",
            "personality_title": "мистик",
            "description": "Кот Феликс чувствителен к изменениям.",
            "background": "Прячется в кустах",
            "avatar_emoji": "🐱",
            "mood_value": -40,
        },
    ]

    agent_objects: dict[str, AgentModel] = {}
    for data in agents_raw:
        agent = AgentModel(**data)
        session.add(agent)
        agent_objects[data["name"]] = agent

    await session.flush()  # получить id

    # --- Отношения ---
    rels_raw = [
        ("Мо", "Роки", "друзья", 72),
        ("Роки", "Мо", "друзья", 68),
        ("Роки", "Фыр", "напряжение", 74),
        ("Мо", "Фыр", "забота", 63),
        ("Феликс", "Лея", "уважение", 56),
        ("Лея", "Роки", "нейтральные", 48),
    ]
    for from_name, to_name, rtype, strength in rels_raw:
        session.add(
            RelationshipModel(
                agent_from_id=agent_objects[from_name].id,
                agent_to_id=agent_objects[to_name].id,
                relation_type=rtype,
                strength=strength,
            )
        )

    # --- Воспоминания для Мо ---
    mo = agent_objects["Мо"]
    memories_raw = [
        (
            "Обнаружил скрытую поляну со старыми цветущими сакурами, "
            "их лепестки танцевали в лунном свете.",
            datetime.now() - timedelta(hours=5),
            True,
        ),
        (
            "Вместе с Феликсом нашли светящийся камень под старым дубом. "
            "Договорились никому не рассказывать.",
            datetime.now() - timedelta(days=60),
            True,
        ),
        (
            "Нашёл потерявшегося малыша-оленёнка и согревал его всю ночь, "
            "пока не пришла его мама. На следующий день она принесла мне ягоды.",
            datetime.now() - timedelta(days=365),
            True,
        ),
    ]
    for content, ts, is_key in memories_raw:
        session.add(
            MemoryModel(agent_id=mo.id, content=content, timestamp=ts, is_key=is_key)
        )

    # --- Цели для Мо ---
    goals_raw = [
        "Посетить ручей: вернуться к ручью, чтобы проверить, поёт ли вода днём.",
        "Дождаться заката на скале Эха и послушать, как ветер свистит.",
        "Найти место, где видно созвездие Большой Медведицы, и просто смотреть вверх.",
    ]
    for goal_text in goals_raw:
        session.add(GoalModel(agent_id=mo.id, goal=goal_text, status="active"))

    # --- Начальное событие ---
    session.add(
        EventModel(
            content="Панда Мо медленно прогуливается у ручья.",
            actor_id=mo.id,
            mood_after="счастлив",
            relation_type="нейтральные",
            relation_delta=0,
        )
    )

    await session.commit()
