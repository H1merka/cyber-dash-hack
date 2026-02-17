"""
Модуль для хранения и обновления отношений между агентами.
Отношения представляют собой число от -100 (ненависть) до 100 (любовь).
"""

class Relationships:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        # Словарь: {other_agent_id: affinity_value}
        self.affinities = {}

    def get_affinity(self, other_agent_id):
        """Вернуть текущее значение симпатии к другому агенту (по умолчанию 0)"""
        return self.affinities.get(other_agent_id, 0)

    def update_affinity(self, other_agent_id, delta):
        """
        Изменить отношение к другому агенту на delta (может быть отрицательным).
        Значение ограничивается диапазоном -100..100.
        """
        current = self.get_affinity(other_agent_id)
        new_value = current + delta
        # Ограничиваем
        if new_value > 100:
            new_value = 100
        elif new_value < -100:
            new_value = -100
        self.affinities[other_agent_id] = new_value
        return new_value

    def get_all_affinities(self):
        """Вернуть словарь всех отношений (для графа)"""
        return self.affinities.copy()

    def __repr__(self):
        return f"Relationships(agent={self.agent_id}, affinities={self.affinities})"