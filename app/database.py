"""
Database access layer for transaction queries.
All queries go through this module — no raw SQL elsewhere.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Any

from app.config import DB_PATH


@contextmanager
def get_conn():
    """Context manager for SQLite connections."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def query(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    """Execute a query and return list of dicts."""
    with get_conn() as conn:
        cur = conn.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]


def query_one(sql: str, params: tuple = ()) -> dict[str, Any] | None:
    """Execute a query and return single row or None."""
    rows = query(sql, params)
    return rows[0] if rows else None


# ── Transaction queries ──────────────────────────────────────────────

def get_transactions(
    category: str | None = None,
    merchant: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    account: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """Get transactions with optional filters."""
    conditions = []
    params: list = []

    if category:
        conditions.append("category = ?")
        params.append(category)
    if merchant:
        conditions.append("merchant = ?")
        params.append(merchant)
    if date_from:
        conditions.append("date >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("date <= ?")
        params.append(date_to)
    if account:
        conditions.append("account = ?")
        params.append(account)

    where = " AND ".join(conditions) if conditions else "1=1"
    sql = f"SELECT date, merchant, amount, category, account, recurring FROM transactions WHERE {where} ORDER BY date DESC LIMIT ?"
    params.append(limit)

    return query(sql, tuple(params))


def get_category_summary(
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    """Spending summary by category for a period."""
    conditions = ["amount < 0"]  # expenses only
    params: list = []

    if date_from:
        conditions.append("date >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("date <= ?")
        params.append(date_to)

    where = " AND ".join(conditions)
    sql = f"""
        SELECT
            category,
            COUNT(*) AS tx_count,
            ROUND(SUM(amount), 2) AS total,
            ROUND(AVG(amount), 2) AS avg_amount,
            MIN(amount) AS max_single  -- most negative = largest expense
        FROM transactions
        WHERE {where}
        GROUP BY category
        ORDER BY SUM(amount) ASC
    """
    return query(sql, tuple(params))


def get_top_categories(
    n: int = 5,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    """Top N expense categories by total spend."""
    summary = get_category_summary(date_from, date_to)
    # Filter out income categories
    expenses = [s for s in summary if s["total"] < 0]
    return expenses[:n]


def get_merchant_summary(
    merchant: str,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict | None:
    """Spending breakdown for a specific merchant."""
    conditions = ["merchant = ?"]
    params: list = [merchant]

    if date_from:
        conditions.append("date >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("date <= ?")
        params.append(date_to)

    where = " AND ".join(conditions)
    return query_one(f"""
        SELECT
            merchant,
            COUNT(*) AS tx_count,
            ROUND(SUM(amount), 2) AS total,
            ROUND(AVG(amount), 2) AS avg_amount,
            MIN(date) AS first_tx,
            MAX(date) AS last_tx
        FROM transactions WHERE {where}
    """, tuple(params))


def get_subscriptions() -> list[dict]:
    """List all recurring charges with their status."""
    return query("""
        SELECT
            merchant,
            ROUND(AVG(ABS(amount)), 2) AS monthly_amount,
            COUNT(*) AS payment_count,
            MIN(date) AS first_payment,
            MAX(date) AS last_payment,
            CASE
                WHEN MAX(date) < date('2025-08-01') THEN 'potentially_forgotten'
                ELSE 'active'
            END AS status
        FROM transactions
        WHERE recurring = 1 AND amount < 0
        GROUP BY merchant
        ORDER BY AVG(ABS(amount)) DESC
    """)


def get_monthly_comparison(
    month1: str,
    month2: str,
) -> list[dict]:
    """Compare spending between two months (format: YYYY-MM)."""
    return query("""
        SELECT
            category,
            SUM(CASE WHEN substr(date, 1, 7) = ? THEN amount ELSE 0 END) AS month1_total,
            SUM(CASE WHEN substr(date, 1, 7) = ? THEN amount ELSE 0 END) AS month2_total,
            ROUND(
                SUM(CASE WHEN substr(date, 1, 7) = ? THEN amount ELSE 0 END) -
                SUM(CASE WHEN substr(date, 1, 7) = ? THEN amount ELSE 0 END),
            2) AS difference
        FROM transactions
        WHERE substr(date, 1, 7) IN (?, ?)
        GROUP BY category
        ORDER BY difference ASC
    """, (month1, month2, month2, month1, month1, month2))


def get_time_pattern(category: str | None = None) -> list[dict]:
    """Analyze transaction time patterns (hour distribution)."""
    conditions = ["amount < 0"]
    params: list = []

    if category:
        conditions.append("category = ?")
        params.append(category)

    where = " AND ".join(conditions)
    return query(f"""
        SELECT
            CASE WHEN hour >= 21 THEN 'late_night_21+'
                 WHEN hour >= 18 THEN 'evening_18-21'
                 WHEN hour >= 12 THEN 'afternoon_12-18'
                 ELSE 'morning_before_12'
            END AS time_slot,
            COUNT(*) AS tx_count,
            ROUND(SUM(amount), 2) AS total,
            ROUND(AVG(amount), 2) AS avg_amount
        FROM transactions
        WHERE {where}
        GROUP BY time_slot
        ORDER BY tx_count DESC
    """, tuple(params))


def get_weekend_vs_weekday(category: str | None = None) -> dict:
    """Compare weekend vs weekday spending."""
    conditions = ["amount < 0"]
    params: list = []

    if category:
        conditions.append("category = ?")
        params.append(category)

    where = " AND ".join(conditions)
    result = query(f"""
        SELECT
            is_weekend,
            COUNT(*) AS tx_count,
            ROUND(SUM(amount), 2) AS total,
            ROUND(AVG(amount), 2) AS avg_per_tx
        FROM transactions
        WHERE {where}
        GROUP BY is_weekend
    """, tuple(params))

    return {
        "weekday": next((r for r in result if r["is_weekend"] == 0), {}),
        "weekend": next((r for r in result if r["is_weekend"] == 1), {}),
    }


def get_suspicious_transactions() -> list[dict]:
    """Flag suspicious/foreign transactions on credit card."""
    return query("""
        SELECT date, merchant, amount, category, account
        FROM transactions
        WHERE account = 'credit_card'
        ORDER BY date DESC
    """)


def get_credit_card_behavior() -> list[dict]:
    """Analyze credit card payment patterns."""
    return query("""
        SELECT date, merchant, amount
        FROM transactions
        WHERE category = 'credit_payment'
        ORDER BY date
    """)


def get_income_vs_expenses(
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    """Get total income vs expenses for a period."""
    conditions = []
    params: list = []

    if date_from:
        conditions.append("date >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("date <= ?")
        params.append(date_to)

    where = " AND ".join(conditions) if conditions else "1=1"

    result = query_one(f"""
        SELECT
            ROUND(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 2) AS income,
            ROUND(SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END), 2) AS expenses,
            ROUND(SUM(amount), 2) AS net
        FROM transactions
        WHERE {where}
    """, tuple(params))
    return result or {"income": 0, "expenses": 0, "net": 0}


def get_savings_potential() -> list[dict]:
    """Identify top savings opportunities based on patterns."""
    return query("""
        SELECT
            category,
            merchant,
            COUNT(*) AS frequency,
            ROUND(SUM(amount), 2) AS total,
            ROUND(AVG(amount), 2) AS avg_amount,
            SUM(CASE WHEN hour >= 21 THEN 1 ELSE 0 END) AS late_night_count,
            SUM(CASE WHEN is_weekend = 1 THEN 1 ELSE 0 END) AS weekend_count
        FROM transactions
        WHERE amount < 0
        GROUP BY category, merchant
        HAVING COUNT(*) >= 3
        ORDER BY SUM(amount) ASC
        LIMIT 20
    """)
