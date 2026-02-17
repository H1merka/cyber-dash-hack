from agents.memory import Memory

mem = Memory(agent_id=1)

# Очистим старую коллекцию (осторожно, если нужно сохранить)
mem.client.delete_collection(f"agent_{mem.agent_id}")
mem.collection = mem.client.create_collection(f"agent_{mem.agent_id}")

# Добавим разные воспоминания
mem.add_memory("Сегодня светило солнце, я гулял в парке.")
mem.add_memory("Поругался с агентом Бобом из-за еды.")
mem.add_memory("Маша подарила мне цветок, я очень рад.")
mem.add_memory("Агент Боб сказал, что я глупый.")

# Поиск по запросу "конфликт"
docs, metas = mem.search_similar("конфликт")
print("По запросу 'конфликт':", docs)

# Поиск по запросу "подарок"
docs, metas = mem.search_similar("подарок")
print("По запросу 'подарок':", docs)

#             python backend\test_memory.py