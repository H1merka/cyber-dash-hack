# Виртуальный мир — симулятор живых существ

> Хакатон-проект «КИБЕР РЫВОК» (16–18 февраля 2026)

Веб-приложение с автономными AI-агентами, которые живут своей жизнью: имеют личность, память, настроение и отношения друг с другом. Пользователь наблюдает за их жизнью в реальном времени и может вмешиваться через веб-интерфейс.

---

## Возможности

- **Автономные AI-агенты** — уникальная личность, характер, цели и планы
- **Долговременная память** — эпизодическая память на базе векторной БД с суммаризацией
- **Эмоциональный интеллект** — модель настроения, влияющая на стиль речи и решения
- **Мультиагентное взаимодействие** — агенты общаются, спорят, дружат, помнят прошлое
- **Граф отношений** — интерактивная визуализация связей между агентами (дружба ↔ конфликт)
- **Панель управления** — добавление событий, отправка сообщений агентам, регулировка скорости времени
- **Real-time обновления** — лента событий через WebSocket

---

## Стек технологий

| Слой | Технология |
|---|---|
| Backend | FastAPI (Python 3.10), async, WebSocket |
| Frontend | React + TypeScript + Vite |
| LLM | Google Gemini API (free tier), fallback — Groq |
| Векторная БД | ChromaDB (embedded) |
| БД состояния | SQLite + SQLAlchemy (async) |
| Граф отношений | react-force-graph / D3.js |
| Стилизация | Tailwind CSS |

---

## Структура проекта

```
cyber-dash-hack/
├── backend/
│   ├── main.py                  # FastAPI app, точка входа
│   ├── config.py                # Настройки, загрузка .env
│   ├── agents/
│   │   ├── agent.py             # Класс Agent (личность, настроение, планы)
│   │   ├── memory.py            # ChromaDB — эпизодическая память, суммаризация
│   │   ├── emotions.py          # Модель настроения (числовые значения)
│   │   ├── planner.py           # Рефлексия → цель → действие через LLM
│   │   └── relationships.py     # Матрица отношений (симпатия -100..+100)
│   ├── llm/
│   │   ├── client.py            # Абстракция LLM (единый интерфейс Gemini/Groq)
│   │   └── prompts.py           # Системные промпты, шаблоны
│   ├── simulation/
│   │   ├── world.py             # Мировой цикл, управление скоростью времени
│   │   ├── events.py            # Система событий
│   │   └── messaging.py         # Обмен сообщениями между агентами
│   ├── api/
│   │   ├── routes.py            # REST: /agents, /agents/{id}, /events
│   │   └── websocket.py         # WS: стрим событий, обновления состояния
│   ├── db/
│   │   ├── models.py            # SQLAlchemy модели
│   │   └── database.py          # Подключение, сессии
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── EventFeed.tsx     # Лента событий (real-time WS)
│   │   │   ├── RelationGraph.tsx # Интерактивный граф отношений
│   │   │   ├── AgentCard.tsx     # Аватар, имя, настроение
│   │   │   ├── AgentInspector.tsx# Профиль: характер, память, планы
│   │   │   └── ControlPanel.tsx  # Добавить событие, сообщение, скорость
│   │   ├── hooks/useWebSocket.ts
│   │   └── types/index.ts
│   └── package.json
├── tests/                       # pytest
├── .env.example                 # Шаблон переменных окружения
└── README.md
```

---

## Быстрый старт

### Требования

- Python 3.10+
- Node.js 18+
- API-ключ Google Gemini (бесплатно: [aistudio.google.com](https://aistudio.google.com/))

### Backend

```bash
# Создать и активировать виртуальное окружение
python -m venv venv
.\venv\Scripts\activate        # PowerShell
# source venv/Scripts/activate  # Git Bash

# Установить зависимости
pip install -r backend/requirements.txt

# Скопировать и заполнить .env
cp .env.example .env

# Запустить сервер
uvicorn backend.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Переменные окружения

```env
LLM_PROVIDER=gemini          # gemini | groq
GEMINI_API_KEY=...
GROQ_API_KEY=...             # fallback
CHROMA_PERSIST_DIR=./data/chroma
DB_PATH=./data/world.db
SIMULATION_TICK_SECONDS=10
```

---

## Бесплатные LLM API

| Провайдер | Лимит | Модели | Ссылка |
|---|---|---|---|
| Google Gemini | 15 RPM, 1M tokens/day | Gemini 2.0 Flash, 1.5 Flash | [aistudio.google.com](https://aistudio.google.com/) |
| Groq | 14 400 req/day, 30 RPM | Llama 3.3 70B, Mixtral | [console.groq.com](https://console.groq.com/) |
| OpenRouter | Free tier модели | Различные open-source | [openrouter.ai](https://openrouter.ai/) |
| Cohere | 1000 calls/month | Command R+ | [dashboard.cohere.com](https://dashboard.cohere.com/) |

---

## Архитектура

### Цикл симуляции

Каждый «тик» мира агенты действуют последовательно (rate limit LLM):

```
Рефлексия → Постановка цели → Действие → Обновление памяти/настроения
```

### Ключевые решения

- **LLM-абстракция**: единый интерфейс `generate(prompt, system_prompt) -> str`, провайдер переключается через `.env`
- **Память агента**: ChromaDB хранит эпизоды как embeddings; при >50 записей — суммаризация старых в «ключевые факты»
- **Настроение → речь**: эмоциональное состояние динамически вставляется в системный промпт
- **WebSocket**: стрим всех событий (сообщения, смена настроения, обновление отношений)
- **Embedding для русского**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

---

## Роли в команде

| Роль | Ответственность |
|---|---|
| Backend Lead | FastAPI, WebSocket, архитектура агентов, интеграция LLM, модель мира |
| AI/ML Engineer | Промпт-инжиниринг, модель эмоций, система памяти (ChromaDB), планирование агентов |
| Frontend Developer | React-приложение, граф D3, лента событий, панель управления, WebSocket-клиент |
| Fullstack / DevOps | API-интеграция фронт↔бэк, деплой (Railway/Render), тестирование, документация |

---

## План реализации

### День 1 — Фундамент

- [ ] Инициализация проекта, установка зависимостей, настройка `.env`
- [ ] LLM-клиент с поддержкой Gemini/Groq + обработка rate limit
- [ ] Класс `Agent` (имя, личность, настроение, цели)
- [ ] Модель эмоций (`emotions.py`)
- [ ] Эпизодическая память (`memory.py` + ChromaDB)
- [ ] Планировщик агента (`planner.py`)
- [ ] Матрица отношений (`relationships.py`)
- [ ] Цикл симуляции (`world.py`) + обмен сообщениями

### День 2 — Интерфейс и интеграция

- [ ] REST API + WebSocket endpoints
- [ ] Лента событий (EventFeed)
- [ ] Карточки агентов (AgentCard)
- [ ] Граф отношений (RelationGraph) — force-graph с цветными рёбрами
- [ ] Инспектор агента (AgentInspector)
- [ ] Панель управления (ControlPanel)
- [ ] Суммаризация памяти, влияние настроения на стиль речи

### День 3 — Деплой и защита

- [ ] Деплой backend (Railway/Render) + frontend (Vercel)
- [ ] Smoke-тестирование на production
- [ ] README, документация, презентация
- [ ] Защита проекта (14:30)

---

## Критерии оценки

| Критерий | Макс. баллы | Описание |
|---|---|---|
| Функциональность | 30 | Агенты взаимодействуют, настроение меняется правильно |
| Интерактивность веба | 20 | Красивый, живой интерфейс, граф отношений |
| Глубина памяти | 15 | Агент вспоминает прошлое, оно влияет на решения |
| Стабильность и масштабируемость | 25 | Работа без ошибок, возможность добавления агентов |
| Презентация и защита | 10 | Подача, объяснение решений, демонстрация |

---

## Лицензия

MIT