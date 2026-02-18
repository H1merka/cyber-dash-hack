"""
Абстрактный LLM-клиент с поддержкой retry / backoff / логирования.
Провайдер: DeepSeek-совместимый API (OpenAI-формат).
Конфигурация берётся из backend.config.settings.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)

# Настройки retry
_MAX_RETRIES = 3
_BACKOFF_BASE = 2.0  # секунды
_TIMEOUT = 45.0  # секунды на запрос


class LLMClient:
    """Асинхронный клиент для LLM API (OpenAI-compatible)."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key or settings.llm_api_key
        if not self.api_key:
            raise ValueError("LLM_API_KEY не задан в .env")
        self.base_url = (base_url or settings.llm_base_url).rstrip("/")
        self.model = model or settings.llm_model

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Отправить запрос к LLM и вернуть текст ответа.
        Автоматически повторяет при сбоях (до _MAX_RETRIES раз).
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }

        last_error: Exception | None = None

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                    )

                if response.status_code == 429:
                    # Rate limit — ждём дольше
                    wait = _BACKOFF_BASE * attempt * 2
                    logger.warning(
                        "LLM rate limit (429), попытка %d/%d, ждём %.1fs",
                        attempt, _MAX_RETRIES, wait,
                    )
                    await asyncio.sleep(wait)
                    continue

                if response.status_code >= 500:
                    wait = _BACKOFF_BASE * attempt
                    logger.warning(
                        "LLM серверная ошибка (%d), попытка %d/%d, ждём %.1fs",
                        response.status_code, attempt, _MAX_RETRIES, wait,
                    )
                    await asyncio.sleep(wait)
                    continue

                if response.status_code != 200:
                    error_text = response.text[:300]
                    raise RuntimeError(
                        f"LLM API ошибка (статус {response.status_code}): {error_text}"
                    )

                data = response.json()
                if "error" in data:
                    raise RuntimeError(f"LLM API error: {data['error']}")

                content = data["choices"][0]["message"]["content"]
                logger.debug(
                    "LLM ответ получен (модель=%s, длина=%d)", self.model, len(content)
                )
                return content

            except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout) as exc:
                last_error = exc
                wait = _BACKOFF_BASE * attempt
                logger.warning(
                    "LLM сетевая ошибка: %s, попытка %d/%d, ждём %.1fs",
                    exc, attempt, _MAX_RETRIES, wait,
                )
                await asyncio.sleep(wait)

        raise RuntimeError(
            f"LLM: все {_MAX_RETRIES} попытки исчерпаны. Последняя ошибка: {last_error}"
        )


