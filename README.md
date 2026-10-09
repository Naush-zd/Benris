## Setup

Install `uv`, then create the project environment and install its dependencies:

```sh
uv sync
```

Run the desktop assistant with:

```sh
uv sync && uv run python jarvis.py
```

Put the required settings in the project root `.env` file:

```dotenv
GROQ_API_KEY=your-groq-key
ANTHROPIC_API_KEY=your-proxy-key
ANTHROPIC_BASE_URL=https://your-anthropic-proxy.example.com
CLAUDE_MODEL=claude-sonnet-4-5
```

Groq is used first when `GROQ_API_KEY` is set. If it fails, the assistant
falls back to Claude Sonnet 4.5 through `ANTHROPIC_BASE_URL`. If Groq is not
configured, Claude is used directly. Override the model ID with
`CLAUDE_MODEL` when your proxy uses a dated model name.

The assistant uses the operating system's default microphone and prefers a
natural system voice when available. To choose a specific device, set
`BENRIS_MICROPHONE_INDEX` or `BENRIS_VOICE_INDEX` to a zero-based index. The
active microphone and voice are shown in the UI.

On this Mac, the built-in microphone is index `1` and Samantha is voice index
`139`:

```sh
export BENRIS_MICROPHONE_INDEX=1
export BENRIS_VOICE_INDEX=139
```

The PyQt5 UI starts the Python voice backend in the same process. The `.env`
file is loaded automatically.

## Agent Runtime MVP

Start the local control plane:

```sh
uv run agentctl start
```

The API exposes `GET /health`, task creation at `POST /tasks`, task state and
events at `GET /tasks/{id}`, and pause/resume/stop/approve/reject controls.
Connect a dashboard to `ws://127.0.0.1:8000/ws/events` for the live event stream.
The first runtime uses the existing Benris agent; browser, terminal, and file
tools will be added behind the policy engine next.
