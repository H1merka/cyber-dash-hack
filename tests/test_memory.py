"""
Тесты модуля Memory — эпизодическая память агента (ChromaDB).
Используем мок ChromaDB, чтобы не зависеть от внешнего хранилища.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.fixture
def mock_chroma():
    """Подменить ChromaDB.Client, чтобы тесты не трогали диск."""
    with patch("backend.agents.memory.chromadb") as mock_module:
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0
        mock_collection.add = MagicMock()
        mock_collection.query = MagicMock(return_value={
            "documents": [["гулял по лесу", "нашёл грибы"]],
            "metadatas": [[{}, {}]],
            "ids": [["id1", "id2"]],
            "distances": [[0.1, 0.3]],
        })
        mock_collection.get = MagicMock(return_value={
            "documents": [],
            "metadatas": [],
            "ids": [],
        })
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_module.Client.return_value = mock_client

        yield mock_collection


@pytest.fixture
def memory(mock_chroma):
    from backend.agents.memory import Memory
    return Memory(agent_id=42, persist_directory="./test_data/chroma")


class TestMemoryInit:
    def test_collection_created(self, mock_chroma, memory):
        # get_or_create_collection вызывается при инициализации
        assert memory.collection is mock_chroma

    def test_count_initialized(self, memory):
        assert memory._count == 0


class TestMemoryAdd:
    @pytest.mark.asyncio
    async def test_add_memory_calls_collection_add(self, memory, mock_chroma):
        await memory.add_memory("Встретил Роки у реки")
        mock_chroma.add.assert_called_once()
        call_kwargs = mock_chroma.add.call_args
        assert call_kwargs[1]["documents"] == ["Встретил Роки у реки"]

    @pytest.mark.asyncio
    async def test_add_memory_increments_count(self, memory):
        await memory.add_memory("событие 1")
        assert memory._count == 1
        await memory.add_memory("событие 2")
        assert memory._count == 2


class TestMemorySearch:
    def test_search_similar_returns_documents(self, memory, mock_chroma):
        results = memory.search_similar("лес", n_results=2)
        mock_chroma.query.assert_called_once()
        assert len(results) == 2

    def test_get_recent_calls_get(self, memory, mock_chroma):
        mock_chroma.get.return_value = {
            "documents": ["событие A", "событие B", "событие C"],
            "metadatas": [
                {"timestamp": "2026-02-18T10:00:00"},
                {"timestamp": "2026-02-18T11:00:00"},
                {"timestamp": "2026-02-18T12:00:00"},
            ],
            "ids": ["1", "2", "3"],
        }
        recent = memory.get_recent(2)
        assert isinstance(recent, list)
