"""
Data Analyst Agent — handles factual queries about transactions.

Responsibilities:
- Answer questions about spending amounts, counts, dates
- Provide category/merchant breakdowns
- Compare periods (month-over-month, year-over-year)
- Calculate income vs expenses
"""
from __future__ import annotations

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent

from app.config import MODEL_FAST, TEMPERATURE, GOOGLE_API_KEY
from app.tools import DATA_ANALYST_TOOLS

SYSTEM_PROMPT = """You are a data analyst in the mobile bank financial assistant.

Your role is to answer factual queries about the user's spending.

Rules:
- Always use tools to get real data — NEVER make up numbers
- Answer with specific numbers: amounts, number of transactions, dates
- If the query relates to a specific period — filter by dates
- For comparison — use get_monthly_comparison
- Response format: compact, with key numbers
- Tone: friendly, addressing user as "ty" (informal "you")
- Respond in the Ukrainian language

Example of a good response: "$34 за минулий тиждень — 11 транзакцій, переважно Aroma Kava і Lviv Croissants."
Example of a bad response: "Ти витрачаєш приблизно $30-40 на каву."
"""


def create_data_analyst():
    """Create the Data Analyst agent."""
    llm = ChatGoogleGenerativeAI(
        model=MODEL_FAST,
        temperature=TEMPERATURE,
        google_api_key=GOOGLE_API_KEY,
        max_output_tokens=2048,
    )

    agent = create_react_agent(
        model=llm,
        tools=DATA_ANALYST_TOOLS,
        prompt=SystemMessage(content=SYSTEM_PROMPT),
        name="data_analyst",
    )

    return agent
