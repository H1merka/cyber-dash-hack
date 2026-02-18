"""
REST API маршруты для «Виртуального мира».
Эндпоинты:
  GET    /api/agents             — список всех агентов
  GET    /api/agents/{id}        — один агент (с памятью, целями)
  POST   /api/agents             — создать нового агента
  PATCH  /api/agents/{id}/mood   — изменить настроение
  GET    /api/relationships      — все отношения
  GET    /api/events             — лента событий
  POST   /api/events             — создать событие / сообщение
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, update

from backend.db.database import async_session
from backend.db.models import (
    AgentModel,
    EventModel,
    GoalModel,
    MemoryModel,
    RelationshipModel,
)
from backend.simulation.world import inject_event_to_agents, inject_message_to_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# ── Допустимые значения ──────────────────────────────────────────────

VALID_MOODS = {"счастлив", "грустный", "злой", "нейтральный", "напуган"}
VALID_REL_TYPES = {"друзья", "напряжение", "забота", "уважение", "нейтральные"}

MOOD_IMPACT = {
    "счастлив": 10,
    "нейтральный": 0,
    "грустный": -8,
    "злой": -16,
    "напуган": -10,
}


# ── Pydantic-схемы ───────────────────────────────────────────────────

class MoodPatch(BaseModel):
    mood: str


class EventCreate(BaseModel):
    content: str
    actorId: int | None = None
    targetId: int | None = None
    moodAfter: str | None = None
    relationType: str = "нейтральные"
    relationDelta: int = 0


class AgentCreate(BaseModel):
    name: str
    mood: str = "нейтральный"
    personality_type: str = "INFP"
    personality_title: str = ""
    description: str = ""
    background: str = ""
    avatar_emoji: str = "🐾"
    mood_value: int = 0


# ── Хелперы ──────────────────────────────────────────────────────────

def _mood_adjusted_strength(
    base: int, from_mood: str, to_mood: str, rel_type: str
) -> int:
    """Корректировка отображаемой силы связи с учётом настроений."""
    from_impact = MOOD_IMPACT.get(from_mood, 0)
    to_impact = MOOD_IMPACT.get(to_mood, 0)
    avg = round((from_impact + to_impact) / 2)
    direction = -1 if rel_type == "напряжение" else 1
    return max(0, min(100, base + direction * avg))


# ── Эндпоинты: Агенты ───────────────────────────────────────────────

@router.get("/agents")
async def get_agents() -> list[dict[str, Any]]:
    async with async_session() as session:
        result = await session.execute(
            select(AgentModel).order_by(AgentModel.id)
        )
        agents = result.scalars().all()
        return [
            {
                "id": a.id,
                "name": a.name,
                "mood": a.mood,
                "personality_type": a.personality_type,
                "personality_title": a.personality_title,
                "description": a.description,
                "avatar_emoji": a.avatar_emoji,
                "mood_value": a.mood_value,
            }
            for a in agents
        ]


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: int) -> dict[str, Any]:
    async with async_session() as session:
        agent = await session.get(AgentModel, agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Агент не найден")

        # Последние воспоминания
        mem_result = await session.execute(
            select(MemoryModel)
            .where(MemoryModel.agent_id == agent_id)
            .order_by(MemoryModel.timestamp.desc())
            .limit(10)
        )
        memories = [
            {"id": m.id, "content": m.content, "is_key": m.is_key, "timestamp": m.timestamp.isoformat()}
            for m in mem_result.scalars().all()
        ]

        # Активные цели
        goal_result = await session.execute(
            select(GoalModel)
            .where(GoalModel.agent_id == agent_id, GoalModel.status == "active")
            .order_by(GoalModel.created_at.desc())
        )
        goals = [
            {"id": g.id, "goal": g.goal, "status": g.status}
            for g in goal_result.scalars().all()
        ]

        return {
            "id": agent.id,
            "name": agent.name,
            "mood": agent.mood,
            "personality_type": agent.personality_type,
            "personality_title": agent.personality_title,
            "description": agent.description,
            "background": agent.background,
            "avatar_emoji": agent.avatar_emoji,
            "mood_value": agent.mood_value,
            "memories": memories,
            "goals": goals,
        }


@router.post("/agents", status_code=201)
async def create_agent(body: AgentCreate) -> dict[str, Any]:
    async with async_session() as session:
        agent = AgentModel(
            name=body.name,
            mood=body.mood,
            personality_type=body.personality_type,
            personality_title=body.personality_title,
            description=body.description,
            background=body.background,
            avatar_emoji=body.avatar_emoji,
            mood_value=body.mood_value,
        )
        session.add(agent)
        await session.commit()
        await session.refresh(agent)
        logger.info("Создан агент %s (id=%d)", agent.name, agent.id)
        return {
            "id": agent.id,
            "name": agent.name,
            "mood": agent.mood,
            "personality_type": agent.personality_type,
            "personality_title": agent.personality_title,
            "avatar_emoji": agent.avatar_emoji,
        }


@router.patch("/agents/{agent_id}/mood")
async def patch_mood(agent_id: int, body: MoodPatch) -> dict[str, Any]:
    mood = body.mood.lower()
    if mood not in VALID_MOODS:
        raise HTTPException(status_code=400, detail="Некорректное настроение")

    async with async_session() as session:
        agent = await session.get(AgentModel, agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Агент не найден")
        agent.mood = mood
        await session.commit()
        return {"id": agent.id, "name": agent.name, "mood": agent.mood}


# ── Эндпоинты: Отношения ────────────────────────────────────────────

@router.get("/relationships")
async def get_relationships() -> list[dict[str, Any]]:
    async with async_session() as session:
        result = await session.execute(
            select(RelationshipModel).order_by(RelationshipModel.id)
        )
        rels = result.scalars().all()

        # Подгрузить имена и настроения агентов
        agent_result = await session.execute(select(AgentModel))
        agents_map = {a.id: a for a in agent_result.scalars().all()}

        out: list[dict[str, Any]] = []
        for r in rels:
            a_from = agents_map.get(r.agent_from_id)
            a_to = agents_map.get(r.agent_to_id)
            display = _mood_adjusted_strength(
                r.strength,
                a_from.mood if a_from else "нейтральный",
                a_to.mood if a_to else "нейтральный",
                r.relation_type,
            )
            out.append(
                {
                    "id": r.id,
                    "agent_from_id": r.agent_from_id,
                    "agent_to_id": r.agent_to_id,
                    "relation_type": r.relation_type,
                    "strength": r.strength,
                    "display_strength": display,
                    "from_name": a_from.name if a_from else None,
                    "to_name": a_to.name if a_to else None,
                }
            )
        return out


# ── Эндпоинты: События ──────────────────────────────────────────────

@router.get("/events")
async def get_events(limit: int = Query(20, ge=1, le=100)) -> list[dict[str, Any]]:
    async with async_session() as session:
        result = await session.execute(
            select(EventModel).order_by(EventModel.id.desc()).limit(limit)
        )
        events = result.scalars().all()

        agent_result = await session.execute(select(AgentModel))
        agents_map = {a.id: a for a in agent_result.scalars().all()}

        return [
            {
                "id": e.id,
                "content": e.content,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "actor_name": agents_map[e.actor_id].name if e.actor_id and e.actor_id in agents_map else None,
                "target_name": agents_map[e.target_id].name if e.target_id and e.target_id in agents_map else None,
                "mood_after": e.mood_after,
                "relation_type": e.relation_type,
                "relation_delta": e.relation_delta,
            }
            for e in events
        ]


@router.post("/events", status_code=201)
async def create_event(body: EventCreate) -> dict[str, Any]:
    content = body.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Событие не может быть пустым")

    mood_after = body.moodAfter.lower() if body.moodAfter else None
    if mood_after and mood_after not in VALID_MOODS:
        raise HTTPException(status_code=400, detail="Некорректное настроение")

    rel_type = body.relationType.lower() if body.relationType else "нейтральные"
    if rel_type not in VALID_REL_TYPES:
        raise HTTPException(status_code=400, detail="Некорректный тип связи")

    async with async_session() as session:
        event_obj = EventModel(
            content=content,
            actor_id=body.actorId,
            target_id=body.targetId,
            mood_after=mood_after,
            relation_type=rel_type,
            relation_delta=body.relationDelta,
        )
        session.add(event_obj)

        # Обновить настроение актора
        if body.actorId and mood_after:
            actor = await session.get(AgentModel, body.actorId)
            if actor:
                actor.mood = mood_after

        # Обновить силу отношений
        if body.actorId and body.targetId and body.relationDelta != 0:
            rel_result = await session.execute(
                select(RelationshipModel).where(
                    RelationshipModel.agent_from_id == body.actorId,
                    RelationshipModel.agent_to_id == body.targetId,
                )
            )
            rel = rel_result.scalar_one_or_none()
            if rel:
                rel.strength = max(0, min(100, rel.strength + body.relationDelta))
                rel.relation_type = rel_type
            else:
                new_strength = max(0, min(100, 50 + body.relationDelta))
                session.add(
                    RelationshipModel(
                        agent_from_id=body.actorId,
                        agent_to_id=body.targetId,
                        relation_type=rel_type,
                        strength=new_strength,
                    )
                )

        await session.commit()
        await session.refresh(event_obj)

        # Подготовить ответ
        agent_result = await session.execute(select(AgentModel))
        agents_map = {a.id: a for a in agent_result.scalars().all()}

        result_data = {
            "id": event_obj.id,
            "content": event_obj.content,
            "created_at": event_obj.created_at.isoformat() if event_obj.created_at else None,
            "actor_name": agents_map[event_obj.actor_id].name if event_obj.actor_id and event_obj.actor_id in agents_map else None,
            "target_name": agents_map[event_obj.target_id].name if event_obj.target_id and event_obj.target_id in agents_map else None,
            "mood_after": event_obj.mood_after,
            "relation_type": event_obj.relation_type,
            "relation_delta": event_obj.relation_delta,
        }

    # Внедрить событие в runtime-агентов
    await inject_event_to_agents(content, actor_id=body.actorId)

    return result_data


# ── Эндпоинт: Сообщение пользователя агенту ─────────────────────────

class UserMessage(BaseModel):
    content: str


@router.post("/agents/{agent_id}/message", status_code=201)
async def send_user_message(agent_id: int, body: UserMessage) -> dict[str, Any]:
    """Пользователь отправляет сообщение конкретному агенту."""
    content = body.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Сообщение не может быть пустым")

    async with async_session() as session:
        agent = await session.get(AgentModel, agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Агент не найден")

        # Создать событие
        event_obj = EventModel(
            content=f"Пользователь → {agent.name}: {content}",
            actor_id=None,
            target_id=agent_id,
        )
        session.add(event_obj)
        await session.commit()
        await session.refresh(event_obj)

    # Внедрить в runtime-агента
    await inject_message_to_agent(agent_id, "Пользователь", content)

    # Оповестить WS
    from backend.api.websocket import manager
    await manager.broadcast({
        "type": "event",
        "data": {
            "id": event_obj.id,
            "content": event_obj.content,
            "created_at": event_obj.created_at.isoformat() if event_obj.created_at else None,
            "actor_name": "Пользователь",
            "target_name": agent.name,
        },
    })

    return {"ok": True, "agent": agent.name, "content": content}


# ── Эндпоинт: Скорость симуляции ─────────────────────────────────────

class SpeedPatch(BaseModel):
    speed: float


@router.get("/simulation/speed")
async def get_simulation_speed() -> dict[str, Any]:
    from backend.simulation.world import get_speed, is_running
    return {"speed": get_speed(), "running": is_running()}


@router.patch("/simulation/speed")
async def set_simulation_speed(body: SpeedPatch) -> dict[str, Any]:
    from backend.simulation.world import set_speed, get_speed
    set_speed(body.speed)
    return {"speed": get_speed()}


@router.get("/health")
async def health() -> dict[str, Any]:
    from backend.api.websocket import manager
    return {
        "ok": True,
        "service": "virtual-world-backend",
        "ws_clients": manager.active_count,
    }
