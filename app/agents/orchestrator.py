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

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph_supervisor import create_supervisor

from app.config import MODEL_FAST, TEMPERATURE, GOOGLE_API_KEY
from app.agents.data_analyst import create_data_analyst
from app.agents.savings_advisor import create_savings_advisor
from app.agents.escalation import create_escalation_agent


SUPERVISOR_PROMPT = """You are the main coordinator of the mobile bank financial assistant.

You have 3 specialized agents:

1. **data_analyst** — for factual queries about spending:
   - "How much did I spend on coffee?"
   - "Top 5 categories of spending"
   - "Total spending for the month"
   - Period comparison

2. **savings_advisor** — for savings advice:
   - "Where can I save?"
   - "Which subscriptions are extra?"
   - "How to pay off a credit card?"
   - Spending pattern analysis

3. **escalation** — for fraud and out-of-scope requests:
   - Suspicious transactions / fraud
   - "Buy Apple shares" (out of scope)
   - Anything requiring customer support

Routing Rules:
- For simple factual queries → data_analyst
- For savings advice → savings_advisor
- For fraud/suspicious transactions → escalation
- For out-of-scope requests → escalation
- For multi-step queries (comparison + advice) → first data_analyst, then savings_advisor
- If a query is ambiguous → data_analyst as default

IMPORTANT: Pass the request to the appropriate agent WITHOUT modification. Do not answer yourself — always delegate.
"""


def create_crew():
    """Create the multi-agent crew with supervisor orchestrator."""
    # Create specialist agents
    data_analyst = create_data_analyst()
    savings_advisor = create_savings_advisor()
    escalation = create_escalation_agent()

    # Create supervisor
    supervisor_llm = ChatGoogleGenerativeAI(
        model=MODEL_FAST,
        temperature=TEMPERATURE,
        google_api_key=GOOGLE_API_KEY,
        max_output_tokens=1024,
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
            content = msg.content
            # Gemini may return content as list of dicts with 'text' key
            if isinstance(content, list):
                response_text = " ".join(
                    item.get("text", "") if isinstance(item, dict) else str(item)
                    for item in content
                ).strip()
            else:
                response_text = str(content)

    return {
        "response": response_text,
        "latency_ms": round(latency_ms, 1),
        "messages": final_messages,
        "agent_trace": agent_trace,
    }
