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
  onClick?: () => void;
}

export default function AgentCard({ agent, selected, onClick }: Props) {
  const borderColor = selected ? "#fff" : MOOD_COLORS[agent.mood] ?? "#555";

  return (
    <div
      onClick={onClick}
      style={{
        background: "rgba(30,30,40,0.85)",
        borderRadius: 16,
        border: `2px solid ${borderColor}`,
        padding: "14px 18px",
        cursor: "pointer",
        minWidth: 160,
        transition: "border-color 0.2s, transform 0.15s",
        transform: selected ? "scale(1.04)" : undefined,
      }}
    >
      <div style={{ fontSize: 36, textAlign: "center", marginBottom: 4 }}>
        {agent.avatar_emoji}
      </div>
      <div
        style={{
          textAlign: "center",
          fontWeight: 700,
          fontSize: 16,
          color: "#fff",
          marginBottom: 2,
        }}
      >
        {agent.name}
      </div>
      <div
        style={{
          textAlign: "center",
          fontSize: 13,
          color: MOOD_COLORS[agent.mood] ?? "#aaa",
          marginBottom: 4,
        }}
      >
        {MOOD_LABELS[agent.mood] ?? agent.mood}
      </div>
      <div
        style={{
          textAlign: "center",
          fontSize: 11,
          color: "#888",
        }}
      >
        {agent.personality_type} — {agent.personality_title}
      </div>
    </div>
  );
}
