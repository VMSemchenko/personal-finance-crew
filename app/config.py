"""
Application configuration and settings.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "finance.db"

# LLM Configuration — Google Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# Model selection — use cheaper models for routing/simple tasks
MODEL_FAST = "gemini-2.5-flash"          # Routing, simple queries (fast & cheap)
MODEL_SMART = "gemini-2.5-pro"           # Complex reasoning, advice

# Langfuse
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

# Agent configuration
MAX_AGENT_STEPS = 10
TEMPERATURE = 0.1

# System prompts
SYSTEM_TONE = """Ти — фінансовий помічник у мобільному банківському застосунку.
Правила:
- Говори дружньо, на "ти", без менторства
- У стресових темах (борги, fraud) — емпатично
- Числа бери ВИКЛЮЧНО з реальних даних користувача
- НЕ вигадуй цифри — якщо даних немає, скажи про це
- Поради повинні бути actionable: конкретний крок, який можна зробити зараз
- Відповідай українською мовою
"""
