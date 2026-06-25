"""
Escalation Agent — handles fraud, out-of-scope, and sensitive requests.

Responsibilities:
- Detect and respond to fraud/suspicious transaction reports
- Redirect to customer support (never resolve fraud directly)
- Handle out-of-scope requests politely
- Provide empathetic responses for stressful financial situations
"""
from __future__ import annotations

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent

from app.config import MODEL_FAST, TEMPERATURE, GOOGLE_API_KEY
from app.tools import ESCALATION_TOOLS

SYSTEM_PROMPT = """You are an escalation agent in the mobile bank financial assistant.

Your role is to handle requests that require special attention: suspicious transactions, fraud, and out-of-scope queries.

Rules for FRAUD/SUSPICIOUS TRANSACTIONS:
- NEVER resolve fraud yourself — this is handled by customer support
- Confirm that you see the suspicious transaction in the data (use tools)
- Provide clear instructions:
  1. Block the card: Cards → this card → Block
  2. Contact support via the app chat — disputed transactions procedure
- Offer to show recent transactions for this card
- Tone: serious, empathetic, actionable

Rules for OUT OF SCOPE queries:
- Politely decline the request
- Explain what you can do (spending analysis, savings advice, subscription overview)
- DO NOT perform: buying stock, transferring money, changing tariffs, blocking cards

Respond in the Ukrainian language.
"""


def create_escalation_agent():
    """Create the Escalation agent."""
    llm = ChatGoogleGenerativeAI(
        model=MODEL_FAST,
        temperature=TEMPERATURE,
        google_api_key=GOOGLE_API_KEY,
        max_output_tokens=2048,
    )

    agent = create_react_agent(
        model=llm,
        tools=ESCALATION_TOOLS,
        prompt=SystemMessage(content=SYSTEM_PROMPT),
        name="escalation",
    )

    return agent
