# Virtual World — Living Creatures Simulator

> Hackathon project "CYBER DASH" (February 16–18, 2026)

A web application featuring autonomous AI agents that live their own lives: they have personalities, memory, moods, and relationships with each other. The user observes their life in real time and can intervene through a web interface.

---

## Features

- **Autonomous AI agents** — unique personality, character, goals, and plans
- **Long-term memory** — episodic memory powered by a vector database with summarization
- **Emotional intelligence** — mood model that influences speech style and decisions
- **Multi-agent interaction** — agents chat, argue, befriend each other, and remember the past
- **Relationship graph** — interactive visualization of agent connections (friendship ↔ conflict)
- **Control panel** — add events, send messages to agents, adjust time speed
- **Real-time updates** — event feed via WebSocket

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.10), async, WebSocket |
| Frontend | React + TypeScript + Vite |
| LLM | Google Gemini API (free tier), fallback — Groq |
| Vector DB | ChromaDB (embedded) |
| State DB | SQLite + SQLAlchemy (async) |
| Relationship Graph | react-force-graph / D3.js |
| Styling | Tailwind CSS |

---

## Project Structure

```
cyber-dash-hack/
├── backend/
│   ├── main.py                  # FastAPI app, entry point
│   ├── config.py                # Settings, .env loading
│   ├── agents/
│   │   ├── agent.py             # Agent class (personality, mood, plans)
│   │   ├── memory.py            # ChromaDB — episodic memory, summarization
│   │   ├── emotions.py          # Mood model (numeric values)
│   │   ├── planner.py           # Reflection → goal → action via LLM
│   │   └── relationships.py     # Relationship matrix (affinity -100..+100)
│   ├── llm/
│   │   ├── client.py            # LLM abstraction (unified Gemini/Groq interface)
│   │   └── prompts.py           # System prompts, templates
│   ├── simulation/
│   │   ├── world.py             # World loop, time speed control
│   │   ├── events.py            # Event system
│   │   └── messaging.py         # Inter-agent messaging
│   ├── api/
│   │   ├── routes.py            # REST: /agents, /agents/{id}, /events
│   │   └── websocket.py         # WS: event stream, state updates
│   ├── db/
│   │   ├── models.py            # SQLAlchemy models
│   │   └── database.py          # Connection, sessions
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── EventFeed.tsx     # Event feed (real-time WS)
│   │   │   ├── RelationGraph.tsx # Interactive relationship graph
│   │   │   ├── AgentCard.tsx     # Avatar, name, mood
│   │   │   ├── AgentInspector.tsx# Profile: character, memory, plans
│   │   │   └── ControlPanel.tsx  # Add event, message, speed control
│   │   ├── hooks/useWebSocket.ts
│   │   └── types/index.ts
│   └── package.json
├── tests/                       # pytest
├── .env.example                 # Environment variables template
└── README.md
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Google Gemini API key (free: [aistudio.google.com](https://aistudio.google.com/))

### Backend

```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate        # PowerShell
# source venv/Scripts/activate  # Git Bash

# Install dependencies
pip install -r backend/requirements.txt

# Copy and fill in .env
cp .env.example .env

# Start the server
uvicorn backend.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Environment Variables

```env
LLM_PROVIDER=gemini          # gemini | groq
GEMINI_API_KEY=...
GROQ_API_KEY=...             # fallback
CHROMA_PERSIST_DIR=./data/chroma
DB_PATH=./data/world.db
SIMULATION_TICK_SECONDS=10
```

---

## Free LLM APIs

| Provider | Limit | Models | Link |
|---|---|---|---|
| Google Gemini | 15 RPM, 1M tokens/day | Gemini 2.0 Flash, 1.5 Flash | [aistudio.google.com](https://aistudio.google.com/) |
| Groq | 14,400 req/day, 30 RPM | Llama 3.3 70B, Mixtral | [console.groq.com](https://console.groq.com/) |
| OpenRouter | Free tier models | Various open-source | [openrouter.ai](https://openrouter.ai/) |
| Cohere | 1,000 calls/month | Command R+ | [dashboard.cohere.com](https://dashboard.cohere.com/) |

---

## Architecture

### Simulation Loop

Each world "tick", agents act sequentially (due to LLM rate limits):

```
Reflection → Goal Setting → Action → Memory/Mood Update
```

### Key Decisions

- **LLM abstraction**: unified interface `generate(prompt, system_prompt) -> str`, provider is switched via `.env`
- **Agent memory**: ChromaDB stores episodes as embeddings; when >50 entries — old ones are summarized into "key facts"
- **Mood → speech**: emotional state is dynamically injected into the system prompt
- **WebSocket**: streams all events (messages, mood changes, relationship updates)
- **Russian language embeddings**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

---

## Team Roles

| Role | Responsibility |
|---|---|
| Backend Lead | FastAPI, WebSocket, agent architecture, LLM integration, world model |
| AI/ML Engineer | Prompt engineering, emotion model, memory system (ChromaDB), agent planning |
| Frontend Developer | React app, D3 graph, event feed, control panel, WebSocket client |
| Fullstack / DevOps | Frontend↔Backend API integration, deployment (Railway/Render), testing, docs |

---

## Implementation Plan

### Day 1 — Foundation

- [ ] Project initialization, dependency installation, `.env` setup
- [ ] LLM client with Gemini/Groq support + rate limit handling
- [ ] `Agent` class (name, personality, mood, goals)
- [ ] Emotion model (`emotions.py`)
- [ ] Episodic memory (`memory.py` + ChromaDB)
- [ ] Agent planner (`planner.py`)
- [ ] Relationship matrix (`relationships.py`)
- [ ] Simulation loop (`world.py`) + messaging

### Day 2 — Interface & Integration

- [ ] REST API + WebSocket endpoints
- [ ] Event feed (EventFeed)
- [ ] Agent cards (AgentCard)
- [ ] Relationship graph (RelationGraph) — force-graph with colored edges
- [ ] Agent inspector (AgentInspector)
- [ ] Control panel (ControlPanel)
- [ ] Memory summarization, mood influence on speech style

### Day 3 — Deployment & Presentation

- [ ] Deploy backend (Railway/Render) + frontend (Vercel)
- [ ] Smoke testing on production
- [ ] README, documentation, presentation
- [ ] Project defense (14:30)

---

## Evaluation Criteria

| Criterion | Max Points | Description |
|---|---|---|
| Functionality | 30 | Agents interact, mood changes correctly |
| Web Interactivity | 20 | Beautiful, responsive interface, relationship graph |
| Memory Depth | 15 | Agent recalls past events, they influence decisions |
| Stability & Scalability | 25 | Error-free operation, ability to add agents |
| Presentation & Defense | 10 | Delivery, clear explanation of decisions, demo |

---

## License

MIT
