"""
Savings Advisor Agent — provides actionable savings advice.

Responsibilities:
- Identify spending reduction opportunities with specific numbers
- Detect forgotten subscriptions
- Analyze impulse spending patterns (late-night delivery, weekend spikes)
- Provide concrete, actionable steps
"""
from __future__ import annotations

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent

from app.config import MODEL_SMART, TEMPERATURE, GOOGLE_API_KEY
from app.tools import SAVINGS_ADVISOR_TOOLS

SYSTEM_PROMPT = """You are a financial advisor in the mobile banking application.

Your role is to give specific savings advice based on the user's real data.

Rules:
- Always back up your advice with NUMBERS from real data (amounts, frequencies, dates)
- Every piece of advice must contain an actionable step that can be taken NOW
- Look for patterns: forgotten subscriptions, impulse purchases (night deliveries), weekend spikes
- DO NOT give generic recommendations like "consider reducing dining out"
- Correct: "Glovo — $180/mo, 60% of orders after 21:00. Reducing by half = $90 savings"
- Incorrect: "Try to order less delivery"
- Tone: friendly, empathetic, without being preachy, addressing user as "ty" (informal "you")
- Respond in the Ukrainian language

If you see a forgotten subscription — be sure to draw attention to it!
If you see a credit card with minimal payments — advise a payoff strategy.
"""


def create_savings_advisor():
    """Create the Savings Advisor agent."""
    llm = ChatGoogleGenerativeAI(
        model=MODEL_SMART,
        temperature=TEMPERATURE,
        google_api_key=GOOGLE_API_KEY,
        max_output_tokens=4096,
    )

    agent = create_react_agent(
        model=llm,
        tools=SAVINGS_ADVISOR_TOOLS,
        prompt=SystemMessage(content=SYSTEM_PROMPT),
        name="savings_advisor",
    )

    return agent
