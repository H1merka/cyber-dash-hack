import os
import httpx
from dotenv import load_dotenv

load_dotenv()

class LLMClient:

    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        if not self.api_key:
            raise ValueError("LLM_API_KEY не найден в .env файле")
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
        self.model = os.getenv("LLM_MODEL", "deepseek-chat")


    async def generate(self, prompt, system_prompt=None, temperature=0.7):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature
                }
            )
            
            
            # Проверяем статус ответа
            if response.status_code != 200:
                error_text = response.text
                raise Exception(f"Ошибка API (статус {response.status_code}): {error_text[:200]}")
            
            try:
                data = response.json()
            except Exception as e:
                raise Exception(f"Не удалось распарсить JSON ответ: {e}, текст ответа: {response.text[:200]}")
            
            if "error" in data:
                raise Exception(f"Ошибка DeepSeek API: {data['error']}")
            
            return data["choices"][0]["message"]["content"]

