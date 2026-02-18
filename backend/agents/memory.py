"""
Модуль для управления эпизодической памятью агента
Используем ChromaDB для хранения и поиска воспоминаний
Создает автоматическую суммаризацию старых воспоминаний при превышении лимита
"""

import chromadb
from chromadb.config import Settings
import uuid
from datetime import datetime
import asyncio
import logging
from backend.llm.client import LLMClient
from backend.llm.prompts import SUMMARIZE_SYSTEM, SUMMARIZE_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


class Memory:

    def __init__(self, agent_id, persist_directory="./data/chroma", summarization_limit=50):
        """
        agent_id: айди агента
        persist_directory: папка для хранения данных ChromaDB
        summarization_limit: после скольких воспоминаний запускать суммирование
        """
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        self.collection_name = f"agent_{agent_id}"
        # Используем get_or_create вместо delete+create чтобы сохранять данные между перезапусками
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self.agent_id = agent_id
        self.summarization_limit = summarization_limit
        # Инициализируем счётчик реальным количеством записей
        self._count = self.collection.count()



    async def add_memory(self, text, metadata=None):
        """
        Добавляет новое воспоминание, после добавления проверяет, пора ли суммаризировать
        """
        if metadata is None:
            metadata = {}
        metadata.update({
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "type": "episodic"
        })
        memory_id = str(uuid.uuid4())
        self.collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[memory_id]
        )
        self._count += 1
        asyncio.create_task(self._check_and_summarize())



    async def _check_and_summarize(self):
        """
        Проверяет, нужно ли выполнить суммаризацию, и если да — запускает её.
        """
        if self._count <= self.summarization_limit:
            return

        # все данные коллекции
        all_data = self.collection.get()
        if not all_data['metadatas']:
            return

        # старые первые
        items = sorted(
            zip(all_data['ids'], all_data['documents'], all_data['metadatas']),
            key=lambda x: x[2].get('timestamp', '')
        )

        # Оставляем последние 10 
        keep_count = 10
        to_summarize = items[:-keep_count] if len(items) > keep_count else []
        if not to_summarize:
            return

        ids_to_remove = [item[0] for item in to_summarize]
        texts_to_summarize = [item[1] for item in to_summarize]

        # вызов LLM для суммаризации
        summary = await self._summarize_texts(texts_to_summarize)

        # Удаляем старые
        self.collection.delete(ids=ids_to_remove)

        # Добавляем суммаризированное воспоминание
        summary_metadata = {
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "type": "summary",
            "summarized_ids": ",".join(ids_to_remove) 
        }
        summary_id = str(uuid.uuid4())
        self.collection.add(
            documents=[summary],
            metadatas=[summary_metadata],
            ids=[summary_id]
        )
        #  счётчик
        self._count = self._count - len(ids_to_remove) + 1



    async def _summarize_texts(self, texts):
        """
        список текстов в LLM -возвращает краткую суммаризацию
        """
        if not texts:
            return "Нет событий."

        events_list = "\n".join(f"{i}. {t}" for i, t in enumerate(texts, 1))
        prompt = SUMMARIZE_PROMPT_TEMPLATE.format(events_list=events_list)

        try:
            llm = LLMClient()
            summary = await llm.generate(prompt, system_prompt=SUMMARIZE_SYSTEM)
            return summary
        except Exception:
            logger.exception("Ошибка суммаризации памяти агента %s", self.agent_id)
            return "Произошло несколько событий."



    def search_similar(self, query_text, n_results=5):
        """Находит похожие воспоминания по смыслу"""
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        return results['documents'][0] if results['documents'] else []



    def get_recent(self, n=5):
        """Вернет последние n воспоминаний"""
        all_data = self.collection.get()
        if not all_data['metadatas']:
            return []
        # от новых к старым
        sorted_items = sorted(
            zip(all_data['documents'], all_data['metadatas']),
            key=lambda x: x[1].get('timestamp', ''),
            reverse=True
        )
        return [doc for doc, _ in sorted_items[:n]]

