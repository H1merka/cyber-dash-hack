

"""
AI-интерфейс
Здесь описаны основные функции для работы с агентами.
"""

from agents.agent import Agent
from agents.agent_generator import generate_agent_profile
from typing import List, Dict, Any

# ======================== ОСНОВНЫЕ ФУНКЦИИ ========================

def create_agent(agent_id: int, name: str, personality: str, initial_mood: int = 0) -> Agent:
    """
    Создаёт нового агента.
    """
    return Agent(agent_id, name, personality, initial_mood)


async def generate_agent_from_user_input(user_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Генерирует профиль нового агента на основе пользовательского ввода.
    Вызывается при добавлении агента через интерфейс.
    """
    return await generate_agent_profile(user_input)


async def agent_perceive(agent: Agent, event_text: str, event_delta: int = 0, other_agent_id: int = None):
    """
    Передать событие агенту.
    """
    await agent.perceive(event_text, event_delta, other_agent_id)


async def agent_act(agent: Agent, other_agent_names: List[str]) -> Dict[str, Any]:
    """
    Получить следующее действие агента.
    """
    return await agent.act(other_agent_names)


def get_agent_profile(agent: Agent) -> Dict[str, Any]:
    """
    Получить данные для инспектора агента.
    """
    return {
        "name": agent.name,
        "personality": agent.personality,
        "mood_label": agent.emotions.get_mood_label(),
        "recent_memories": agent.memory.get_recent(5),
        "current_plan": agent.current_goal if agent.current_goal else "Нет плана"
    }


def get_agent_relationships(agent: Agent) -> Dict[int, int]:
    """
    Возвращает словарь отношений агента к другим агентам.
    Ключ: ID другого агента, значение: уровень симпатии (-100..100).
    """

    return agent.relationships.get_all_affinities()
