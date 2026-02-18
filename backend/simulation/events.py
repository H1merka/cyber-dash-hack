"""
Система событий виртуального мира.
Генерирует события и сохраняет в БД + уведомляет WebSocket-клиентов.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select

from backend.db.database import async_session
from backend.db.models import AgentModel, EventModel, RelationshipModel
from backend.api.websocket import manager

logger = logging.getLogger(__name__)


async def record_event(
    content: str,
    actor_id: int | None = None,
    target_id: int | None = None,
    mood_after: str | None = None,
    relation_type: str | None = None,
    relation_delta: int = 0,
) -> dict[str, Any]:
    """
    Записать событие в БД и разослать через WebSocket.
    Возвращает словарь с данными события.
    """
    async with async_session() as session:
        event_obj = EventModel(
            content=content,
            actor_id=actor_id,
            target_id=target_id,
            mood_after=mood_after,
            relation_type=relation_type,
            relation_delta=relation_delta,
        )
        session.add(event_obj)

        # Обновить настроение актора в БД
        if actor_id and mood_after:
            actor = await session.get(AgentModel, actor_id)
            if actor:
                actor.mood = mood_after

        # Обновить силу отношений в БД
        if actor_id and target_id and relation_delta != 0:
            rel_result = await session.execute(
                select(RelationshipModel).where(
                    RelationshipModel.agent_from_id == actor_id,
                    RelationshipModel.agent_to_id == target_id,
                )
            )
            rel = rel_result.scalar_one_or_none()
            if rel:
                rel.strength = max(0, min(100, rel.strength + relation_delta))
                if relation_type:
                    rel.relation_type = relation_type
            elif relation_type:
                new_strength = max(0, min(100, 50 + relation_delta))
                session.add(
                    RelationshipModel(
                        agent_from_id=actor_id,
                        agent_to_id=target_id,
                        relation_type=relation_type,
                        strength=new_strength,
                    )
                )

        await session.commit()
        await session.refresh(event_obj)

        # Собрать имена для ответа
        agents_map: dict[int, str] = {}
        agent_result = await session.execute(select(AgentModel))
        for a in agent_result.scalars().all():
            agents_map[a.id] = a.name

        event_data = {
            "id": event_obj.id,
            "content": event_obj.content,
            "created_at": event_obj.created_at.isoformat() if event_obj.created_at else None,
            "actor_name": agents_map.get(event_obj.actor_id) if event_obj.actor_id else None,
            "target_name": agents_map.get(event_obj.target_id) if event_obj.target_id else None,
            "mood_after": event_obj.mood_after,
            "relation_type": event_obj.relation_type,
            "relation_delta": event_obj.relation_delta,
        }

    # Уведомить WebSocket-клиентов
    await manager.broadcast({"type": "event", "data": event_data})
    logger.info("Событие #%d: %s", event_obj.id, content[:80])

    return event_data
