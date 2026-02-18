"""
Мировой цикл симуляции «Виртуального мира».
Каждый тик все агенты последовательно выполняют:
  рефлексия → постановка цели → действие → обновление памяти/настроения.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from sqlalchemy import select

from backend.agents.agent import Agent
from backend.config import settings
from backend.db.database import async_session
from backend.db.models import AgentModel
from backend.simulation.events import record_event
from backend.simulation.messaging import deliver_message
from backend.api.websocket import manager

logger = logging.getLogger(__name__)

# Состояние симуляции
_running = False
_speed_multiplier: float = 1.0
_agents_runtime: dict[int, Agent] = {}


def set_speed(multiplier: float) -> None:
    """Установить множитель скорости (0.5 … 5.0)."""
    global _speed_multiplier
    _speed_multiplier = max(0.5, min(5.0, multiplier))
    logger.info("Скорость симуляции: %.1fx", _speed_multiplier)


def get_speed() -> float:
    return _speed_multiplier


def is_running() -> bool:
    return _running


async def _load_agents() -> dict[int, Agent]:
    """Загрузить агентов из БД и создать runtime-объекты."""
    agents: dict[int, Agent] = {}
    async with async_session() as session:
        result = await session.execute(select(AgentModel).order_by(AgentModel.id))
        for row in result.scalars().all():
            agent = Agent(
                agent_id=row.id,
                name=row.name,
                personality=row.description or row.personality_title,
                initial_mood=row.mood_value,
            )
            agents[row.id] = agent
    logger.info("Загружено %d агентов для симуляции", len(agents))
    return agents


async def _sync_mood_to_db(agent: Agent) -> None:
    """Записать текущее настроение агента обратно в БД."""
    mood_label = agent.emotions.get_mood_label()
    mood_value = agent.emotions.get_mood_value()

    # Преобразуем внутреннюю метку в формат фронтенда
    label_map = {
        "ужасное": "злой",
        "плохое": "грустный",
        "нейтральное": "нейтральный",
        "хорошее": "счастлив",
        "отличное": "счастлив",
    }
    db_mood = label_map.get(mood_label, "нейтральный")

    async with async_session() as session:
        db_agent = await session.get(AgentModel, agent.id)
        if db_agent:
            db_agent.mood = db_mood
            db_agent.mood_value = mood_value
            await session.commit()

    # Уведомить WS-клиентов об обновлении настроения
    await manager.broadcast({
        "type": "mood_update",
        "data": {
            "agent_id": agent.id,
            "mood": db_mood,
            "mood_value": mood_value,
        },
    })


async def inject_event_to_agents(event_text: str, actor_id: int | None = None) -> None:
    """Внедрить пользовательское событие в память всех (или целевых) runtime-агентов."""
    if not _agents_runtime:
        return
    for agent_id, agent in _agents_runtime.items():
        if agent_id != actor_id:
            await agent.perceive(f"[Событие мира] {event_text}", event_delta=2)
    logger.info("Событие внедрено в %d агентов: %s", len(_agents_runtime), event_text[:60])


async def inject_message_to_agent(
    target_id: int, from_name: str, content: str
) -> None:
    """Внедрить сообщение пользователя в конкретного агента."""
    agent = _agents_runtime.get(target_id)
    if agent:
        await agent.perceive(
            f"Пользователь ({from_name}) сказал тебе: {content}",
            event_delta=5,
        )
        logger.info("Сообщение пользователя внедрено в агента %s", agent.name)


async def _tick() -> None:
    """Один тик симуляции: каждый агент по очереди решает, что делать."""
    if not _agents_runtime:
        return

    agent_names = {aid: a.name for aid, a in _agents_runtime.items()}
    # Маппинг имя→id для корректного поиска отношений
    name_to_id = {a.name: aid for aid, a in _agents_runtime.items()}

    for agent_id, agent in _agents_runtime.items():
        try:
            other_names = [n for aid, n in agent_names.items() if aid != agent_id]
            action = await agent.act(other_names, agent_id_map=name_to_id)

            if action.get("type") == "message":
                target_name = action.get("target", "")
                content = action.get("content", "")

                # Найти ID цели
                target_id = None
                for aid, name in agent_names.items():
                    if name == target_name:
                        target_id = aid
                        break

                if target_id:
                    await deliver_message(agent_id, target_id, content)

                    # Получатель воспринимает сообщение
                    target_agent = _agents_runtime.get(target_id)
                    if target_agent:
                        await target_agent.perceive(
                            f"{agent.name} сказал: {content}", event_delta=3, other_agent_id=agent_id
                        )
                else:
                    # Монолог — запишем как событие
                    await record_event(
                        content=f"{agent.name}: {content}",
                        actor_id=agent_id,
                    )
            else:
                await record_event(
                    content=f"{agent.name} размышляет...",
                    actor_id=agent_id,
                )

            # Синхронизировать настроение
            await _sync_mood_to_db(agent)

        except Exception:
            logger.exception("Ошибка на тике агента %s (id=%d)", agent.name, agent_id)


async def start_simulation() -> None:
    """Запустить бесконечный цикл симуляции (вызывается как asyncio.Task)."""
    global _running, _agents_runtime

    _running = True
    _agents_runtime = await _load_agents()
    logger.info("Симуляция запущена (тик каждые %ds)", settings.simulation_tick_seconds)

    try:
        while _running:
            await _tick()
            delay = settings.simulation_tick_seconds / _speed_multiplier
            await asyncio.sleep(delay)
    except asyncio.CancelledError:
        logger.info("Симуляция остановлена (cancelled)")
    finally:
        _running = False


def stop_simulation() -> None:
    """Остановить цикл симуляции."""
    global _running
    _running = False
    logger.info("Симуляция остановлена")
