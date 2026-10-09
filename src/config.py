import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL")
if ANTHROPIC_BASE_URL and ANTHROPIC_BASE_URL.rstrip("/").endswith("localhost:6655"):
    ANTHROPIC_BASE_URL = f"{ANTHROPIC_BASE_URL.rstrip('/')}/anthropic"
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")


def asset_path(filename: str) -> str:
    return str(PROJECT_ROOT / filename)