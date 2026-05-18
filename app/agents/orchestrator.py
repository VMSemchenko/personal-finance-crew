"""
Orchestrator — Supervisor agent that routes queries to specialized agents.

Uses LangGraph's supervisor pattern to:
1. Classify incoming query
2. Route to appropriate specialist agent(s)
3. For multi-step queries, coordinate multiple agents sequentially
4. Return final synthesized response
"""
from __future__ import annotations

import time
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langgraph_supervisor import create_supervisor

from app.config import MODEL_FAST, TEMPERATURE, ANTHROPIC_API_KEY
from app.agents.data_analyst import create_data_analyst
from app.agents.savings_advisor import create_savings_advisor
from app.agents.escalation import create_escalation_agent


SUPERVISOR_PROMPT = """Ти — головний координатор фінансового помічника мобільного банку.

У тебе є 3 спеціалізовані агенти:

1. **data_analyst** — для фактичних запитів про витрати:
   - "Скільки витратив на каву?"
   - "Топ-5 категорій витрат"
   - "Загальні витрати за місяць"
   - Порівняння періодів

2. **savings_advisor** — для порад щодо економії:
   - "Де можна зекономити?"
   - "Які підписки зайві?"
   - "Як виплатити кредитну картку?"
   - Аналіз патернів витрат

3. **escalation** — для fraud та out-of-scope:
   - Підозрілі транзакції / fraud
   - "Купи акції" (out of scope)
   - Будь-що, що потребує служби підтримки

Правила маршрутизації:
- Для простих фактичних запитів → data_analyst
- Для порад щодо економії → savings_advisor
- Для fraud/підозрілих транзакцій → escalation
- Для запитів поза скоупом → escalation
- Для multi-step запитів (порівняння + поради) → спочатку data_analyst, потім savings_advisor
- Якщо запит неоднозначний — data_analyst як default

ВАЖЛИВО: Передавай запит відповідному агенту БЕЗ модифікації. Не відповідай сам — завжди делегуй.
"""


def create_crew():
    """Create the multi-agent crew with supervisor orchestrator."""
    # Create specialist agents
    data_analyst = create_data_analyst()
    savings_advisor = create_savings_advisor()
    escalation = create_escalation_agent()

    # Create supervisor
    supervisor_llm = ChatAnthropic(
        model=MODEL_FAST,
        temperature=TEMPERATURE,
        api_key=ANTHROPIC_API_KEY,
        max_tokens=1024,
    )

    workflow = create_supervisor(
        agents=[data_analyst, savings_advisor, escalation],
        model=supervisor_llm,
        prompt=SUPERVISOR_PROMPT,
    )

    return workflow.compile()


def run_crew(query: str, history: list[dict] | None = None) -> dict[str, Any]:
    """Run a query through the multi-agent crew.

    Args:
        query: User's question
        history: Optional conversation history

    Returns:
        Dict with 'response', 'latency_ms', 'messages', 'agent_trace'
    """
    crew = create_crew()

    # Build messages
    messages = []
    if history:
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                from langchain_core.messages import AIMessage
                messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=query))

    start = time.time()
    result = crew.invoke({"messages": messages})
    latency_ms = (time.time() - start) * 1000

    # Extract the final response
    final_messages = result.get("messages", [])
    response_text = ""
    agent_trace = []

    for msg in final_messages:
        agent_name = getattr(msg, "name", None) or msg.__class__.__name__
        agent_trace.append({
            "agent": agent_name,
            "type": msg.__class__.__name__,
            "content": str(msg.content)[:500] if hasattr(msg, "content") else "",
        })
        # The last AI message with real content is our response
        if hasattr(msg, "content") and msg.content and msg.__class__.__name__ == "AIMessage":
            response_text = msg.content

    return {
        "response": response_text,
        "latency_ms": round(latency_ms, 1),
        "messages": final_messages,
        "agent_trace": agent_trace,
    }
