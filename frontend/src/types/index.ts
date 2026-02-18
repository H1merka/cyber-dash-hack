/**
 * TypeScript типы для «Виртуального мира».
 */

// ── Настроение ──────────────────────────────────────────────────────

export type Mood = "счастлив" | "грустный" | "злой" | "нейтральный" | "напуган";

export const MOOD_LABELS: Record<Mood, string> = {
  счастлив: "Счастлив",
  грустный: "Грустный",
  злой: "Злой",
  нейтральный: "Нейтральный",
  напуган: "Напуган",
};

// ── Типы отношений ──────────────────────────────────────────────────

export type RelationType =
  | "друзья"
  | "напряжение"
  | "забота"
  | "уважение"
  | "нейтральные";

// ── Агент ───────────────────────────────────────────────────────────

export interface Agent {
  id: number;
  name: string;
  mood: Mood;
  personality_type: string;
  personality_title: string;
  description?: string;
  avatar_emoji: string;
  mood_value: number;
}

export interface AgentDetail extends Agent {
  background?: string;
  memories: Memory[];
  goals: Goal[];
}

// ── Память ──────────────────────────────────────────────────────────

export interface Memory {
  id: number;
  content: string;
  is_key: boolean;
  timestamp: string;
}

// ── Цели ────────────────────────────────────────────────────────────

export interface Goal {
  id: number;
  goal: string;
  status: "active" | "completed" | "abandoned";
}

// ── Отношения ───────────────────────────────────────────────────────

export interface Relationship {
  id: number;
  agent_from_id: number;
  agent_to_id: number;
  relation_type: RelationType;
  strength: number;
  display_strength: number;
  from_name?: string;
  to_name?: string;
}

// ── Событие ─────────────────────────────────────────────────────────

export interface EventItem {
  id: number;
  content: string;
  created_at: string;
  actor_name: string | null;
  target_name: string | null;
  mood_after: Mood | null;
  relation_type: RelationType | null;
  relation_delta: number;
}

// ── WebSocket-сообщения ─────────────────────────────────────────────

export type WSMessageType = "event" | "mood_update" | "relation_update";

export interface WSMessage {
  type: WSMessageType;
  data: Record<string, unknown>;
}

export interface MoodUpdateData {
  agent_id: number;
  mood: Mood;
  mood_value: number;
}
