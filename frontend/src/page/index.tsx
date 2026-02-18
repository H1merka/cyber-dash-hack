/**
 * Главная страница «Виртуального мира».
 * Компонует все виджеты: карточки агентов, граф, ленту, панель управления, инспектор.
 */

import React, { useCallback, useEffect, useState } from "react";
import type { Agent, EventItem, Relationship, WSMessage } from "../types";
import AgentCard from "../components/AgentCard";
import EventFeed from "../components/EventFeed";
import RelationGraph from "../components/RelationGraph";
import AgentInspector from "../components/AgentInspector";
import ControlPanel from "../components/ControlPanel";
import { useWebSocket } from "../hooks/useWebSocket";
import { useIsMobile, useIsTablet } from "../hooks/useMediaQuery";
import "./index.css";

const API_URL = "http://localhost:8000";
const WS_URL = "ws://localhost:8000/ws";

export default function Main() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAgentId, setSelectedAgentId] = useState<number | null>(null);

  const isMobile = useIsMobile();
  const isTablet = useIsTablet();

  // WebSocket
  const { connected, lastMessage } = useWebSocket(WS_URL);

  // ── Загрузка данных ───────────────────────────────────────────────

  const refreshData = useCallback(async () => {
    try {
      const [agentsRes, relRes, eventsRes] = await Promise.all([
        fetch(`${API_URL}/api/agents`),
        fetch(`${API_URL}/api/relationships`),
        fetch(`${API_URL}/api/events?limit=20`),
      ]);
      const [agentsData, relData, eventsData] = await Promise.all([
        agentsRes.json(),
        relRes.json(),
        eventsRes.json(),
      ]);
      setAgents(agentsData);
      setRelationships(relData);
      setEvents(eventsData);
    } catch (err) {
      console.error("Ошибка загрузки данных:", err);
    }
  }, []);

  useEffect(() => {
    refreshData().finally(() => setLoading(false));
  }, [refreshData]);

  // ── Реакция на WebSocket-сообщения ────────────────────────────────

  useEffect(() => {
    if (!lastMessage) return;
    const msg = lastMessage as WSMessage;

    if (msg.type === "event") {
      const evData = msg.data as unknown as EventItem;
      setEvents((prev) => [evData, ...prev].slice(0, 50));
    }

    if (msg.type === "mood_update") {
      const { agent_id, mood, mood_value } = msg.data as {
        agent_id: number;
        mood: string;
        mood_value: number;
      };
      setAgents((prev) =>
        prev.map((a) =>
          a.id === agent_id ? { ...a, mood: mood as Agent["mood"], mood_value } : a
        )
      );
    }

    if (msg.type === "relation_update") {
      fetch(`${API_URL}/api/relationships`)
        .then((r) => r.json())
        .then(setRelationships)
        .catch(() => {});
    }
  }, [lastMessage]);

  // ── Рендер ────────────────────────────────────────────────────────

  if (isMobile) {
    // ── Мобильная раскладка: вертикальный стек ──
    return (
      <div className="page-root page-mobile">
        <header className="page-header">
          <h1 className="page-title">🌲 Secret Forest</h1>
          <div className={`ws-status ${connected ? "online" : "offline"}`}>
            {connected ? "● онлайн" : "○ офлайн"}
          </div>
        </header>

        {/* Карточки агентов — горизонтальная прокрутка */}
        <div className="agents-row agents-row-mobile">
          {agents.map((agent) => (
            <AgentCard
              key={agent.id}
              agent={agent}
              compact
              selected={selectedAgentId === agent.id}
              onClick={() =>
                setSelectedAgentId((prev) => (prev === agent.id ? null : agent.id))
              }
            />
          ))}
        </div>

        {/* Граф */}
        <RelationGraph agents={agents} relationships={relationships} compact
          onSelectAgent={(id) => setSelectedAgentId((prev) => (prev === id ? null : id))}
        />

        {/* Лента событий */}
        <EventFeed events={events} loading={loading} />

        {/* Панель управления */}
        <ControlPanel agents={agents} onRefresh={refreshData} compact />

        {/* Инспектор */}
        <AgentInspector agentId={selectedAgentId} onClose={() => setSelectedAgentId(null)} fullScreen />
      </div>
    );
  }

  // ── Десктоп / Планшет раскладка ──
  const gridCols = isTablet ? "1fr 1fr" : "1fr 1fr 340px";

  return (
    <div className="page-root">
      <header className="page-header">
        <h1 className="page-title">🌲 Secret Forest — Виртуальный мир</h1>
        <div className={`ws-status ${connected ? "online" : "offline"}`}>
          {connected ? "● подключено" : "○ отключено"}
        </div>
      </header>

      {/* Карточки агентов */}
      <div className="agents-row">
        {agents.map((agent) => (
          <AgentCard
            key={agent.id}
            agent={agent}
            selected={selectedAgentId === agent.id}
            onClick={() =>
              setSelectedAgentId((prev) => (prev === agent.id ? null : agent.id))
            }
          />
        ))}
      </div>

      {/* Основная сетка */}
      <div
        className="main-grid"
        style={{ gridTemplateColumns: gridCols }}
      >
        <RelationGraph agents={agents} relationships={relationships}
          onSelectAgent={(id) => setSelectedAgentId((prev) => (prev === id ? null : id))}
        />
        <EventFeed events={events} loading={loading} />
        <ControlPanel agents={agents} onRefresh={refreshData} />
      </div>

      <AgentInspector agentId={selectedAgentId} onClose={() => setSelectedAgentId(null)} />
    </div>
  );
}

