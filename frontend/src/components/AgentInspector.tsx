/**
 * Профиль агента: подробная информация, память, планы.
 * Открывается при клике на карточку агента.
 */

import React, { useEffect, useState } from "react";
import type { AgentDetail } from "../types";
import { MOOD_LABELS } from "../types";

const API_URL = "http://localhost:8000";

interface Props {
  agentId: number | null;
  onClose: () => void;
  fullScreen?: boolean;
}

export default function AgentInspector({ agentId, onClose, fullScreen }: Props) {
  const [detail, setDetail] = useState<AgentDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!agentId) {
      setDetail(null);
      return;
    }
    setLoading(true);
    fetch(`${API_URL}/api/agents/${agentId}`)
      .then((r) => r.json())
      .then((data) => setDetail(data))
      .catch(() => setDetail(null))
      .finally(() => setLoading(false));
  }, [agentId]);

  if (!agentId) return null;

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        right: 0,
        width: fullScreen ? "100vw" : 380,
        height: "100vh",
        background: fullScreen ? "#0a0a14" : "rgba(20,20,30,0.97)",
        borderLeft: fullScreen ? "none" : "1px solid #444",
        padding: fullScreen ? "16px 14px" : "24px 20px",
        overflowY: "auto",
        zIndex: 100,
      }}
    >
      <button
        onClick={onClose}
        style={{
          position: "absolute",
          top: 12,
          right: 16,
          background: "none",
          border: "none",
          color: "#aaa",
          fontSize: 22,
          cursor: "pointer",
        }}
      >
        ✕
      </button>

      {loading && <div style={{ color: "#888" }}>Загрузка...</div>}

      {detail && !loading && (
        <>
          <div style={{ textAlign: "center", fontSize: 48, marginBottom: 4 }}>
            {detail.avatar_emoji}
          </div>
          <h2 style={{ color: "#fff", textAlign: "center", margin: "4px 0 2px" }}>
            {detail.name}
          </h2>
          <div style={{ textAlign: "center", color: "#aaa", fontSize: 13, marginBottom: 12 }}>
            {detail.personality_type} — {detail.personality_title}
          </div>
          <div style={{ textAlign: "center", color: "#9ce0ff", fontSize: 14, marginBottom: 16 }}>
            Настроение: {MOOD_LABELS[detail.mood] ?? detail.mood} ({detail.mood_value})
          </div>

          {detail.description && (
            <div style={{ color: "#ccc", fontSize: 13, marginBottom: 14 }}>
              <strong>Описание:</strong> {detail.description}
            </div>
          )}

          {detail.background && (
            <div style={{ color: "#ccc", fontSize: 13, marginBottom: 14 }}>
              <strong>Предыстория:</strong> {detail.background}
            </div>
          )}

          {/* Воспоминания */}
          <h3 style={{ color: "#9ce0ff", fontSize: 14, marginBottom: 8 }}>
            🧠 Воспоминания
          </h3>
          {detail.memories.length === 0 && (
            <div style={{ color: "#666", fontSize: 12 }}>Пока пусто</div>
          )}
          {detail.memories.map((m) => (
            <div
              key={m.id}
              style={{
                color: "#bbb",
                fontSize: 12,
                padding: "4px 0",
                borderBottom: "1px solid #222",
              }}
            >
              {m.is_key && <span style={{ color: "#ffd35a" }}>★ </span>}
              {m.content}
            </div>
          ))}

          {/* Цели */}
          <h3 style={{ color: "#9ce0ff", fontSize: 14, margin: "16px 0 8px" }}>
            🎯 Цели
          </h3>
          {detail.goals.length === 0 && (
            <div style={{ color: "#666", fontSize: 12 }}>Нет активных целей</div>
          )}
          {detail.goals.map((g) => (
            <div
              key={g.id}
              style={{
                color: "#bbb",
                fontSize: 12,
                padding: "4px 0",
                borderBottom: "1px solid #222",
              }}
            >
              {g.goal}
            </div>
          ))}
        </>
      )}
    </div>
  );
}
