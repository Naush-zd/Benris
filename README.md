## Setup

Install `uv`, then create the project environment and install its dependencies:

```sh
uv sync
```

Run the desktop assistant with:

```sh
uv run python jarvis.py
```

Set the required API keys before starting the assistant:

```sh
export GROQ_API_KEY="your-groq-api-key"
```

The generated `.venv` and `uv.lock` are local project files managed by `uv`.
