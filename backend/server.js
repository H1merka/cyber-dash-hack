const path = require("path");
const fs = require("fs");
const express = require("express");
const cors = require("cors");
const Database = require("better-sqlite3");

const PORT = Number(process.env.PORT || 4000);
const DB_DIR = path.join(__dirname, "data");
const DB_PATH = path.join(DB_DIR, "secret_forest.db");

const MOODS = new Set(["счастлив", "грустный", "злой", "нейтральный", "напуган"]);
const REL_TYPES = new Set(["друзья", "напряжение", "забота", "уважение", "нейтральные"]);

const moodImpact = {
  счастлив: 10,
  нейтральный: 0,
  грустный: -8,
  злой: -16,
  напуган: -10,
};

if (!fs.existsSync(DB_DIR)) {
  fs.mkdirSync(DB_DIR, { recursive: true });
}

const db = new Database(DB_PATH);
db.pragma("foreign_keys = ON");

function createSchema() {
  db.exec(`
    CREATE TABLE IF NOT EXISTS agents (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL UNIQUE,
      mood TEXT NOT NULL,
      personality_type TEXT NOT NULL,
      personality_title TEXT NOT NULL,
      description TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS relationships (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      agent_from_id INTEGER NOT NULL,
      agent_to_id INTEGER NOT NULL,
      relation_type TEXT NOT NULL,
      strength INTEGER NOT NULL DEFAULT 50,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (agent_from_id) REFERENCES agents(id) ON DELETE CASCADE,
      FOREIGN KEY (agent_to_id) REFERENCES agents(id) ON DELETE CASCADE,
      UNIQUE(agent_from_id, agent_to_id)
    );

    CREATE TABLE IF NOT EXISTS events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      content TEXT NOT NULL,
      actor_id INTEGER,
      target_id INTEGER,
      mood_after TEXT,
      relation_type TEXT,
      relation_delta INTEGER DEFAULT 0,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (actor_id) REFERENCES agents(id) ON DELETE SET NULL,
      FOREIGN KEY (target_id) REFERENCES agents(id) ON DELETE SET NULL
    );
  `);
}

function seedData() {
  const count = db.prepare("SELECT COUNT(*) AS total FROM agents").get().total;
  if (count > 0) return;

  const insertAgent = db.prepare(`
    INSERT INTO agents (name, mood, personality_type, personality_title, description)
    VALUES (@name, @mood, @personality_type, @personality_title, @description)
  `);

  const agents = [
    { name: "Мо", mood: "счастлив", personality_type: "ISFP", personality_title: "мечтатель", description: "Панда Мо любит тишину и ручьи." },
    { name: "Роки", mood: "грустный", personality_type: "ENTP", personality_title: "изобретатель", description: "Лис Роки придумывает рискованные идеи." },
    { name: "Фыр", mood: "злой", personality_type: "ISTJ", personality_title: "хранитель", description: "Ежик Фыр защищает свои границы." },
    { name: "Лея", mood: "нейтральный", personality_type: "INTJ", personality_title: "стратег", description: "Змея Лея анализирует каждую ситуацию." },
    { name: "Феликс", mood: "напуган", personality_type: "INFJ", personality_title: "мистик", description: "Кот Феликс чувствителен к изменениям." },
  ];
  const txAgents = db.transaction(() => agents.forEach((agent) => insertAgent.run(agent)));
  txAgents();

  const byName = Object.fromEntries(
    db.prepare("SELECT id, name FROM agents").all().map((row) => [row.name, row.id])
  );

  const insertRelation = db.prepare(`
    INSERT INTO relationships (agent_from_id, agent_to_id, relation_type, strength)
    VALUES (@agent_from_id, @agent_to_id, @relation_type, @strength)
  `);

  const rels = [
    { agent_from_id: byName["Мо"], agent_to_id: byName["Роки"], relation_type: "друзья", strength: 72 },
    { agent_from_id: byName["Роки"], agent_to_id: byName["Мо"], relation_type: "друзья", strength: 68 },
    { agent_from_id: byName["Роки"], agent_to_id: byName["Фыр"], relation_type: "напряжение", strength: 74 },
    { agent_from_id: byName["Мо"], agent_to_id: byName["Фыр"], relation_type: "забота", strength: 63 },
    { agent_from_id: byName["Феликс"], agent_to_id: byName["Лея"], relation_type: "уважение", strength: 56 },
    { agent_from_id: byName["Лея"], agent_to_id: byName["Роки"], relation_type: "нейтральные", strength: 48 },
  ];
  const txRels = db.transaction(() => rels.forEach((rel) => insertRelation.run(rel)));
  txRels();

  db.prepare(`
    INSERT INTO events (content, actor_id, target_id, mood_after, relation_type, relation_delta)
    VALUES (?, ?, ?, ?, ?, ?)
  `).run(
    "Панда Мо медленно прогуливается у ручья.",
    byName["Мо"],
    null,
    "счастлив",
    "нейтральные",
    0
  );
}

function moodAdjustedStrength(baseStrength, fromMood, toMood, relationType) {
  const from = moodImpact[fromMood] ?? 0;
  const to = moodImpact[toMood] ?? 0;
  const avg = Math.round((from + to) / 2);
  const direction = relationType === "напряжение" ? -1 : 1;
  const withMood = baseStrength + direction * avg;
  return Math.max(0, Math.min(100, withMood));
}

createSchema();
seedData();

const app = express();
app.use(cors());
app.use(express.json());

app.get("/api/health", (_req, res) => {
  res.json({ ok: true, service: "secret-forest-backend" });
});

app.get("/api/agents", (_req, res) => {
  const rows = db.prepare(`
    SELECT id, name, mood, personality_type, personality_title, description
    FROM agents
    ORDER BY id
  `).all();
  res.json(rows);
});

app.patch("/api/agents/:id/mood", (req, res) => {
  const id = Number(req.params.id);
  const mood = String(req.body?.mood || "").toLowerCase();
  if (!Number.isInteger(id)) return res.status(400).json({ error: "Некорректный id агента" });
  if (!MOODS.has(mood)) return res.status(400).json({ error: "Некорректное настроение" });

  const info = db.prepare("UPDATE agents SET mood = ? WHERE id = ?").run(mood, id);
  if (!info.changes) return res.status(404).json({ error: "Агент не найден" });
  const updated = db.prepare("SELECT id, name, mood FROM agents WHERE id = ?").get(id);
  res.json(updated);
});

app.get("/api/relationships", (_req, res) => {
  const rows = db.prepare(`
    SELECT r.id, r.agent_from_id, r.agent_to_id, r.relation_type, r.strength,
           af.name AS from_name, af.mood AS from_mood,
           at.name AS to_name, at.mood AS to_mood
    FROM relationships r
    JOIN agents af ON af.id = r.agent_from_id
    JOIN agents at ON at.id = r.agent_to_id
    ORDER BY r.id
  `).all();

  const normalized = rows.map((row) => ({
    ...row,
    display_strength: moodAdjustedStrength(row.strength, row.from_mood, row.to_mood, row.relation_type),
  }));
  res.json(normalized);
});

app.get("/api/events", (req, res) => {
  const limit = Math.min(100, Number(req.query.limit || 20));
  const rows = db.prepare(`
    SELECT e.id, e.content, e.mood_after, e.relation_type, e.relation_delta, e.created_at,
           af.name AS actor_name, at.name AS target_name
    FROM events e
    LEFT JOIN agents af ON af.id = e.actor_id
    LEFT JOIN agents at ON at.id = e.target_id
    ORDER BY e.id DESC
    LIMIT ?
  `).all(limit);
  res.json(rows);
});

app.post("/api/events", (req, res) => {
  const content = String(req.body?.content || "").trim();
  const actorId = req.body?.actorId ? Number(req.body.actorId) : null;
  const targetId = req.body?.targetId ? Number(req.body.targetId) : null;
  const moodAfter = req.body?.moodAfter ? String(req.body.moodAfter).toLowerCase() : null;
  const relationType = req.body?.relationType ? String(req.body.relationType).toLowerCase() : "нейтральные";
  const relationDelta = Number(req.body?.relationDelta || 0);

  if (!content) return res.status(400).json({ error: "Событие не может быть пустым" });
  if (moodAfter && !MOODS.has(moodAfter)) return res.status(400).json({ error: "Некорректное настроение" });
  if (!REL_TYPES.has(relationType)) return res.status(400).json({ error: "Некорректный тип связи" });

  const insertEvent = db.prepare(`
    INSERT INTO events (content, actor_id, target_id, mood_after, relation_type, relation_delta)
    VALUES (?, ?, ?, ?, ?, ?)
  `);

  const upsertRelation = db.prepare(`
    INSERT INTO relationships (agent_from_id, agent_to_id, relation_type, strength, updated_at)
    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(agent_from_id, agent_to_id) DO UPDATE SET
      relation_type = excluded.relation_type,
      strength = excluded.strength,
      updated_at = CURRENT_TIMESTAMP
  `);

  const tx = db.transaction(() => {
    const eventInfo = insertEvent.run(content, actorId, targetId, moodAfter, relationType, relationDelta);

    if (actorId && moodAfter) {
      db.prepare("UPDATE agents SET mood = ? WHERE id = ?").run(moodAfter, actorId);
    }

    if (actorId && targetId && relationDelta !== 0) {
      const current = db
        .prepare("SELECT strength FROM relationships WHERE agent_from_id = ? AND agent_to_id = ?")
        .get(actorId, targetId);
      const nextStrength = Math.max(0, Math.min(100, (current?.strength ?? 50) + relationDelta));
      upsertRelation.run(actorId, targetId, relationType, nextStrength);
    }

    return eventInfo.lastInsertRowid;
  });

  const id = tx();
  const created = db.prepare(`
    SELECT e.id, e.content, e.mood_after, e.relation_type, e.relation_delta, e.created_at,
           af.name AS actor_name, at.name AS target_name
    FROM events e
    LEFT JOIN agents af ON af.id = e.actor_id
    LEFT JOIN agents at ON at.id = e.target_id
    WHERE e.id = ?
  `).get(id);

  res.status(201).json(created);
});

app.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`Secret Forest backend running: http://localhost:${PORT}`);
});
