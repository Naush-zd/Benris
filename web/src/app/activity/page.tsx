"use client";

import { useAgent, formatTime, statusLabels, shortId } from "@/lib/agent-context";

export default function ActivityPage() {
  const { turns, liveTurn, lastTurn, connected } = useAgent();
  const focus = liveTurn ?? lastTurn;
  const events = focus?.events ?? [];
  const totalEvents = turns.reduce((sum, turn) => sum + turn.events.length, 0);

  return (
    <div className="content">
      <div className="page-head">
        <h1>Activity</h1>
        <p>Live agent lifecycle, decisions, and execution events.</p>
      </div>

      <div className="metric-row">
        <div className="metric">
          <small>Device status</small>
          <strong>{connected ? "Online" : "Waiting"}</strong>
          <span className="sub">Local MacBook runtime</span>
        </div>
        <div className="metric">
          <small>Active session</small>
          <strong>{focus?.taskId ? shortId(focus.taskId) : "—"}</strong>
          <span className="sub">{focus ? statusLabels[focus.state] : "No active session"}</span>
        </div>
        <div className="metric">
          <small>Events</small>
          <strong>{totalEvents}</strong>
          <span className="sub">{turns.length} task{turns.length === 1 ? "" : "s"} total</span>
        </div>
      </div>

      <div className="panel">
        <div className="panel-head">
          <h2>Execution log</h2>
          <span className="live-tag">
            <i />
            {liveTurn ? "LIVE" : "IDLE"}
          </span>
        </div>
        {events.length ? (
          <div className="event-list">
            {events.map((event, index) => (
              <div className="event-row" key={`${event.timestamp}-${event.type}-${index}`}>
                <span className="event-time">{formatTime(event.timestamp)}</span>
                <span
                  className={`event-marker ${
                    event.type.includes("FAILED")
                      ? "failure"
                      : event.type.includes("COMPLETED")
                        ? "complete"
                        : ""
                  }`}
                />
                <span className="event-message">
                  <strong>{event.type.replaceAll("_", " ").toLowerCase()}</strong>
                  <small>{event.message}</small>
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty">
            <div className="empty-mark">◷</div>
            Start a task to see the agent lifecycle and live execution events.
          </div>
        )}
      </div>
    </div>
  );
}
