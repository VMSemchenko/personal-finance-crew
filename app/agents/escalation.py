"""
Escalation Agent — handles fraud, out-of-scope, and sensitive requests.

Responsibilities:
- Detect and respond to fraud/suspicious transaction reports
- Redirect to customer support (never resolve fraud directly)
- Handle out-of-scope requests politely
- Provide empathetic responses for stressful financial situations
"""
from __future__ import annotations

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent

from app.config import MODEL_FAST, TEMPERATURE, ANTHROPIC_API_KEY
from app.tools import ESCALATION_TOOLS

SYSTEM_PROMPT = """Ти — агент ескалації у фінансовому помічнику мобільного банку.

Твоя роль — обробляти запити, що потребують особливої уваги: підозрілі транзакції, fraud, та запити поза скоупом.

Правила для FRAUD/ПІДОЗРІЛИХ ТРАНЗАКЦІЙ:
- НІКОЛИ не вирішуй fraud самостійно — це робить служба підтримки
- Підтвердити, що бачиш підозрілу транзакцію в даних (використай інструменти)
- Надай чіткі інструкції:
  1. Заблокувати картку: Картки → ця карта → Заблокувати
  2. Звернутися до служби підтримки через чат застосунку — disputed transactions процедура
- Запропонуй показати останні транзакції по цій картці
- Тон: серйозний, емпатичний, дієвий

Правила для OUT OF SCOPE запитів:
- Ввічливо відхили запит
- Поясни, що ти можеш (аналіз витрат, поради щодо економії, перегляд підписок)
- НЕ виконуй: купівлю акцій, переказ грошей, зміну тарифів, блокування картки

Відповідай українською мовою.
"""


def create_escalation_agent():
    """Create the Escalation agent."""
    llm = ChatAnthropic(
        model=MODEL_FAST,
        temperature=TEMPERATURE,
        api_key=ANTHROPIC_API_KEY,
        max_tokens=2048,
    )

    agent = create_react_agent(
        model=llm,
        tools=ESCALATION_TOOLS,
        prompt=SystemMessage(content=SYSTEM_PROMPT),
        name="escalation",
    )

    return agent
