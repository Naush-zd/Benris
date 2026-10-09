"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import {
  useAgent,
  statusLabels,
  terminalStates,
  type Turn,
} from "@/lib/agent-context";
import { VoiceMode } from "@/components/VoiceMode";

const suggestions = [
  {
    title: "Summarize a build",
    text: "Check my latest GitHub build and explain any failures.",
  },
  {
    title: "Research a topic",
    text: "Research the latest on local-first AI agents and summarize.",
  },
  {
    title: "Draft a plan",
    text: "Draft a step-by-step plan to migrate a service to Postgres.",
  },
  {
    title: "Explain a concept",
    text: "Explain in one sentence why human approval matters for AI agents.",
  },
];

function TurnView({ turn, isLive }: { turn: Turn; isLive: boolean }) {
  const { control } = useAgent();
  const running = turn.state === "running" || turn.state === "created";
  const waiting = turn.state === "waiting_approval";
  const canControl = ["running", "paused", "waiting_approval"].includes(turn.state);
  const actions = turn.events.filter((event) => event.type === "ACTION_PERFORMED");

  return (
    <div className="turn">
      <div className="msg">
        <span className="msg-avatar user">K</span>
        <div className="msg-body">
          <div className="msg-name">You</div>
          <div className="msg-text">{turn.prompt}</div>
        </div>
      </div>

      <div className="msg">
        <span className="msg-avatar agent">B</span>
        <div className="msg-body">
          <div className="msg-name">Benris</div>
          {actions.length > 0 && (
            <ul className="action-list">
              {actions.map((event) => (
                <li
                  className={`action-item ${event.data.ok === false ? "failed" : ""}`}
                  key={`${event.timestamp}-${event.data.action}`}
                >
                  <span className="action-tag">{String(event.data.action)}</span>
                  <span>{event.message}</span>
                </li>
              ))}
            </ul>
          )}
          {turn.response ? (
            <div className="msg-text">{turn.response}</div>
          ) : running ? (
            <div className="thinking">
              Thinking
              <span className="dots">
                <i />
                <i />
                <i />
              </span>
            </div>
          ) : (
            <div className="msg-text">
              {turn.state === "cancelled"
                ? "Task stopped."
                : turn.state === "failed"
                  ? "The agent could not complete this task."
                  : "Waiting..."}
            </div>
          )}
        </div>
      </div>

      {waiting && (
        <div className="approval">
          <span className="approval-icon">!</span>
          <div>
            <strong>Approval required</strong>
            <p>The agent wants to perform an action. Review it before continuing.</p>
          </div>
          <div className="approval-actions">
            <button className="control-btn danger" onClick={() => void control("reject")}>
              Reject
            </button>
            <button className="control-btn approve" onClick={() => void control("approve")}>
              Approve
            </button>
          </div>
        </div>
      )}

      {isLive && (
        <div className="turn-meta">
          <span className={`status-pill ${turn.state}`}>
            <i />
            {statusLabels[turn.state]}
          </span>
          {canControl && (
            <>
              <button
                className="control-btn"
                disabled={!["running", "paused"].includes(turn.state)}
                onClick={() => void control(turn.state === "paused" ? "resume" : "pause")}
              >
                {turn.state === "paused" ? "▶ Resume" : "Ⅱ Pause"}
              </button>
              <button className="control-btn danger" onClick={() => void control("stop")}>
                ■ Stop
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default function Home() {
  const { turns, liveTurn, submitting, submitTask, connected } = useAgent();
  const [prompt, setPrompt] = useState("");
  const [voiceOpen, setVoiceOpen] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const voiceLauncherRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const node = scrollRef.current;
    if (node) node.scrollTop = node.scrollHeight;
  }, [turns]);

  useEffect(() => {
    const node = textareaRef.current;
    if (!node) return;
    node.style.height = "auto";
    node.style.height = `${Math.min(node.scrollHeight, 200)}px`;
  }, [prompt]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!prompt.trim() || submitting) return;
    const value = prompt;
    setPrompt("");
    await submitTask(value);
  }

  function onKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (prompt.trim() && !submitting) {
        const value = prompt;
        setPrompt("");
        void submitTask(value);
      }
    }
  }

  const empty = turns.length === 0;

  function closeVoiceMode() {
    setVoiceOpen(false);
    window.requestAnimationFrame(() => voiceLauncherRef.current?.focus());
  }

  return (
    <div className="chat">
      <div className="chat-scroll" ref={scrollRef}>
        <div className="chat-inner">
          {empty ? (
            <div className="hero">
              <span className="hero-badge">Human-controlled agents</span>
              <h1>What should Benris do?</h1>
              <p>Give your agent a task. Watch every move. Stay in control.</p>
              <div className="suggestions">
                {suggestions.map((item) => (
                  <button
                    key={item.title}
                    className="suggestion"
                    onClick={() => setPrompt(item.text)}
                  >
                    <strong>{item.title}</strong>
                    {item.text}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            turns.map((turn) => (
              <TurnView
                key={turn.id}
                turn={turn}
                isLive={!terminalStates.has(turn.state) && liveTurn?.id === turn.id}
              />
            ))
          )}
        </div>
      </div>

      <div className="composer-wrap">
        <form className="composer" onSubmit={onSubmit}>
          <button
            ref={voiceLauncherRef}
            type="button"
            className="voice-launch"
            onClick={() => setVoiceOpen(true)}
            aria-label="Open voice mode"
            title="Voice mode"
          >
            🎙
          </button>
          <textarea
            ref={textareaRef}
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            onKeyDown={onKeyDown}
            placeholder={connected ? "Message Benris..." : "Start the daemon to begin..."}
            rows={1}
            aria-label="Task prompt"
          />
          <button
            className="send-btn"
            type="submit"
            disabled={submitting || !prompt.trim()}
            aria-label="Send task"
          >
            ↑
          </button>
        </form>
        <p className="composer-hint">
          Benris can inspect, reason, and ask before acting. Press Enter to send, Shift+Enter for a new line.
        </p>
      </div>

      {voiceOpen && <VoiceMode onClose={closeVoiceMode} />}
    </div>
  );
}
