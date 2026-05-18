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

# LLM Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Model selection — use cheaper models for routing/simple tasks
MODEL_FAST = "claude-haiku-4-20250414"       # Routing, simple queries
MODEL_SMART = "claude-sonnet-4-20250514"     # Complex reasoning, advice

# LangSmith
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", "")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "personal-finance-crew")

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
