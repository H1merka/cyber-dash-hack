import React, { useEffect, useMemo, useState } from "react";
import "./index.css";

const API_URL = "http://localhost:4000";
const DESIGN_WIDTH = 1440;
const DESIGN_HEIGHT = 1024;

type Mood = "счастлив" | "грустный" | "злой" | "нейтральный" | "напуган";
type RelationType = "друзья" | "напряжение" | "забота" | "уважение" | "нейтральные";

type Agent = {
  id: number;
  name: string;
  mood: Mood;
  personality_type: string;
  personality_title: string;
};

type Relationship = {
  id: number;
  agent_from_id: number;
  agent_to_id: number;
  relation_type: RelationType;
  display_strength: number;
};

type EventItem = {
  id: number;
  content: string;
  created_at: string;
  actor_name: string | null;
  target_name: string | null;
  mood_after: Mood | null;
  relation_type: RelationType | null;
  relation_delta: number;
};

const NODE_POSITIONS: Record<string, { x: number; y: number; emoji: string }> = {
  Мо: { x: 42, y: 36, emoji: "🐼" },
  Роки: { x: 300, y: 36, emoji: "🦊" },
  Фыр: { x: 42, y: 210, emoji: "🦔" },
  Феликс: { x: 300, y: 210, emoji: "🐱" },
  Лея: { x: 170, y: 394, emoji: "🐍" },
};

const moodLabel: Record<Mood, string> = {
  счастлив: "Счастлив",
  грустный: "Грустный",
  злой: "Злой",
  нейтральный: "Нейтральный",
  напуган: "Напуган",
};

function relationColor(type: RelationType, value: number) {
  if (type === "напряжение") {
    if (value >= 70) return "#ff8a3d";
    if (value >= 45) return "#ffd35a";
    return "#66dd8f";
  }
  if (value >= 70) return "#57f163";
  if (value >= 45) return "#73baff";
  return "#b38cff";
}

function formatTime(input: string) {
  const date = new Date(input);
  return `[${date.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" })}]`;
}

export default function Main() {
  const [viewport, setViewport] = useState({ width: window.innerWidth, height: window.innerHeight });
  const [agents, setAgents] = useState([] as Agent[]);
  const [relationships, setRelationships] = useState([] as Relationship[]);
  const [events, setEvents] = useState([] as EventItem[]);
  const [loading, setLoading] = useState(true);
  const [newEvent, setNewEvent] = useState("");
  const [messageText, setMessageText] = useState("");
  const [messageActorId, setMessageActorId] = useState(null as number | null);

  useEffect(() => {
    const onResize = () => setViewport({ width: window.innerWidth, height: window.innerHeight });
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  async function refreshData() {
    const [agentsRes, relRes, eventsRes] = await Promise.all([
      fetch(`${API_URL}/api/agents`),
      fetch(`${API_URL}/api/relationships`),
      fetch(`${API_URL}/api/events?limit=8`),
    ]);
    const [agentsData, relData, eventsData] = await Promise.all([agentsRes.json(), relRes.json(), eventsRes.json()]);
    setAgents(agentsData);
    setRelationships(relData);
    setEvents(eventsData);
    if (!messageActorId && agentsData.length > 0) {
      setMessageActorId(agentsData[0].id);
    }
  }

  useEffect(() => {
    refreshData()
      .catch(() => null)
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const agentByName = useMemo(
    () => Object.fromEntries(agents.map((agent) => [agent.name, agent])),
    [agents]
  );

  const graphEdges = useMemo(() => {
    const map = new Map<string, Relationship>();
    relationships.forEach((edge) => {
      const fromName = agents.find((x) => x.id === edge.agent_from_id)?.name;
      const toName = agents.find((x) => x.id === edge.agent_to_id)?.name;
      if (!fromName || !toName) return;
      const key = [fromName, toName].sort().join("-");
      const old = map.get(key);
      if (!old || edge.display_strength > old.display_strength) map.set(key, edge);
    });
    return Array.from(map.values());
  }, [relationships, agents]);

  const scaleStyle = {
    transform: `scale(${viewport.width / DESIGN_WIDTH}, ${viewport.height / DESIGN_HEIGHT})`,
  };

  async function createEvent() {
    if (!newEvent.trim()) return;
    const actorId = agents[0]?.id ?? null;
    const targetId = agents[1]?.id ?? null;
    await fetch(`${API_URL}/api/events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        content: newEvent.trim(),
        actorId,
        targetId,
        moodAfter: "нейтральный",
        relationType: "нейтральные" as RelationType,
        relationDelta: 0,
      }),
    });
    setNewEvent("");
    await refreshData();
  }

  async function sendMessageFromActor() {
    if (!messageText.trim() || !messageActorId) return;
    await fetch(`${API_URL}/api/events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        content: messageText.trim(),
        actorId: messageActorId,
        targetId: null,
        moodAfter: "нейтральный",
        relationType: "нейтральные" as RelationType,
        relationDelta: 0,
      }),
    });
    setMessageText("");
    await refreshData();
  }

  const mo = agentByName["Мо"];
  const roki = agentByName["Роки"];
  const fyr = agentByName["Фыр"];
  const leya = agentByName["Лея"];
  const felix = agentByName["Феликс"];

  return (
    <div className="screen-root">
      <div className="main-container" style={scaleStyle}>
        <div className="flex-row-a">
          <div className="rectangle">
            <span className="felix">Феликс</span>
            <div className="ellipse" />
            <div className="fxemoji-cat" />
            <span className="napugan">{felix ? moodLabel[felix.mood] : "Напуган"}</span>
            <div className="ellipse-1" />
            <div className="ellipse-2" />
            <span className="agent-personality felix-type">{felix ? `${felix.personality_type} - ${felix.personality_title}` : ""}</span>
          </div>
          <div className="rectangle-3">
            <div className="flex-row-fc">
              <div className="wand-stars-outline-rounded" />
              <span className="novoe-sobytie">Новое событие</span>
            </div>
            <div className="line" />
            <div className="event-form-compact">
              <input
                className="event-input-compact"
                placeholder="Опиши событие..."
                value={newEvent}
                onChange={(event) => setNewEvent(event.target.value)}
              />
              <div className="regroup regroup-compact">
                <button type="button" className="rectangle-4" onClick={() => setNewEvent("")}>
                  <span className="otmena">Очистить</span>
                </button>
                <button type="button" className="rectangle-5" onClick={createEvent}>
                  <span className="sozdat">Создать</span>
                </button>
              </div>
            </div>
          </div>
        </div>
        <div className="image" />
        <div className="flex-row-ba">
          <div className="ellipse-6" />
          <span className="plus">+</span>
          <span className="secret-forest">Secret forest</span>
          <div className="rectangle-7">
            <span className="speed">Скорость</span>
            <div className="speed-outline" />
            <span className="x">1,5x</span>
            <div className="ellipse-8" />
            <div className="line-9" />
            <div className="line-a" />
          </div>
          <span className="add-character">Добавить персонажа</span>
          <div className="rectangle-b">
            <div className="ellipse-c" />
            <div className="fluent-emoji-flat-panda" />
            <span className="mo">Мо</span>
            <span className="happy">{mo ? moodLabel[mo.mood] : "Счастлив"}</span>
            <div className="ellipse-d" />
            <div className="ellipse-e" />
            <span className="agent-personality mo-type">{mo ? `${mo.personality_type} - ${mo.personality_title}` : ""}</span>
          </div>
          <div className="rectangle-f">
            <span className="event-feed">Лента событий</span>
            <div className="event-list">
              {loading && <div className="event-row">Загрузка...</div>}
              {!loading && events.map((event) => (
                <div className="event-row" key={event.id}>
                  <span className="event-time">{formatTime(event.created_at)}</span>
                  <span className="event-text">
                    {event.actor_name ? `${event.actor_name}: ` : ""}
                    {event.content}
                    {event.relation_delta ? ` (${event.relation_type} ${event.relation_delta > 0 ? "+" : ""}${event.relation_delta})` : ""}
                  </span>
                </div>
              ))}
            </div>
          </div>
          <div className="rectangle-19">
            <div className="relationship-graph-panel">
              <span className="relationship-graph-title">Граф отношений</span>
              <div className="graph-db-note">
                Данные графа подтягиваются из БД
              </div>
              <div className="graph-mood-readonly">
                {agents.map((agent) => (
                  <span key={agent.id}>
                    {agent.name}: {moodLabel[agent.mood]}
                  </span>
                ))}
              </div>
              <svg viewBox="0 0 340 440" className="relationship-svg" role="img" aria-label="Граф отношений">
                {graphEdges.map((edge) => {
                  const fromName = agents.find((x) => x.id === edge.agent_from_id)?.name;
                  const toName = agents.find((x) => x.id === edge.agent_to_id)?.name;
                  if (!fromName || !toName || !NODE_POSITIONS[fromName] || !NODE_POSITIONS[toName]) return null;
                  const from = NODE_POSITIONS[fromName];
                  const to = NODE_POSITIONS[toName];
                  const midX = (from.x + to.x) / 2;
                  const midY = (from.y + to.y) / 2;
                  const color = relationColor(edge.relation_type, edge.display_strength);
                  return (
                    <g key={edge.id}>
                      <line x1={from.x} y1={from.y} x2={to.x} y2={to.y} stroke={color} strokeWidth="5" strokeLinecap="round" />
                      <text x={midX} y={midY - 8} fill={color} textAnchor="middle" className="graph-edge-label">
                        {edge.relation_type}
                      </text>
                    </g>
                  );
                })}
                {agents.map((agent) => {
                  const node = NODE_POSITIONS[agent.name];
                  if (!node) return null;
                  return (
                    <g key={agent.id}>
                      <circle cx={node.x} cy={node.y} r="24" fill="#d4d4d4" />
                      <text x={node.x} y={node.y + 9} textAnchor="middle" className="graph-node-emoji">
                        {node.emoji}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>
          </div>
          <div className="rectangle-2b">
            <div className="ellipse-2c" />
            <span className="roki">Роки</span>
            <div className="fluent-emoji-flat-fox" />
            <span className="grustnyi">{roki ? moodLabel[roki.mood] : "Грустный"}</span>
            <div className="ellipse-2d" />
            <div className="ellipse-2e" />
            <span className="agent-personality roki-type">{roki ? `${roki.personality_type} - ${roki.personality_title}` : ""}</span>
          </div>
          <div className="rectangle-2f">
            <span className="fyr">Фыр</span>
            <div className="twemoji-hedgehog-30" />
            <div className="ellipse-31" />
            <span className="span-zloy">{fyr ? moodLabel[fyr.mood] : "Злой"}</span>
            <div className="ellipse-32" />
            <div className="ellipse-33" />
            <span className="agent-personality fyr-type">{fyr ? `${fyr.personality_type} - ${fyr.personality_title}` : ""}</span>
          </div>
          <div className="rectangle-34">
            <span className="span-leya">Лея</span>
            <div className="ellipse-35" />
            <div className="snake" />
            <span className="span-spokojnaya">{leya ? moodLabel[leya.mood] : "Нейтральный"}</span>
            <div className="ellipse-36" />
            <div className="ellipse-37" />
            <span className="agent-personality leya-type">{leya ? `${leya.personality_type} - ${leya.personality_title}` : ""}</span>
          </div>
        </div>
        <div className="rectangle-38">
          <button type="button" className="rectangle-39 send-button" onClick={sendMessageFromActor}>
            <span className="span-send">Send</span>
            <div className="plain-line-duotone" />
          </button>
          <div className="rectangle-3a">
            <div className="emoji-flat-panda" />
            <select
              className="message-actor-select"
              value={messageActorId ?? ""}
              onChange={(event) => setMessageActorId(Number(event.target.value))}
            >
              {agents.map((agent) => (
                <option key={agent.id} value={agent.id}>
                  {agent.name}
                </option>
              ))}
            </select>
            <div className="flex-column-eed">
              <div className="polygon" />
              <div className="polygon-3b" />
            </div>
          </div>
          <input
            className="message-input"
            placeholder="Отправить сообщение..."
            value={messageText}
            onChange={(event) => setMessageText(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                void sendMessageFromActor();
              }
            }}
          />
        </div>
      </div>
    </div>
  );
}
