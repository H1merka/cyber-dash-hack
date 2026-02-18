"""
FastAPI-приложение «Виртуальный мир».
Точка входа: uvicorn backend.main:app --reload
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routes import router as api_router
from backend.api.websocket import websocket_endpoint
from backend.db.database import init_db

# ── Логирование ──────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Выполняется при старте и остановке приложения."""
    logger.info("🚀 Инициализация базы данных...")
    await init_db()
    logger.info("✅ БД готова")

    # Запуск фоновой симуляции
    from backend.simulation.world import start_simulation, stop_simulation

    sim_task = asyncio.create_task(start_simulation())
    logger.info("🌍 Симуляция запущена как фоновая задача")

    yield

    # Shutdown
    stop_simulation()
    sim_task.cancel()
    try:
        await sim_task
    except asyncio.CancelledError:
        pass
    logger.info("🔻 Приложение остановлено")


# ── Приложение ───────────────────────────────────────────────────────

app = FastAPI(
    title="Виртуальный мир — КИБЕР РЫВОК",
    description="Автономные AI-агенты с памятью, эмоциями и отношениями",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — разрешаем фронтенд (Vite dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST API
app.include_router(api_router)

# WebSocket
app.add_api_websocket_route("/ws", websocket_endpoint)


# ── Глобальный обработчик ошибок ─────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Необработанная ошибка: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера"},
    )
