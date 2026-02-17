import asyncio
from llm.client import LLMClient


async def main():
    client = LLMClient()
    response = await client.generate(
        prompt="Привет! Как тебя зовут?",
        system_prompt="Ты друже помощник."
    )
    print("Ответ от DeepSeek:", response)
    
import os
print("ключик .ENV:", os.getenv("LLM_API_KEY"))  

if __name__ == "__main__":
    asyncio.run(main())

#  python backend/test_deepseek.py