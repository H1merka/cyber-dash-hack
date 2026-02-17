import chromadb
from chromadb.config import Settings
import uuid
from datetime import datetime
import math

class Memory:
    def __init__(self, agent_id, persist_directory="./data/chroma", summarization_limit=50):
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        self.collection_name = f"agent_{agent_id}"
        # Удалим старую коллекцию, если она есть (для чистоты тестов) — в продакшене убрать
        try:
            self.client.delete_collection(self.collection_name)
        except:
            pass
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self.agent_id = agent_id
        self.summarization_limit = summarization_limit  # после скольких воспоминаний делать суммаризацию
        # Для простоты будем считать количество записей через отдельный счётчик или через получение всех
        # Но ChromaDB не даёт быстро узнать размер, поэтому будем хранить счётчик в памяти (он сбросится при перезапуске, но для демо пойдёт)
        self._count = 0

    def add_memory(self, text, metadata=None):
        """Добавить воспоминание, после чего проверить, не пора ли суммаризировать"""
        if metadata is None:
            metadata = {}
        metadata.update({
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "type": "episodic"  # пометим, что это обычное воспоминание
        })
        memory_id = str(uuid.uuid4())
        self.collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[memory_id]
        )
        self._count += 1
        # Проверяем, не пора ли суммаризировать
        self.summarize_old_if_needed()

    def search_similar(self, query_text, n_results=5):
        """Найти похожие воспоминания"""
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        return results['documents'][0] if results['documents'] else []

    def get_recent(self, n=5):
        """Получить последние n воспоминаний (по времени добавления)"""
        all_data = self.collection.get()
        if not all_data['metadatas']:
            return []
        # Сортируем по timestamp (строки ISO можно сравнивать лексикографически)
        sorted_items = sorted(
            zip(all_data['documents'], all_data['metadatas']),
            key=lambda x: x[1].get('timestamp', ''),
            reverse=True
        )
        return [doc for doc, _ in sorted_items[:n]]

    def summarize_old_if_needed(self):
        """
        Если количество воспоминаний превысило лимит, берёт самые старые (кроме последних 10)
        и заменяет их одним суммаризированным.
        """
        if self._count <= self.summarization_limit:
            return

        # Получаем все данные
        all_data = self.collection.get()
        if not all_data['metadatas']:
            return

        # Сортируем по времени (старые первые)
        items = sorted(
            zip(all_data['ids'], all_data['documents'], all_data['metadatas']),
            key=lambda x: x[2].get('timestamp', '')
        )

        # Оставляем последние 10 (самые свежие) — их не трогаем
        keep_count = 10
        to_summarize = items[:-keep_count] if len(items) > keep_count else []
        if not to_summarize:
            return

        # Собираем тексты для суммаризации
        texts_to_summarize = [doc for _, doc, _ in to_summarize]
        ids_to_remove = [id for id, _, _ in to_summarize]

        # Вызываем LLM для суммаризации (пока заглушка, потом заменим на реальный вызов)
        summary_text = self._call_summarization(texts_to_summarize)

        # Удаляем старые записи
        self.collection.delete(ids=ids_to_remove)

        # Добавляем суммаризированное воспоминание
        summary_metadata = {
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "type": "summary",
            "summarized_ids": ",".join(ids_to_remove)  # для отладки
        }
        summary_id = str(uuid.uuid4())
        self.collection.add(
            documents=[summary_text],
            metadatas=[summary_metadata],
            ids=[summary_id]
        )
        # Обновляем счётчик (грубо, но для демки пойдёт)
        self._count = self._count - len(ids_to_remove) + 1

    def _call_summarization(self, texts):
        """
        Заглушка для суммаризации. Возвращает фиктивный текст.
        Позже здесь будет вызов LLM.
        """
        # Пока просто склеиваем первые слова
        if not texts:
            return "Нет событий."
        # Берём первые 3 текста и сокращаем
        sample = texts[:3]
        combined = " ".join([t[:50] for t in sample])
        return f"[СУММАРИЗАЦИЯ] Краткое содержание старых событий: {combined}..."