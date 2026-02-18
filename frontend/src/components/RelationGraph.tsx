/**
 * Интерактивный SVG-граф отношений между агентами.
 */

import React from "react";
import type { Agent, Relationship, RelationType } from "../types";

interface Props {
  agents: Agent[];
  relationships: Relationship[];
  compact?: boolean;
  onSelectAgent?: (agentId: number) => void;
}

// Позиции узлов по имени (статичные для 5 персонажей)
const NODE_POS: Record<string, { x: number; y: number }> = {
  Мо: { x: 80, y: 60 },
  Роки: { x: 300, y: 60 },
  Фыр: { x: 80, y: 240 },
  Феликс: { x: 300, y: 240 },
  Лея: { x: 190, y: 380 },
};

function getEdgeColor(type: RelationType, strength: number): string {
  if (type === "напряжение") {
    if (strength >= 70) return "#ff8a3d";
    if (strength >= 45) return "#ffd35a";
    return "#66dd8f";
  }
  if (strength >= 70) return "#57f163";
  if (strength >= 45) return "#73baff";
  return "#b38cff";
}

export default function RelationGraph({ agents, relationships, compact, onSelectAgent }: Props) {
  // Дедупликация рёбер (оставляем самое сильное на пару)
  const edgeMap = new Map<string, Relationship>();
  relationships.forEach((r) => {
    const key = [r.agent_from_id, r.agent_to_id].sort().join("-");
    const prev = edgeMap.get(key);
    if (!prev || r.display_strength > prev.display_strength) {
      edgeMap.set(key, r);
    }
  });
  const edges = Array.from(edgeMap.values());

  // Карта id → agent
  const byId = new Map(agents.map((a) => [a.id, a]));

  // Динамические позиции: если агент не в NODE_POS, расставим по кругу
  const posMap = new Map<number, { x: number; y: number }>();
  let extraIndex = 0;
  agents.forEach((a) => {
    const fixed = NODE_POS[a.name];
    if (fixed) {
      posMap.set(a.id, fixed);
    } else {
      const angle = ((2 * Math.PI) / (agents.length - Object.keys(NODE_POS).length || 1)) * extraIndex;
      posMap.set(a.id, {
        x: 190 + Math.cos(angle) * 140,
        y: 220 + Math.sin(angle) * 140,
      });
      extraIndex++;
    }
  });

  return (
    <div
      style={{
        background: "rgba(30,30,40,0.85)",
        borderRadius: compact ? 12 : 16,
        border: "1px solid #333",
        padding: compact ? "10px 12px" : "14px 16px",
        flex: 1,
        display: "flex",
        flexDirection: "column",
        minHeight: 0,
        overflow: "hidden",
      }}
    >
      <div style={{ fontWeight: 700, fontSize: 15, color: "#fff", marginBottom: 8 }}>
        Граф отношений
      </div>

      <svg viewBox="0 0 380 440" style={{ width: "100%", flex: 1, minHeight: 0 }}>
        {/* Рёбра */}
        {edges.map((edge) => {
          const from = posMap.get(edge.agent_from_id);
          const to = posMap.get(edge.agent_to_id);
          if (!from || !to) return null;
          const color = getEdgeColor(edge.relation_type, edge.display_strength);
          const midX = (from.x + to.x) / 2;
          const midY = (from.y + to.y) / 2;
          return (
            <g key={edge.id}>
              <line
                x1={from.x}
                y1={from.y}
                x2={to.x}
                y2={to.y}
                stroke={color}
                strokeWidth={Math.max(2, edge.display_strength / 20)}
                strokeLinecap="round"
                opacity={0.7}
              />
              <text
                x={midX}
                y={midY - 8}
                fill={color}
                textAnchor="middle"
                fontSize={10}
                fontWeight={600}
              >
                {edge.relation_type}
              </text>
            </g>
          );
        })}

        {/* Узлы */}
        {agents.map((agent) => {
          const pos = posMap.get(agent.id);
          if (!pos) return null;
          return (
            <g
              key={agent.id}
              style={{ cursor: "pointer" }}
              onClick={() => onSelectAgent?.(agent.id)}
            >
              <circle cx={pos.x} cy={pos.y} r={26} fill="#2a2a3a" stroke="#555" strokeWidth={1.5} />
              <text
                x={pos.x}
                y={pos.y + 8}
                textAnchor="middle"
                fontSize={24}
              >
                {agent.avatar_emoji}
              </text>
              <text
                x={pos.x}
                y={pos.y + 42}
                textAnchor="middle"
                fill="#ccc"
                fontSize={12}
                fontWeight={600}
              >
                {agent.name}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
