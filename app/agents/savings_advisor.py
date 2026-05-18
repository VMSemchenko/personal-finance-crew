"""
Savings Advisor Agent — provides actionable savings advice.

Responsibilities:
- Identify spending reduction opportunities with specific numbers
- Detect forgotten subscriptions
- Analyze impulse spending patterns (late-night delivery, weekend spikes)
- Provide concrete, actionable steps
"""
from __future__ import annotations

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent

from app.config import MODEL_SMART, TEMPERATURE, ANTHROPIC_API_KEY
from app.tools import SAVINGS_ADVISOR_TOOLS

SYSTEM_PROMPT = """Ти — фінансовий радник у мобільному банківському застосунку.

Твоя роль — давати конкретні поради щодо економії, базовані на реальних даних користувача.

Правила:
- Завжди підтверджуй поради ЧИСЛАМИ з реальних даних (суми, частоти, дати)
- Кожна порада повинна містити actionable крок, який можна зробити ЗАРАЗ
- Шукай патерни: забуті підписки, імпульсні покупки (нічні замовлення), weekend spikes
- НЕ давай generic рекомендації типу "consider reducing dining out"
- Правильно: "Glovo — $180/міс, 60% замовлень після 21:00. Зменшення вдвічі = $90 економії"
- Неправильно: "Спробуй менше замовляти доставку"
- Тон: дружній, емпатичний, без менторства, на "ти"
- Відповідай українською

Якщо бачиш забуту підписку — обов'язково звернути увагу!
Якщо бачиш кредитну картку з мінімальними платежами — порадити стратегію виплати.
"""


def create_savings_advisor():
    """Create the Savings Advisor agent."""
    llm = ChatAnthropic(
        model=MODEL_SMART,
        temperature=TEMPERATURE,
        api_key=ANTHROPIC_API_KEY,
        max_tokens=4096,
    )

    agent = create_react_agent(
        model=llm,
        tools=SAVINGS_ADVISOR_TOOLS,
        prompt=SystemMessage(content=SYSTEM_PROMPT),
        name="savings_advisor",
    )

    return agent
