"""
Data Analyst Agent — handles factual queries about transactions.

Responsibilities:
- Answer questions about spending amounts, counts, dates
- Provide category/merchant breakdowns
- Compare periods (month-over-month, year-over-year)
- Calculate income vs expenses
"""
from __future__ import annotations

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent

from app.config import MODEL_FAST, TEMPERATURE, ANTHROPIC_API_KEY
from app.tools import DATA_ANALYST_TOOLS

SYSTEM_PROMPT = """Ти — аналітик даних у фінансовому помічнику мобільного банку.

Твоя роль — відповідати на фактичні запити про витрати користувача.

Правила:
- Завжди використовуй інструменти для отримання реальних даних — НІКОЛИ не вигадуй цифри
- Відповідай конкретними числами: суми, кількість транзакцій, дати
- Якщо запит стосується конкретного періоду — фільтруй за датами
- Для порівняння — використовуй get_monthly_comparison
- Формат відповіді: компактний, з ключовими числами
- Тон: дружній, на "ти"
- Відповідай українською

Приклад хорошої відповіді: "$34 за минулий тиждень — 11 транзакцій, переважно Aroma Kava і Lviv Croissants."
Приклад поганої відповіді: "Ти витрачаєш приблизно $30-40 на каву."
"""


def create_data_analyst():
    """Create the Data Analyst agent."""
    llm = ChatAnthropic(
        model=MODEL_FAST,
        temperature=TEMPERATURE,
        api_key=ANTHROPIC_API_KEY,
        max_tokens=2048,
    )

    agent = create_react_agent(
        model=llm,
        tools=DATA_ANALYST_TOOLS,
        prompt=SystemMessage(content=SYSTEM_PROMPT),
        name="data_analyst",
    )

    return agent
