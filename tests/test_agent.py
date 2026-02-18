"""
Тесты класса Agent и модуля Relationships.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from backend.agents.emotions import Emotions
from backend.agents.relationships import Relationships


# ══════════════════════════════════════════════════════════════════════
#  Relationships
# ══════════════════════════════════════════════════════════════════════

class TestRelationships:
    def test_default_affinity(self):
        rel = Relationships(agent_id=1)
        assert rel.get_affinity(2) == 0

    def test_update_affinity_positive(self):
        rel = Relationships(agent_id=1)
        new = rel.update_affinity(2, 25)
        assert new == 25
        assert rel.get_affinity(2) == 25

    def test_update_affinity_negative(self):
        rel = Relationships(agent_id=1)
        rel.update_affinity(2, -30)
        assert rel.get_affinity(2) == -30

    def test_clamp_upper(self):
        rel = Relationships(agent_id=1)
        rel.update_affinity(2, 80)
        new = rel.update_affinity(2, 50)
        assert new == 100

    def test_clamp_lower(self):
        rel = Relationships(agent_id=1)
        rel.update_affinity(2, -80)
        new = rel.update_affinity(2, -50)
        assert new == -100

    def test_get_all_affinities_returns_copy(self):
        rel = Relationships(agent_id=1)
        rel.update_affinity(2, 10)
        rel.update_affinity(3, -5)
        all_aff = rel.get_all_affinities()
        assert all_aff == {2: 10, 3: -5}
        # Мутация копии не меняет оригинал
        all_aff[4] = 99
        assert 4 not in rel.affinities

    def test_multiple_agents(self):
        rel = Relationships(agent_id=1)
        rel.update_affinity(2, 50)
        rel.update_affinity(3, -20)
        rel.update_affinity(2, 10)
        assert rel.get_affinity(2) == 60
        assert rel.get_affinity(3) == -20


# ══════════════════════════════════════════════════════════════════════
#  Agent — perceive / act
# ══════════════════════════════════════════════════════════════════════

class TestAgentPerceive:
    """Тесты Agent.perceive — проверяем, что обновляются память, эмоции, отношения."""

    @pytest.fixture
    def agent(self):
        """Создать агента с замоканной памятью (избегаем инициализации ChromaDB)."""
        with patch("backend.agents.agent.Memory") as MockMemory:
            mock_mem = MagicMock()
            mock_mem.add_memory = AsyncMock()
            mock_mem.get_recent = MagicMock(return_value=[])
            MockMemory.return_value = mock_mem

            from backend.agents.agent import Agent
            a = Agent(agent_id=1, name="Тест", personality="тестовая личность")
            yield a

    @pytest.mark.asyncio
    async def test_perceive_updates_mood(self, agent):
        await agent.perceive("получил подарок", event_delta=20)
        assert agent.emotions.get_mood_value() == 20

    @pytest.mark.asyncio
    async def test_perceive_updates_relationship(self, agent):
        await agent.perceive("Роки помог", event_delta=15, other_agent_id=2)
        assert agent.relationships.get_affinity(2) == 15

    @pytest.mark.asyncio
    async def test_perceive_calls_memory_add(self, agent):
        await agent.perceive("что-то произошло", event_delta=0)
        agent.memory.add_memory.assert_awaited_once_with("что-то произошло")


class TestAgentAct:
    """Тесты Agent.act — проверяем, что action корректно формируется."""

    @pytest.fixture
    def agent(self):
        with patch("backend.agents.agent.Memory") as MockMemory, \
             patch("backend.agents.agent.Planner") as MockPlanner:
            mock_mem = MagicMock()
            mock_mem.add_memory = AsyncMock()
            mock_mem.get_recent = MagicMock(return_value=["гулял по лесу"])
            MockMemory.return_value = mock_mem

            mock_planner = MagicMock()
            mock_planner.decide_action = AsyncMock(return_value={
                "type": "message",
                "target": "Фыр",
                "content": "Привет, сосед!"
            })
            MockPlanner.return_value = mock_planner

            from backend.agents.agent import Agent
            a = Agent(agent_id=1, name="Мо", personality="дружелюбная панда")
            yield a

    @pytest.mark.asyncio
    async def test_act_returns_action(self, agent):
        action = await agent.act(["Фыр", "Роки"])
        assert action["type"] == "message"
        assert action["target"] == "Фыр"

    @pytest.mark.asyncio
    async def test_act_sets_current_goal(self, agent):
        await agent.act(["Фыр"])
        assert agent.current_goal is not None
        assert len(agent.current_goal) <= 50
