/**
 * Хук для WebSocket-подключения к backend.
 * Автоматический реконнект, буфер событий.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import type { WSMessage } from "../types";

const RECONNECT_DELAY = 3000; // мс

export function useWebSocket(url: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(url);

    ws.onopen = () => {
      setConnected(true);
      console.log("[WS] Подключено");
    };

    ws.onmessage = (ev) => {
      try {
        const msg: WSMessage = JSON.parse(ev.data);
        setLastMessage(msg);
      } catch {
        console.warn("[WS] Невалидное сообщение", ev.data);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      console.log("[WS] Отключено, реконнект через", RECONNECT_DELAY, "мс");
      reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY);
    };

    ws.onerror = (err) => {
      console.error("[WS] Ошибка", err);
      ws.close();
    };

    wsRef.current = ws;
  }, [url]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { connected, lastMessage };
}
