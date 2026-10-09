<div align="center">

# ⬡ BENRIS

### A voice-driven AI assistant that actually controls your Mac — with a native cockpit UI.

[![License: MIT](https://img.shields.io/badge/License-MIT-00E0C7.svg?style=flat-square)](LICENSE)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Built with uv](https://img.shields.io/badge/built%20with-uv-DE5FE9.svg?style=flat-square)](https://github.com/astral-sh/uv)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](CONTRIBUTING.md)

**Talk to it. It listens, thinks, and *does* — opens apps, plays music, searches the web, checks the weather, and answers back out loud.**

[Features](#-features) · [Quick start](#-quick-start) · [Configuration](#-configuration) · [Agent Runtime](#-agent-runtime-mvp) · [Architecture](#-architecture) · [Contributing](#-contributing)

</div>

---

## ✦ What is Benris?

Benris is a hands-free desktop assistant. Press run, speak, and it transcribes your voice, routes the request through a language model with real **system-control tools**, performs the action on your Mac, and speaks the result back. It ships with a **cinematic native cockpit UI** (built on the Native SDK — compiled to a real binary, no browser, no Electron) and a headless **agent runtime** with a live control plane for driving tasks programmatically.

> ⚡ Dual-model brain: **Groq first for speed, Claude as the fallback for depth.**

---

## ✧ Features

| | |
|---|---|
| 🎙️ **Voice in, voice out** | Microphone speech recognition + natural system TTS (`speech_recognition`, `pyttsx3`). |
| 🧠 **Dual-model with fallback** | Groq (`llama-3.3-70b`) handles requests first; if it fails, Claude Sonnet 4.5 takes over seamlessly. |
| 🖥️ **Real system control** | Open sites & apps, play/pause music, change volume, close windows — not instructions, *actual* actions. |
| 🔎 **Web + knowledge tools** | DuckDuckGo, Python execution, and live weather via Open-Meteo. |
| 🌦️ **Live weather** | Ask for any city — geocoded and fetched on the fly, no API key needed. |
| 🪟 **Native cockpit UI** | A frameless dark HUD: pulsing status orb, live audio waveform, role-styled conversation feed, glowing stat tiles. |
| 🤖 **Agent Runtime MVP** | FastAPI control plane with pausable/approvable tasks and a live WebSocket event stream. |
| 🔐 **Policy engine** | Every sensitive action can be gated: allow / deny / require-approval. |

---

## ⚑ Quick start

> **Requirements:** macOS, [`uv`](https://github.com/astral-sh/uv), Python 3.13+. (Microphone & speaker required for voice mode.)

```sh
# 1. Clone
git clone https://github.com/Naush-zd/Benris.git
cd Benris

# 2. Install dependencies into an isolated environment
uv sync

# 3. Add your keys (see Configuration below)
cp .env.example .env
$EDITOR .env

# 4. Talk to Benris
uv run python jarvis.py
```

Then press **Run**, start speaking, and watch the conversation appear.

---

## ⚙ Configuration

Benris reads settings from a `.env` file in the project root (auto-loaded via `python-dotenv`). Copy [`.env.example`](.env.example) and fill in what you need:

```dotenv
# Primary model (fast). Benris uses this first when present.
GROQ_API_KEY=your-groq-key

# Fallback model (Claude). Used if Groq fails, or directly if Groq is unset.
ANTHROPIC_API_KEY=your-anthropic-key
ANTHROPIC_BASE_URL=https://your-anthropic-proxy.example.com   # optional proxy
CLAUDE_MODEL=claude-sonnet-4-5                                 # optional override
```

**Model routing:**
- `GROQ_API_KEY` set → Groq is tried first, Claude is the fallback.
- Only `ANTHROPIC_API_KEY` set → Claude is used directly.
- Neither set → the assistant tells you no model is configured.

**Choosing a microphone & voice** (optional — defaults to the system devices):

```sh
# Zero-based indexes. The active mic & voice are shown in the UI.
export BENRIS_MICROPHONE_INDEX=1
export BENRIS_VOICE_INDEX=139   # e.g. "Samantha" on this Mac
```

---

## 🤖 Agent Runtime MVP

Beyond the voice UI, Benris exposes a local **control plane** for running agent tasks programmatically — with pause, resume, stop, and human-in-the-loop approval.

```sh
uv run agentctl start           # defaults to 127.0.0.1:8000
uv run agentctl start --host 0.0.0.0 --port 9000
```

### HTTP API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Liveness check. |
| `POST` | `/tasks` | Submit a task — `{ "prompt": "..." }`. Returns a session id. |
| `GET` | `/tasks/{id}` | Current state + full event history. |
| `POST` | `/tasks/{id}/pause` | Pause a running task. |
| `POST` | `/tasks/{id}/resume` | Resume a paused task. |
| `POST` | `/tasks/{id}/stop` | Request cancellation. |
| `POST` | `/tasks/{id}/approve` | Approve a gated action. |
| `POST` | `/tasks/{id}/reject` | Reject a gated action. |
| `GET` | `/policy/{action}` | Ask the policy engine what would happen for an action. |
| `WS` | `/ws/events` | Live event stream (`ws://127.0.0.1:8000/ws/events`). |

### Example

```sh
# Submit a task
curl -s -X POST http://127.0.0.1:8000/tasks \
  -H 'content-type: application/json' \
  -d '{"prompt": "what is the weather in Berlin?"}'

# Watch events live
websocat ws://127.0.0.1:8000/ws/events
```

**Session lifecycle:** `CREATED → RUNNING → (PAUSED | WAITING_APPROVAL) → COMPLETED | CANCELLED`. Every transition emits a typed `RuntimeEvent` on the stream.

---

## ◈ Architecture

```
            ┌──────────────────────────┐        ┌──────────────────────────┐
            │   Native Cockpit UI       │        │   Agent Runtime (API)     │
            │  app.zon · core.ts        │        │  agentctl → FastAPI       │
            │  app.native (dark HUD)    │        │  /tasks · /ws/events      │
            └────────────┬─────────────┘        └────────────┬─────────────┘
                         │ spawns & streams                   │
                         │ stdout line prefixes               │ TaskManager
                         ▼                                    ▼
            ┌─────────────────────────────────────────────────────────────┐
            │                    Benris Agent Core                          │
            │   assistant.py  —  Groq → Claude fallback (phidata Agent)     │
            │   tools: SystemControl · DuckDuckGo · Python · Weather        │
            │   speech.py  —  listen() / speak()                            │
            │   security/policy.py  —  allow / deny / approve               │
            └─────────────────────────────────────────────────────────────┘
```

| Path | Role |
|------|------|
| `jarvis.py` | Entry point. |
| `src/assistant.py` | Agent factory + Groq/Claude fallback + the listen→think→act→speak worker loop. |
| `src/speech.py` | Microphone recognition and text-to-speech. |
| `src/tools.py` | `SystemControlTools` — macOS actions the agent can call. |
| `src/weather.py` | Open-Meteo geocoding + current conditions. |
| `src/config.py` | Loads `.env`, resolves model/API settings. |
| `src/api/` | `agentctl` CLI + FastAPI server. |
| `src/runtime/` | `TaskManager`, `TaskSession`, executor — pause/resume/approval state machine. |
| `src/core/events.py` | Thread-safe event log + live subscriber queues. |
| `src/security/policy.py` | Action policy engine (`allow` / `deny` / `require_approval`). |
| `core.ts` · `app.native` · `app.zon` | Native SDK cockpit frontend. |

---

## ⟡ The Native cockpit UI

The frontend is authored for the [Native SDK](https://native-sdk.dev) — a TypeScript app core (`core.ts`) plus declarative markup (`app.native`), compiled ahead-of-time to a native binary (no JS runtime ships). It launches the Python backend and parses its streamed status lines (`TRANSCRIPT:`, `Assistant:`, `VOICE:`, `MICROPHONE:`, `Listening…`) into a live conversation feed, an animated waveform, and a pulsing status orb.

```sh
native dev        # live-reload the cockpit UI
native check      # typecheck the core + validate every binding
native test       # build the model contract and run core tests
```

---

## ⚐ Roadmap

- [ ] Browser, terminal, and file tools behind the policy engine
- [ ] Wire the native cockpit directly to a headless backend (replace the legacy PyQt shell)
- [ ] Streaming responses in the UI
- [ ] Cross-platform system control (Linux / Windows)
- [ ] A web dashboard for the agent runtime event stream

See the [open issues](https://github.com/Naush-zd/Benris/issues) for the current list.

---

## ⚑ Contributing

Contributions are welcome! Please read **[CONTRIBUTING.md](CONTRIBUTING.md)** and our **[Code of Conduct](CODE_OF_CONDUCT.md)** before opening a PR.

```sh
uv sync                 # install everything
uv run python jarvis.py # run the app
native check            # validate the native UI
```

---

## ⚖ License

Benris is open source under the **[MIT License](LICENSE)**. Do what you like — just keep the copyright notice.

<div align="center">

---

**Built with 🎙️ + 🧠 by [Nausheen Noor Zaidi](https://github.com/Naush-zd)**

*If Benris saved you a few clicks, drop a ⭐ — it genuinely helps.*

</div>
