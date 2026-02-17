"""
Планировщик действий агента
Принимает решение, какое действие совершить, на основе личности, настроения, воспоминаний и отношений
Использует LLM для генерации действия в формате JSON
"""

from llm.client import LLMClient



class Planner:
    def __init__(self, agent_name, personality):
        self.agent_name = agent_name
        self.personality = personality
        self.llm = LLMClient()

    def _get_system_prompt(self, mood_label):
        """
        Делает системный промт от настроения
        
        """
        base = f"Ты {self.agent_name}. Твой характер: {self.personality}."

        # ключ - метка настроения, значение - инструкция по стилю речи
        style_instructions = {
            "ужасное": " Ты в ярости, настроение ужасное. Отвечай максимально грубо, используй оскорбления, будь краток и резок.",
            "плохое": " Ты раздражён, настроение плохое. Отвечай недружелюбно, резко, но без откровенных оскорблений.",
            "нейтральное": " Твоё настроение нейтральное. Общайся спокойно, вежливо, нейтрально.",
            "хорошее": " У тебя хорошее настроение. Ты приветлив, доброжелателен, можешь поддерживать разговор.",
            "отличное": " Ты в отличном настроении! Ты энергичен, весел, полон энтузиазма. Используй восклицательные знаки, хвали собеседника, будь многословным."
        }

        # Берём инструкцию для текущего настроения, если нет — нейтральная
        instruction = style_instructions.get(mood_label, " Общайся нейтрально.")
        return base + instruction



    async def decide_action(self, mood_label, recent_memories, other_agents_names, relations):
        """
        Возвращает действие в виде словаря:
        {"type": "message", "target": "Алиса", "content": "Привет!"}

        """
        system_prompt = self._get_system_prompt(mood_label)

        prompt = f"""Последние воспоминания: {recent_memories}
Твои отношения с другими: {relations}
Другие агенты: {', '.join(other_agents_names)}

Какое действие ты совершишь? Если хочешь поговорить, напиши сообщение. 
Ответ дай в виде JSON с полями "type" (сейчас только "message"), "target" (имя агента) и "content" (текст сообщения).
Пример: {{"type": "message", "target": "Алиса", "content": "Привет, как дела?"}}
"""
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