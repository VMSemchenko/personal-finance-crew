"""
Tool definitions for both multi-agent crew and single-agent baseline.

Each tool wraps a database query and returns formatted results.
Tools are defined as LangChain tools for LangGraph compatibility,
and also converted to Gemini function declarations for the baseline.
"""
from __future__ import annotations

import json
from langchain_core.tools import tool

from app import database as db


# ── Data Query Tools ─────────────────────────────────────────────────

@tool
def query_transactions(
    category: str | None = None,
    merchant: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    account: str | None = None,
    limit: int = 50,
) -> str:
    """Query user transactions with optional filters.

    Args:
        category: Filter by category (coffee, groceries, delivery, etc.)
        merchant: Filter by merchant name (exact match)
        date_from: Start date (ISO format, e.g. 2025-06-01)
        date_to: End date (ISO format, e.g. 2025-06-30)
        account: Filter by account (main_debit or credit_card)
        limit: Max number of transactions to return (default 50)

    Returns:
        JSON list of matching transactions with date, merchant, amount, category
    """
    results = db.get_transactions(
        category=category, merchant=merchant,
        date_from=date_from, date_to=date_to,
        account=account, limit=limit,
    )
    return json.dumps(results, ensure_ascii=False)


@tool
def get_category_summary(
    date_from: str | None = None,
    date_to: str | None = None,
) -> str:
    """Get spending summary grouped by category for a time period.

    Args:
        date_from: Start date (ISO format)
        date_to: End date (ISO format)

    Returns:
        JSON list with category, transaction count, total, and average per category
    """
    results = db.get_category_summary(date_from, date_to)
    return json.dumps(results, ensure_ascii=False)


@tool
def get_top_categories(
    n: int = 5,
    date_from: str | None = None,
    date_to: str | None = None,
) -> str:
    """Get top N expense categories ranked by total spending.

    Args:
        n: Number of top categories to return (default 5)
        date_from: Start date (ISO format)
        date_to: End date (ISO format)

    Returns:
        JSON list of top categories with totals
    """
    results = db.get_top_categories(n, date_from, date_to)
    return json.dumps(results, ensure_ascii=False)


@tool
def get_merchant_summary(
    merchant: str,
    date_from: str | None = None,
    date_to: str | None = None,
) -> str:
    """Get detailed spending breakdown for a specific merchant.

    Args:
        merchant: Merchant name (e.g. "Netflix", "Glovo", "ATB")
        date_from: Start date (ISO format)
        date_to: End date (ISO format)

    Returns:
        JSON with merchant stats: count, total, average, first/last transaction
    """
    result = db.get_merchant_summary(merchant, date_from, date_to)
    return json.dumps(result, ensure_ascii=False) if result else "No data found for this merchant"


@tool
def get_subscriptions() -> str:
    """List all recurring subscriptions with their status.

    Returns:
        JSON list of subscriptions with monthly amount, payment count,
        first/last payment dates, and status (active/potentially_forgotten)
    """
    results = db.get_subscriptions()
    return json.dumps(results, ensure_ascii=False)


@tool
def get_monthly_comparison(month1: str, month2: str) -> str:
    """Compare spending between two months.

    Args:
        month1: First month (format: YYYY-MM, e.g. 2025-06)
        month2: Second month (format: YYYY-MM, e.g. 2025-07)

    Returns:
        JSON list showing spending difference by category between the two months
    """
    results = db.get_monthly_comparison(month1, month2)
    return json.dumps(results, ensure_ascii=False)


@tool
def get_time_pattern(category: str | None = None) -> str:
    """Analyze when transactions happen (morning/afternoon/evening/late-night).

    Args:
        category: Optional category to filter (e.g. 'delivery', 'coffee')

    Returns:
        JSON with transaction distribution across time slots
    """
    results = db.get_time_pattern(category)
    return json.dumps(results, ensure_ascii=False)


@tool
def get_weekend_vs_weekday(category: str | None = None) -> str:
    """Compare weekend vs weekday spending patterns.

    Args:
        category: Optional category to filter

    Returns:
        JSON with weekday and weekend spending comparison
    """
    result = db.get_weekend_vs_weekday(category)
    return json.dumps(result, ensure_ascii=False)


@tool
def get_income_vs_expenses(
    date_from: str | None = None,
    date_to: str | None = None,
) -> str:
    """Get total income vs expenses for a period. Useful for calculating net balance.

    Args:
        date_from: Start date (ISO format)
        date_to: End date (ISO format)

    Returns:
        JSON with income, expenses, and net balance
    """
    result = db.get_income_vs_expenses(date_from, date_to)
    return json.dumps(result, ensure_ascii=False)


@tool
def get_savings_potential() -> str:
    """Identify top savings opportunities based on spending patterns.

    Returns:
        JSON list of merchant/category combos with frequency, totals,
        late-night counts, and weekend counts — to identify reduction targets
    """
    results = db.get_savings_potential()
    return json.dumps(results, ensure_ascii=False)


@tool
def check_suspicious_transactions() -> str:
    """Check for suspicious or foreign transactions on credit card.

    Returns:
        JSON list of all credit card transactions that might be suspicious
    """
    results = db.get_suspicious_transactions()
    return json.dumps(results, ensure_ascii=False)


@tool
def get_credit_card_behavior() -> str:
    """Analyze credit card payment patterns (min payments vs full payments).

    Returns:
        JSON list of credit card payments with dates and amounts
    """
    results = db.get_credit_card_behavior()
    return json.dumps(results, ensure_ascii=False)


# ── Tool collections for different agents ────────────────────────────

DATA_ANALYST_TOOLS = [
    query_transactions,
    get_category_summary,
    get_top_categories,
    get_merchant_summary,
    get_monthly_comparison,
    get_income_vs_expenses,
]

SAVINGS_ADVISOR_TOOLS = [
    get_subscriptions,
    get_savings_potential,
    get_time_pattern,
    get_weekend_vs_weekday,
    get_category_summary,
    get_income_vs_expenses,
    get_credit_card_behavior,
]

ESCALATION_TOOLS = [
    check_suspicious_transactions,
    get_credit_card_behavior,
    query_transactions,
]

ALL_TOOLS = [
    query_transactions,
    get_category_summary,
    get_top_categories,
    get_merchant_summary,
    get_subscriptions,
    get_monthly_comparison,
    get_time_pattern,
    get_weekend_vs_weekday,
    get_income_vs_expenses,
    get_savings_potential,
    check_suspicious_transactions,
    get_credit_card_behavior,
]


def execute_tool_by_name(name: str, args: dict) -> str:
    """Execute a tool by name (for baseline agent tool loop)."""
    tool_map = {t.name: t for t in ALL_TOOLS}
    if name not in tool_map:
        return f"Error: Unknown tool '{name}'"
    try:
        return tool_map[name].invoke(args)
    except Exception as e:
        return f"Error executing {name}: {e}"
