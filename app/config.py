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
SYSTEM_TONE = """You are a financial assistant in a mobile banking application.
Rules:
- Speak in a friendly tone, address the user as "ty" (informal "you"), without being preachy
- Be empathetic in stressful topics (debts, fraud)
- Take numbers EXCLUSIVELY from the user's real data
- DO NOT make up numbers — if there is no data, say so
- Advice must be actionable: a concrete step that can be taken now
- Respond in the Ukrainian language
"""
