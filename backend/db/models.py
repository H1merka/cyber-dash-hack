"""
SQLAlchemy ORM-модели для «Виртуального мира».
Таблицы: agents, relationships, events, memories, goals, messages.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей."""
    pass


class AgentModel(Base):
    """Персонаж виртуального мира."""

    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    mood: Mapped[str] = mapped_column(String(32), nullable=False, default="нейтральный")
    personality_type: Mapped[str] = mapped_column(String(8), nullable=False, default="INFP")
    personality_title: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    background: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_emoji: Mapped[str] = mapped_column(String(8), nullable=False, default="🐾")
    mood_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Связи
    relationships_from: Mapped[list[RelationshipModel]] = relationship(
        "RelationshipModel",
        foreign_keys="RelationshipModel.agent_from_id",
        back_populates="agent_from",
        cascade="all, delete-orphan",
    )
    relationships_to: Mapped[list[RelationshipModel]] = relationship(
        "RelationshipModel",
        foreign_keys="RelationshipModel.agent_to_id",
        back_populates="agent_to",
        cascade="all, delete-orphan",
    )
    memories: Mapped[list[MemoryModel]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )
    goals: Mapped[list[GoalModel]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Agent id={self.id} name={self.name!r} mood={self.mood!r}>"


class RelationshipModel(Base):
    """Направленное отношение agent_from → agent_to."""

    __tablename__ = "relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_from_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    agent_to_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    relation_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="нейтральные"
    )
    strength: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    agent_from: Mapped[AgentModel] = relationship(
        "AgentModel", foreign_keys=[agent_from_id], back_populates="relationships_from"
    )
    agent_to: Mapped[AgentModel] = relationship(
        "AgentModel", foreign_keys=[agent_to_id], back_populates="relationships_to"
    )

    def __repr__(self) -> str:
        return (
            f"<Relationship {self.agent_from_id}→{self.agent_to_id} "
            f"type={self.relation_type!r} str={self.strength}>"
        )


class EventModel(Base):
    """Событие в мире (сообщение, действие, изменение настроения и т.д.)."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    actor_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    target_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    mood_after: Mapped[str | None] = mapped_column(String(32), nullable=True)
    relation_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    relation_delta: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    actor: Mapped[AgentModel | None] = relationship(
        "AgentModel", foreign_keys=[actor_id]
    )
    target: Mapped[AgentModel | None] = relationship(
        "AgentModel", foreign_keys=[target_id]
    )

    def __repr__(self) -> str:
        return f"<Event id={self.id} actor={self.actor_id} content={self.content[:30]!r}>"


class MemoryModel(Base):
    """Эпизод из памяти агента (параллельно хранится в ChromaDB для поиска)."""

    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    is_key: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    agent: Mapped[AgentModel] = relationship(back_populates="memories")

    def __repr__(self) -> str:
        return f"<Memory id={self.id} agent={self.agent_id} key={self.is_key}>"


class GoalModel(Base):
    """Цель агента."""

    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="active"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    agent: Mapped[AgentModel] = relationship(back_populates="goals")

    def __repr__(self) -> str:
        return f"<Goal id={self.id} agent={self.agent_id} status={self.status!r}>"


class MessageModel(Base):
    """Сообщение между двумя агентами."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    from_agent_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    to_agent_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    sender: Mapped[AgentModel] = relationship(
        "AgentModel", foreign_keys=[from_agent_id]
    )
    receiver: Mapped[AgentModel] = relationship(
        "AgentModel", foreign_keys=[to_agent_id]
    )

    def __repr__(self) -> str:
        return f"<Message id={self.id} {self.from_agent_id}→{self.to_agent_id}>"
