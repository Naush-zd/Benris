"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export type TaskState =
  | "created"
  | "running"
  | "paused"
  | "waiting_approval"
  | "completed"
  | "failed"
  | "cancelled";

export type RuntimeEvent = {
  session_id: string;
  type: string;
  message: string;
  timestamp: string;
  data: Record<string, string | number | boolean>;
};

export type Turn = {
  id: string;
  taskId: string | null;
  prompt: string;
  state: TaskState;
  response: string | null;
  events: RuntimeEvent[];
  createdAt: string;
};

export type ControlAction = "pause" | "resume" | "stop" | "approve" | "reject";

type AgentContextValue = {
  connected: boolean;
  turns: Turn[];
  liveTurn: Turn | undefined;
  lastTurn: Turn | undefined;
  submitting: boolean;
  notice: string;
  submitTask: (prompt: string) => Promise<string | null>;
  control: (action: ControlAction) => Promise<void>;
  reset: () => void;
};

const API_URL =
  process.env.NEXT_PUBLIC_CONTROL_PLANE_URL ?? "http://127.0.0.1:8000";
export const terminalStates = new Set<TaskState>([
  "completed",
  "failed",
  "cancelled",
]);

export const statusLabels: Record<TaskState, string> = {
  created: "Queued",
  running: "Running",
  paused: "Paused",
  waiting_approval: "Approval needed",
  completed: "Completed",
  failed: "Failed",
  cancelled: "Stopped",
};

const AgentContext = createContext<AgentContextValue | null>(null);

function extractResponse(events: RuntimeEvent[], fallback: string | null) {
  const latest = events.filter((event) => event.type === "AGENT_RESPONSE").at(-1);
  return latest?.message ?? fallback;
}

export function AgentProvider({ children }: { children: ReactNode }) {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [connected, setConnected] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [notice, setNotice] = useState(
    "Enter a task to start a controlled agent session.",
  );

  const liveTurn = useMemo(
    () => turns.find((turn) => turn.taskId && !terminalStates.has(turn.state)),
    [turns],
  );
  const lastTurn = turns.at(-1);
  const sessionKey = liveTurn?.taskId
    ? `${liveTurn.taskId}:${liveTurn.state}`
    : "";

  const patchTurn = useCallback(
    (taskId: string, patch: Partial<Turn>) =>
      setTurns((prev) =>
        prev.map((turn) =>
          turn.taskId === taskId ? { ...turn, ...patch } : turn,
        ),
      ),
    [],
  );

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`${API_URL}/health`);
        setConnected(response.ok);
      } catch {
        setConnected(false);
      }
    };
    void checkHealth();
    const interval = window.setInterval(checkHealth, 5000);
    return () => window.clearInterval(interval);
  }, []);

  useEffect(() => {
    const [taskId, taskState] = sessionKey.split(":");
    if (!taskId || !taskState || terminalStates.has(taskState as TaskState)) {
      return;
    }
    const socketUrl = API_URL.replace(/^http/, "ws") + "/ws/events";
    const socket = new WebSocket(socketUrl);
    socket.onmessage = (message) => {
      const event = JSON.parse(message.data) as RuntimeEvent;
      if (event.session_id !== taskId) return;
      setTurns((prev) =>
        prev.map((turn) => {
          if (turn.taskId !== taskId) return turn;
          const exists = turn.events.some(
            (item) =>
              item.timestamp === event.timestamp && item.type === event.type,
          );
          const events = exists ? turn.events : [...turn.events, event];
          return { ...turn, events, response: extractResponse(events, turn.response) };
        }),
      );
    };
    return () => socket.close();
  }, [sessionKey]);

  useEffect(() => {
    const [taskId, taskState] = sessionKey.split(":");
    if (!taskId || !taskState || terminalStates.has(taskState as TaskState)) {
      return;
    }
    let cancelled = false;
    const refresh = async () => {
      try {
        const response = await fetch(`${API_URL}/tasks/${taskId}`, {
          cache: "no-store",
        });
        if (response.status === 404) {
          if (!cancelled) {
            patchTurn(taskId, { state: "cancelled" });
            setNotice("That task session expired. Start a new task.");
          }
          return;
        }
        if (!response.ok || cancelled) return;
        const data = (await response.json()) as {
          id: string;
          task: string;
          state: TaskState;
          events: RuntimeEvent[];
        };
        patchTurn(taskId, {
          state: data.state,
          events: data.events,
          response: extractResponse(data.events, null),
        });
      } catch {
        setNotice("The daemon stopped responding.");
      }
    };
    void refresh();
    const interval = window.setInterval(refresh, 1500);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [sessionKey, patchTurn]);

  const submitTask = useCallback(async (prompt: string) => {
    const trimmed = prompt.trim();
    if (!trimmed) return null;
    setSubmitting(true);
    setNotice("Starting a new agent session...");
    const localId = `turn-${Date.now()}`;
    try {
      const response = await fetch(`${API_URL}/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: trimmed }),
      });
      if (!response.ok) throw new Error("Task could not be created");
      const task = (await response.json()) as {
        id: string;
        task: string;
        state: TaskState;
      };
      setTurns((prev) => [
        ...prev,
        {
          id: localId,
          taskId: task.id,
          prompt: trimmed,
          state: task.state,
          response: null,
          events: [],
          createdAt: new Date().toISOString(),
        },
      ]);
      setNotice("Agent session started. Events stream in live.");
      return localId;
    } catch {
      setNotice(
        "Could not reach the Benris daemon. Start it with `uv run agentctl start`.",
      );
      return null;
    } finally {
      setSubmitting(false);
    }
  }, []);

  const control = useCallback(
    async (action: ControlAction) => {
      const taskId = liveTurn?.taskId;
      if (!taskId) return;
      const response = await fetch(`${API_URL}/tasks/${taskId}/${action}`, {
        method: "POST",
      });
      if (response.ok) {
        const task = (await response.json()) as { state: TaskState };
        patchTurn(taskId, { state: task.state });
      }
    },
    [liveTurn?.taskId, patchTurn],
  );

  const reset = useCallback(() => {
    setTurns([]);
    setNotice("Enter a task to start a controlled agent session.");
  }, []);

  const value = useMemo<AgentContextValue>(
    () => ({
      connected,
      turns,
      liveTurn,
      lastTurn,
      submitting,
      notice,
      submitTask,
      control,
      reset,
    }),
    [
      connected,
      turns,
      liveTurn,
      lastTurn,
      submitting,
      notice,
      submitTask,
      control,
      reset,
    ],
  );

  return <AgentContext.Provider value={value}>{children}</AgentContext.Provider>;
}

export function useAgent() {
  const context = useContext(AgentContext);
  if (!context) {
    throw new Error("useAgent must be used within an AgentProvider");
  }
  return context;
}

export function formatTime(value: string) {
  return new Intl.DateTimeFormat("en", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(value));
}

export function shortId(value: string) {
  return value.slice(0, 8).toUpperCase();
}
