import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"


def asset_path(filename: str) -> str:
    return str(PROJECT_ROOT / filename)