"""
WebSocket-менеджер для стрима событий в реальном времени.
Клиенты подключаются к /ws и получают JSON-сообщения:
  {"type": "event",        "data": {...}}
  {"type": "mood_update",  "data": {"agent_id": 1, "mood": "...", "mood_value": 20}}
  {"type": "relation_update", "data": {...}}
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Управляет активными WebSocket-подключениями и рассылает обновления."""

    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.append(ws)
        logger.info("WS клиент подключён (%d всего)", len(self._connections))

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self._connections:
            self._connections.remove(ws)
        logger.info("WS клиент отключён (%d осталось)", len(self._connections))

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Отправить JSON-сообщение всем подключённым клиентам."""
        payload = json.dumps(message, ensure_ascii=False)
        dead: list[WebSocket] = []
        for ws in self._connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    @property
    def active_count(self) -> int:
        return len(self._connections)


# Глобальный экземпляр
manager = ConnectionManager()


async def websocket_endpoint(ws: WebSocket) -> None:
    """Обработчик WS-подключения: держим соединение открытым."""
    await manager.connect(ws)
    try:
        while True:
            # Ожидаем любое сообщение от клиента (ping / keep-alive)
            data = await ws.receive_text()
            # Можно обрабатывать входящие команды от клиента, пока просто игнорируем
            logger.debug("WS получено от клиента: %s", data[:100])
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)
