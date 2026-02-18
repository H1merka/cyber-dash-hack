"""
Обмен сообщениями между агентами.
Доставляет сообщение от одного агента к другому,
обновляет память, настроение и отношения обоих участников.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select

from backend.db.database import async_session
from backend.db.models import AgentModel, MessageModel
from backend.simulation.events import record_event

logger = logging.getLogger(__name__)


async def deliver_message(
    from_agent_id: int,
    to_agent_id: int,
    content: str,
    relation_delta: int = 0,
) -> dict[str, Any]:
    """
    Записать сообщение в таблицу messages и создать событие.
    Возвращает данные события.
    """
    async with async_session() as session:
        # Сохранить сообщение
        msg = MessageModel(
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            content=content,
        )
        session.add(msg)
        await session.commit()

        # Имена для красивого события
        from_agent = await session.get(AgentModel, from_agent_id)
        to_agent = await session.get(AgentModel, to_agent_id)
        from_name = from_agent.name if from_agent else "?"
        to_name = to_agent.name if to_agent else "?"

    # Создать событие
    event_content = f"{from_name} → {to_name}: {content}"
    event_data = await record_event(
        content=event_content,
        actor_id=from_agent_id,
        target_id=to_agent_id,
        relation_delta=relation_delta,
    )
    logger.info("Сообщение %s → %s: %s", from_name, to_name, content[:60])
    return event_data
