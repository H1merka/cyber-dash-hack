# Класс Agent (личность, настроение, планы)  Здесь будет класс Агента (объединит всё)
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
        self.relationships = Relationships(agent_id)  # новое поле
        self.planner = Planner(name, personality)

    def perceive(self, event_text, event_delta=0, other_agent_id=None):
        """
        Воспринимает событие.
        :param event_text: текст события (например, "Алиса сказала: Привет")
        :param event_delta: изменение настроения (от -50 до 50)
        :param other_agent_id: ID другого агента, если событие связано с ним (для обновления отношений)
        """
        self.memory.add_memory(event_text)
        self.emotions.update(event_delta)

        # Если событие связано с другим агентом, обновляем отношения
        if other_agent_id is not None:
            # Пока delta для отношений равна event_delta, но в будущем можно сделать отдельный анализ
            self.relationships.update_affinity(other_agent_id, event_delta)

    async def act(self, other_agents_names):
        """
        Принимает решение и возвращает действие.
        """
        recent = self.memory.get_recent(3)
        recent_text = " ".join(recent) if recent else "нет недавних событий"
        mood_label = self.emotions.get_mood_label()

        # Добавляем информацию об отношениях в планировщик
        # Преобразуем отношения в читаемый вид для промпта
        rel_text = []
        for other_name in other_agents_names:
            # Найдём ID по имени? Пока передадим просто имена, а в планировщике будем использовать заглушку
            # Для простоты будем считать, что other_agents_names — это список имён, а ID мы не знаем.
            # В реальности нужно передавать ID, но пока для теста можно обойтись именами.
            # Мы доработаем это позже.
            affinity = 0  # заглушка
            rel_text.append(f"{other_name}: {affinity}")
        relations_str = ", ".join(rel_text)

        action = await self.planner.decide_action(
            mood_label=mood_label,
            recent_memories=recent_text,
            other_agents_names=other_agents_names,
            relations=relations_str  # добавили
        )
        return action