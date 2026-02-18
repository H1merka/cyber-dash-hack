"""
Настройки приложения.
Загружает переменные из .env через pydantic-settings.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


# Путь к корню проекта (cyber-dash-hack/)
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Конфигурация приложения, загружается из .env в корне проекта."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM ---
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"

    # --- Database ---
    db_path: str = "./data/world.db"

    # --- ChromaDB ---
    chroma_persist_dir: str = "./data/chroma"

    # --- Simulation ---
    simulation_tick_seconds: int = 10

    @property
    def db_url(self) -> str:
        """Абсолютный async URL для SQLAlchemy (aiosqlite)."""
        db_abs = (BASE_DIR / self.db_path).resolve()
        return f"sqlite+aiosqlite:///{db_abs}"

    @property
    def chroma_abs_dir(self) -> str:
        """Абсолютный путь к директории ChromaDB."""
        return str((BASE_DIR / self.chroma_persist_dir).resolve())


# Глобальный синглтон настроек
settings = Settings()
