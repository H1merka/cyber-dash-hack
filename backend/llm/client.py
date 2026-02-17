import os
from dotenv import load_dotenv

load_dotenv()  # загружаем переменные окружения (ключ пока не нужен)

class LLMClient:
    def __init__(self):
        # Мы пока не используем реальный ключ, просто сохраняем его для будущего
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "заглушка")
        self.model = "deepseek-chat"  # для совместимости

    async def generate(self, prompt, system_prompt=None, temperature=0.7):
        """
        Заглушка: возвращает тестовый ответ, не обращаясь к реальному API.
        """
        # Здесь можно имитировать разные ответы в зависимости от промпта
        return f"[ТЕСТ] Это заглушка. Ты спросил: {prompt[:50]}... А я бы ответил, но пока учусь."