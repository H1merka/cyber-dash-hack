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
import "./index.css";

const API_URL = "http://localhost:8000";
const WS_URL = "ws://localhost:8000/ws";

export default function Main() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAgentId, setSelectedAgentId] = useState<number | null>(null);

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
      // Добавить новое событие в начало ленты
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
      // Перезагрузить отношения при обновлении
      fetch(`${API_URL}/api/relationships`)
        .then((r) => r.json())
        .then(setRelationships)
        .catch(() => {});
    }
  }, [lastMessage]);

  // ── Рендер ────────────────────────────────────────────────────────

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#0a0a14",
        color: "#ccc",
        fontFamily: "'Segoe UI', Arial, sans-serif",
        padding: "20px 24px",
      }}
    >
      {/* Заголовок */}
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 20,
        }}
      >
        <h1 style={{ color: "#fff", fontSize: 24, margin: 0 }}>
          🌲 Secret Forest — Виртуальный мир
        </h1>
        <div style={{ fontSize: 12, color: connected ? "#4ade80" : "#f87171" }}>
          {connected ? "● подключено" : "○ отключено"}
        </div>
      </header>

      {/* Карточки агентов */}
      <div
        style={{
          display: "flex",
          gap: 14,
          flexWrap: "wrap",
          marginBottom: 20,
        }}
      >
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

      {/* Основная сетка: граф + лента + управление */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr 340px",
          gap: 16,
          alignItems: "start",
        }}
      >
        {/* Граф отношений */}
        <RelationGraph
          agents={agents}
          relationships={relationships}
          onSelectAgent={(id) =>
            setSelectedAgentId((prev) => (prev === id ? null : id))
          }
        />

        {/* Лента событий */}
        <EventFeed events={events} loading={loading} />

        {/* Панель управления */}
        <ControlPanel agents={agents} onRefresh={refreshData} />
      </div>

      {/* Инспектор агента (боковая панель) */}
      <AgentInspector
        agentId={selectedAgentId}
        onClose={() => setSelectedAgentId(null)}
      />
    </div>
  );
}

