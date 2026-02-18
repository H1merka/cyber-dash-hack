/**
 * Карточка агента: эмодзи-аватар, имя, настроение, тип личности.
 */

import React from "react";
import type { Agent, Mood } from "../types";
import { MOOD_LABELS } from "../types";

const MOOD_COLORS: Record<Mood, string> = {
  счастлив: "#4ade80",
  грустный: "#60a5fa",
  злой: "#f87171",
  нейтральный: "#a3a3a3",
  напуган: "#c084fc",
};

interface Props {
  agent: Agent;
  selected?: boolean;
  compact?: boolean;
  onClick?: () => void;
}

export default function AgentCard({ agent, selected, compact, onClick }: Props) {
  const borderColor = selected ? "#fff" : MOOD_COLORS[agent.mood] ?? "#555";

  return (
    <div
      onClick={onClick}
      style={{
        background: "rgba(10,40,25,0.85)",
        borderRadius: compact ? 12 : 16,
        border: `2px solid ${borderColor}`,
        padding: compact ? "8px 12px" : "14px 18px",
        cursor: "pointer",
        minWidth: compact ? 110 : 160,
        flexShrink: 0,
        transition: "border-color 0.2s, transform 0.15s",
        transform: selected ? "scale(1.04)" : undefined,
      }}
    >
      <div style={{ fontSize: compact ? 24 : 36, textAlign: "center", marginBottom: compact ? 2 : 4 }}>
        {agent.avatar_emoji}
      </div>
      <div
        style={{
          textAlign: "center",
          fontWeight: 700,
          fontSize: compact ? 13 : 16,
          color: "#fff",
          marginBottom: 2,
        }}
      >
        {agent.name}
      </div>
      <div
        style={{
          textAlign: "center",
          fontSize: compact ? 11 : 13,
          color: MOOD_COLORS[agent.mood] ?? "#aaa",
          marginBottom: compact ? 0 : 4,
        }}
      >
        {MOOD_LABELS[agent.mood] ?? agent.mood}
      </div>
      {!compact && (
        <div
          style={{
            textAlign: "center",
            fontSize: 11,
            color: "#888",
          }}
        >
          {agent.personality_type} — {agent.personality_title}
        </div>
      )}
    </div>
  );
}
