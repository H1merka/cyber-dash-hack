import sqlite3
from datetime import datetime, timedelta

DB_NAME = "agents.db"


def create_tables(conn):
    cursor = conn.cursor()

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,              -- имя
                mood TEXT NOT NULL,                     -- настроение 
                personality_description TEXT,           -- характер 
                personality_type TEXT,                  -- тип личности
                background TEXT,                        -- предыстория
                origin TEXT,                            -- происхождение
                avatar_color TEXT DEFAULT '#cccccc',    -- цвет персонажа
                avatar_url TEXT,                        -- ссылка на изображение
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_from_id INTEGER NOT NULL,             -- связь от кого
                agent_to_id INTEGER NOT NULL,               -- связь к кому
                sympathy_level REAL DEFAULT 0.0,            -- от -1.0 до 1.0
                relationship_type TEXT,                     -- например 'друзья', 'враги', 'забота'
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_from_id) REFERENCES agents(id) ON DELETE CASCADE,
                FOREIGN KEY (agent_to_id) REFERENCES agents(id) ON DELETE CASCADE
            )
        """)

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id INTEGER NOT NULL,              -- тип персонажа   
                content TEXT NOT NULL,                  -- о чем воспоминания
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_key BOOLEAN DEFAULT 0,               -- ключевое воспоминание (для отображения)
                summary TEXT,                           -- о чем в кратце
                embedding BLOB,
                FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
            )
        """)

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id INTEGER NOT NULL,          -- тип персонажа
                goal TEXT NOT NULL,                 -- цель
                status TEXT DEFAULT 'active',       -- active, completed, abandoned
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deadline TIMESTAMP,                  -- опционально, когда планируется выполнить
                FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
            )
        """)

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_agent INTEGER NOT NULL,         -- от кого сообщение
                to_agent INTEGER NOT NULL,           -- кому
                content TEXT NOT NULL,               -- содержание сообщения
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_agent) REFERENCES agents(id) ON DELETE CASCADE,
                FOREIGN KEY (to_agent) REFERENCES agents(id) ON DELETE CASCADE
            )
        """)

    conn.commit()

# Функция заполнения профиля персонажей
def insert_initial_agents(conn):
    agents_data = [
        ("Мо", "Счастливая", "Добрая и любознательная панда", "ENFP", "Живёт у ручья, любит ягоды", "Местный житель",
         "#8B4513"),
        ("Роки", "Грустный", "Хитрый лис, склонный к авантюрам", "ISTP", "Всегда ищет приключения", "Местный житель",
         "#FF4500"),
        ("Фыр", "Злой", "Колючий ёжик, недоверчивый", "INTJ", "Живёт в норе под дубом", "Местный житель", "#2E8B57"),
        ("Лея", "Спокойная", "Мудрая змея, наблюдатель", "INFJ", "Обитает в пещере", "Местный житель", "#556B2F"),
        (
        "Феликс", "Напуган", "Трусливый заяц, но верный друг", "ISFP", "Прячется в кустах", "Местный житель", "#C0C0C0")
    ]
    cursor = conn.cursor()

    for name, mood, personality_desc, personality_type, background, origin, color in agents_data:
        try:
            cursor.execute("""
                    INSERT INTO agents (name, mood, personality_description, personality_type, background, origin, avatar_color)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (name, mood, personality_desc, personality_type, background, origin, color))
        except sqlite3.IntegrityError:
            print(f"Агент '{name}' уже есть, пропуск.")

    conn.commit()


# Функция заполнения отношений между персонажами
def insert_initial_relationships(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM agents")
    agents = {name: id for id, name in cursor.fetchall()}

    relations = [
        (agents["Мо"], agents["Роки"], 0.2, "нейтральные"),
        (agents["Мо"], agents["Фыр"], 0.8, "друзья"),
        (agents["Роки"], agents["Мо"], 0.5, "симпатия"),
        (agents["Фыр"], agents["Мо"], -0.3, "настороженность"),
        (agents["Лея"], agents["Роки"], 0.0, "наблюдение"),
        (agents["Феликс"], agents["Фыр"], -0.6, "страх"),
    ]

    for from_id, to_id, level, rtype in relations:

        try:
            cursor.execute("""
                INSERT INTO relationships (agent_from_id, agent_to_id, sympathy_level, relationship_type)
                VALUES (?, ?, ?, ?)
            """, (from_id, to_id, level, rtype))

        except sqlite3.IntegrityError:
            cursor.execute("""
                UPDATE relationships SET sympathy_level = ?, relationship_type = ?, updated_at = CURRENT_TIMESTAMP
                WHERE agent_from_id = ? AND agent_to_id = ?
            """, (level, rtype, from_id, to_id))

    conn.commit()


# Функция заполнения воспоминаний и целей для персонажей
def insert_sample_memories_and_goals(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM agents WHERE name = 'Мо'")
    mo_id = cursor.fetchone()[0]

    # Пример заполнения воспоминаниями для Мо
    memories = [
        (mo_id, "Обнаружил скрытую поляну со старыми цветущими сакурами, их лепестки танцевали в лунном свете.",
         datetime.now() - timedelta(hours=5), True),
        (mo_id, "Вместе с Феликсом нашли светящийся камень под старым дубом. Договорились никому не рассказывать.",
         datetime.now() - timedelta(days=60), True),
        (mo_id, "Нашёл потерявшегося малыша-денёта и согревал его всю ночь, пока не пришла его мама. На следующий день она принесла мне ягоды.",
         datetime.now() - timedelta(days=365), True),
    ]

    for agent_id, content, ts, is_key in memories:
        cursor.execute("""
            INSERT INTO memories (agent_id, content, timestamp, is_key)
            VALUES (?, ?, ?, ?)
        """, (agent_id, content, ts, is_key))

    # Определение целей
    goals = [
        (mo_id, "Посетить ручей: вернуться к ручью, чтобы проверить, поёт ли вода днём.", "active"),
        (mo_id, "Дождаться заката на скале Эха, чтобы послушать, как ветер свистит в пустыне ракушках, останавливаясь змеей Леей.", "active"),
        (mo_id, "Найти место, где кроны деревьев не загораживают созвездие Большой Медведицы, и просто смотреть вверх, пока не слипнутся глаза.", "active"),
    ]

    for agent_id, goal, status in goals:
        cursor.execute("""
            INSERT INTO goals (agent_id, goal, status)
            VALUES (?, ?, ?)
        """, (agent_id, goal, status))

    conn.commit()


def main():
    conn = sqlite3.connect(DB_NAME)
    create_tables(conn)

    # insert_initial_agents(conn)
    # insert_initial_relationships(conn)
    # insert_sample_memories_and_goals(conn)

    # cursor = conn.cursor()
    # cursor.execute("SELECT id, name, mood, personality_type, background FROM agents")
    # for row in cursor.fetchall():
    #     print(row)
    #
    # cursor.execute(
    #     "SELECT content, timestamp FROM memories WHERE agent_id = (SELECT id FROM agents WHERE name = 'Мо') AND is_key = 1")
    # for row in cursor.fetchall():
    #     print(row)

    conn.close()


if __name__ == "__main__":
    main()
