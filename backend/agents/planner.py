"""
Планировщик действий агента
Принимает решение, какое действие совершить, на основе личности, настроения, воспоминаний и отношений
Использует LLM для генерации действия в формате JSON
"""

from backend.llm.client import LLMClient
from backend.llm.prompts import agent_system_prompt, ACTION_PROMPT_TEMPLATE



class Planner:
    def __init__(self, agent_name, personality):
        self.agent_name = agent_name
        self.personality = personality
        self.llm = LLMClient()

    def _get_system_prompt(self, mood_label):
        """
        Делает системный промт от настроения, используя шаблоны из prompts.py
        """
        return agent_system_prompt(self.agent_name, self.personality, mood_label)



    async def decide_action(self, mood_label, recent_memories, other_agents_names, relations):
        """
        Возвращает действие в виде словаря:
        {"type": "message", "target": "Алиса", "content": "Привет!"}

        """
        system_prompt = self._get_system_prompt(mood_label)

        prompt = ACTION_PROMPT_TEMPLATE.format(
            recent_memories=recent_memories,
            relations=relations,
            other_agents=", ".join(other_agents_names),
        )
        response = await self.llm.generate(prompt, system_prompt=system_prompt)

        # извлечь JSON из ответа
        import json
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = response[start:end]
                action = json.loads(json_str)
                return action
        except:
            pass

        # если не получилось, возвращаем действие по умолчанию
        if other_agents_names:
            target = other_agents_names[0]
        else:
            target = "никому"
        return {
            "type": "message",
            "target": target,
            "content": f"Привет, я {self.agent_name}. У меня {mood_label} настроение. Отношения: {relations}"
        }

