"""
Генератор профиля нового агента на основе пользовательского ввода.
Использует LLM для создания характера и начальных воспоминаний.
"""

from backend.llm.client import LLMClient
from backend.llm.prompts import PROFILE_GEN_SYSTEM, PROFILE_GEN_TEMPLATE
import json

# Словарь для преобразования выбора пользователя в промпт
INITIAL_MEMORY_TEMPLATES = {
    "местный житель": "Я родился и вырос в этом мире, знаю каждый уголок.",
    "странник извне": "Я пришёл из другого мира, всё здесь кажется чужим и удивительным.",
    "путешественник во времени": "Я помню события, которые ещё не произошли, и забываю то, что уже было."
}

async def generate_agent_profile(user_input: dict) -> dict:
    """
    Генерирует профиль нового агента.
    user_input содержит:
        - name: имя (строка)
        - mbti: тип личности (например, "INFP")
        - backstory: предыстория (текст)
        - initial_memory_choice: одно из ["местный житель", "странник извне", "путешественник во времени"]
    Возвращает словарь с полями:
        - name: имя (то же, что ввели)
        - personality: сгенерированный характер (строка)
        - backstory: предыстория (можно оставить как есть или дополнить)
        - initial_memories: список строк (первое — из шаблона + сгенерированные)
    """
    name = user_input.get("name", "Незнакомец")
    mbti = user_input.get("mbti", "")
    backstory = user_input.get("backstory", "")
    init_choice = user_input.get("initial_memory_choice", "местный житель")

    # Базовое воспоминание из шаблона
    base_memory = INITIAL_MEMORY_TEMPLATES.get(init_choice, INITIAL_MEMORY_TEMPLATES["местный житель"])

    prompt = PROFILE_GEN_TEMPLATE.format(
        name=name,
        mbti=mbti,
        backstory=backstory,
        base_memory=base_memory,
    )
    llm = LLMClient()
    response = await llm.generate(prompt, system_prompt=PROFILE_GEN_SYSTEM)
    
    try:
        start = response.find('{')
        end = response.rfind('}') + 1
        if start != -1 and end != 0:
            profile = json.loads(response[start:end])
            # Добавляем имя и предысторию (они уже есть)
            profile["name"] = name
            profile["backstory"] = backstory
            return profile
    except:
        pass

    # Заглушка на случай ошибки
    return {
        "name": name,
        "personality": f"Обладатель типа {mbti} с загадочной душой.",
        "backstory": backstory,
        "initial_memories": [base_memory, "Первые шаги в этом мире были неуверенными."]
    }
