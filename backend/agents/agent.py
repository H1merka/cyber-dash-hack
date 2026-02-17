"""

Модуль, реализующий автономную сущность с памятью, эмоциями,
отношениями и планировщиком действий

Агент объединяет все компоненты:
- Memory – долговременная память (ChromaDB)
- Emotions – эмоциональное состояние
- Relationships – матрица отношений с другими агентами
- Planner – планировщик действий на основе LLM

Агент может воспринимать события (perceive) и принимать решения (act)

"""
from .memory import Memory
from .emotions import Emotions
from .planner import Planner
from .relationships import Relationships


class Agent:
    def __init__(self, agent_id, name, personality, initial_mood=0):
        self.id = agent_id
        self.name = name
        self.personality = personality
        self.memory = Memory(agent_id)
        self.emotions = Emotions(initial_mood)
        self.relationships = Relationships(agent_id)
        self.planner = Planner(name, personality)
        self.current_goal = None  


    async def perceive(self, event_text, event_delta=0, other_agent_id=None):
        """
        Воспринимает событие сохраняет в память, меняет настроение, обновляет отношения
        """
        await self.memory.add_memory(event_text)
        self.emotions.update(event_delta)

        if other_agent_id is not None:
            self.relationships.update_affinity(other_agent_id, event_delta)


    async def act(self, other_agents_names):
        """
        Принимает решение и возвращает действиее
        """
        recent = self.memory.get_recent(3)
        recent_text = " ".join(recent) if recent else "нет недавних событий"
        mood_label = self.emotions.get_mood_label()

        
        rel_parts = []
        for other_name in other_agents_names:
            affinity = 0
            rel_parts.append(f"{other_name}: {affinity}")
        relations_str = ", ".join(rel_parts)

        action = await self.planner.decide_action(
            mood_label=mood_label,
            recent_memories=recent_text,
            other_agents_names=other_agents_names,
            relations=relations_str
        )
        # Сохраняем текущий план 
        if action.get("type") == "message":
            self.current_goal = action.get("content", "")[:50]
        else:
            self.current_goal = "Размышляет..."
        return action