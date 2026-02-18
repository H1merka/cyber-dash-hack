/**
 * Панель управления: создать событие, отправить сообщение агенту, скорость.
 */

import React, { useRef, useState } from "react";
import type { Agent } from "../types";

const API_URL = "http://localhost:8000";

interface Props {
  agents: Agent[];
  onRefresh: () => void;
  compact?: boolean;
}

export default function ControlPanel({ agents, onRefresh, compact }: Props) {
  // --- Новое событие ---
  const [eventText, setEventText] = useState("");

  // --- Сообщение пользователя агенту ---
  const [msgText, setMsgText] = useState("");
  const [msgTargetId, setMsgTargetId] = useState<number | null>(agents[0]?.id ?? null);

  // --- Скорость ---
  const [speed, setSpeed] = useState(1);
  const speedTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Подставить первого агента, если ещё не выбран
  if (msgTargetId === null && agents.length > 0) {
    setMsgTargetId(agents[0].id);
  }

  async function handleCreateEvent() {
    if (!eventText.trim()) return;
    await fetch(`${API_URL}/api/events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        content: eventText.trim(),
        actorId: null,
        targetId: null,
        moodAfter: null,
        relationType: "нейтральные",
        relationDelta: 0,
      }),
    });
    setEventText("");
    onRefresh();
  }

  async function handleSendMessage() {
    if (!msgText.trim() || !msgTargetId) return;
    await fetch(`${API_URL}/api/agents/${msgTargetId}/message`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: msgText.trim() }),
    });
    setMsgText("");
    onRefresh();
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: compact ? 10 : 14 }}>
      {/* Новое событие */}
      <div
        style={{
          background: "rgba(30,30,40,0.85)",
          borderRadius: 16,
          border: "1px solid #333",
          padding: compact ? "10px 12px" : "14px 16px",
        }}
      >
        <div style={{ fontWeight: 700, fontSize: compact ? 13 : 14, color: "#fff", marginBottom: 8 }}>
          ✨ Новое событие
        </div>
        <input
          placeholder="Опиши событие..."
          value={eventText}
          onChange={(e) => setEventText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleCreateEvent()}
          style={{
            width: "100%",
            padding: "8px 10px",
            borderRadius: 8,
            border: "1px solid #444",
            background: "#1a1a2a",
            color: "#ccc",
            fontSize: 13,
            marginBottom: 8,
            boxSizing: "border-box",
          }}
        />
        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
          <button
            onClick={() => setEventText("")}
            style={{
              padding: "6px 14px",
              borderRadius: 8,
              border: "1px solid #555",
              background: "transparent",
              color: "#aaa",
              fontSize: 12,
              cursor: "pointer",
            }}
          >
            Очистить
          </button>
          <button
            onClick={handleCreateEvent}
            style={{
              padding: "6px 14px",
              borderRadius: 8,
              border: "none",
              background: "#6366f1",
              color: "#fff",
              fontSize: 12,
              cursor: "pointer",
            }}
          >
            Создать
          </button>
        </div>
      </div>

      {/* Отправить сообщение агенту */}
      <div
        style={{
          background: "rgba(30,30,40,0.85)",
          borderRadius: 16,
          border: "1px solid #333",
          padding: compact ? "10px 12px" : "14px 16px",
        }}
      >
        <div style={{ fontWeight: 700, fontSize: compact ? 13 : 14, color: "#fff", marginBottom: 8 }}>
          💬 Сообщение агенту
        </div>
        <select
          value={msgTargetId ?? ""}
          onChange={(e) => setMsgTargetId(Number(e.target.value))}
          style={{
            width: "100%",
            padding: "8px 10px",
            borderRadius: 8,
            border: "1px solid #444",
            background: "#1a1a2a",
            color: "#ccc",
            fontSize: 13,
            marginBottom: 8,
            boxSizing: "border-box",
          }}
        >
          {agents.map((a) => (
            <option key={a.id} value={a.id}>
              {a.avatar_emoji} {a.name}
            </option>
          ))}
        </select>
        <input
          placeholder="Сообщение..."
          value={msgText}
          onChange={(e) => setMsgText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
          style={{
            width: "100%",
            padding: "8px 10px",
            borderRadius: 8,
            border: "1px solid #444",
            background: "#1a1a2a",
            color: "#ccc",
            fontSize: 13,
            marginBottom: 8,
            boxSizing: "border-box",
          }}
        />
        <button
          onClick={handleSendMessage}
          style={{
            width: "100%",
            padding: "8px 14px",
            borderRadius: 8,
            border: "none",
            background: "#6366f1",
            color: "#fff",
            fontSize: 13,
            cursor: "pointer",
          }}
        >
          Отправить
        </button>
      </div>

      {/* Скорость симуляции */}
      <div
        style={{
          background: "rgba(30,30,40,0.85)",
          borderRadius: 16,
          border: "1px solid #333",
          padding: "14px 16px",
          display: "flex",
          alignItems: "center",
          gap: 12,
        }}
      >
        <span style={{ color: "#fff", fontSize: 13, fontWeight: 600 }}>⚡ Скорость</span>
        <input
          type="range"
          min={0.5}
          max={5}
          step={0.5}
          value={speed}
          onChange={(e) => {
            const val = Number(e.target.value);
            setSpeed(val);
            if (speedTimerRef.current) clearTimeout(speedTimerRef.current);
            speedTimerRef.current = setTimeout(() => {
              fetch(`${API_URL}/api/simulation/speed`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ speed: val }),
              }).catch(() => {});
            }, 300);
          }}
          style={{ flex: 1 }}
        />
        <span style={{ color: "#9ce0ff", fontSize: 14, fontWeight: 700, minWidth: 40 }}>
          {speed}x
        </span>
      </div>
    </div>
  );
}
