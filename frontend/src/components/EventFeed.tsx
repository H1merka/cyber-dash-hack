/**
 * Лента событий (real-time через WebSocket).
 */

import React from "react";
import type { EventItem } from "../types";

interface Props {
  events: EventItem[];
  loading?: boolean;
  compact?: boolean;
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  return `[${d.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" })}]`;
}

export default function EventFeed({ events, loading }: Props) {
  return (
    <div
      style={{
        background: "rgba(30,30,40,0.85)",
        borderRadius: 16,
        border: "1px solid #333",
        padding: "14px 16px",
        display: "flex",
        flexDirection: "column",
        minHeight: 0,
        overflow: "hidden",
      }}
    >
      <div
        style={{
          fontWeight: 700,
          fontSize: 15,
          color: "#fff",
          marginBottom: 10,
          flexShrink: 0,
        }}
      >
        Лента событий
      </div>

      <div style={{ flex: 1, overflowY: "auto", minHeight: 0 }}>
      {loading && (
        <div style={{ color: "#888", fontSize: 13 }}>Загрузка...</div>
      )}

      {!loading && events.length === 0 && (
        <div style={{ color: "#888", fontSize: 13 }}>Событий пока нет</div>
      )}

      {events.map((ev) => (
        <div
          key={ev.id}
          style={{
            fontSize: 13,
            color: "#ccc",
            padding: "4px 0",
            borderBottom: "1px solid #222",
          }}
        >
          <span style={{ color: "#666", marginRight: 6, fontFamily: "monospace" }}>
            {ev.created_at ? formatTime(ev.created_at) : ""}
          </span>
          {ev.actor_name && (
            <span style={{ color: "#9ce0ff", fontWeight: 600 }}>
              {ev.actor_name}:{" "}
            </span>
          )}
          <span>{ev.content}</span>
          {ev.relation_delta !== 0 && (
            <span
              style={{
                color: ev.relation_delta > 0 ? "#4ade80" : "#f87171",
                marginLeft: 6,
                fontSize: 11,
              }}
            >
              ({ev.relation_type} {ev.relation_delta > 0 ? "+" : ""}
              {ev.relation_delta})
            </span>
          )}
        </div>
      ))}
      </div>
    </div>
  );
}
