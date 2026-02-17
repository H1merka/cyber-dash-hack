from llm.client import LLMClient

class Planner:
    def __init__(self, agent_name, personality):
        self.agent_name = agent_name
        self.personality = personality
        self.llm = LLMClient()

    async def decide_action(self, mood_label, recent_memories, other_agents_names, relations):
        """
        relations: строка с описанием отношений, например "Алиса: 50, Боб: -30"
        """
        prompt = f"""Ты {self.agent_name}. Твой характер: {self.personality}.
Твоё настроение: {mood_label}.
Последние воспоминания: {recent_memories}
Твои отношения с другими: {relations}
Другие агенты: {', '.join(other_agents_names)}

Какое действие ты совершишь? Если хочешь поговорить, напиши сообщение. 
Ответ дай в виде JSON с полями "type" (сейчас только "message"), "target" (имя агента) и "content" (текст сообщения).
Пример: {{"type": "message", "target": "Алиса", "content": "Привет, как дела?"}}
"""
        response = await self.llm.generate(prompt, system_prompt="Ты агент в симуляции.")
        
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
        
        # Действие по умолчанию
        if other_agents_names:
            target = other_agents_names[0]
        else:
            target = "никому"
        return {
            "type": "message",
            "target": target,
            "content": f"Привет, я {self.agent_name}. У меня {mood_label} настроение. Отношения: {relations}"
        }