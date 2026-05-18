"""
Golden Set — 17 test cases for evaluating the Personal Finance Coach.

Covers three categories:
1. Facts & statistics (queries with verifiable answers)
2. Savings advice (actionable recommendations)
3. Edge cases (fraud, out-of-scope, multi-turn)
"""
from __future__ import annotations

GOLDEN_SET = [
    # ── Category 1: Facts & Statistics ───────────────────────────────
    {
        "id": "fact_01",
        "category": "facts",
        "query": "Скільки витратив на каву у жовтні 2025?",
        "expected_behavior": "Returns exact sum of coffee transactions for October 2025",
        "must_contain": ["category: coffee", "date range: 2025-10"],
        "ground_truth_hint": "Should use query_transactions or get_category_summary with date filter",
    },
    {
        "id": "fact_02",
        "category": "facts",
        "query": "Топ-5 категорій витрат за червень 2025?",
        "expected_behavior": "Returns ranked list of top 5 spending categories for June 2025",
        "must_contain": ["ranked list", "5 categories"],
        "ground_truth_hint": "Should use get_top_categories with date filter",
    },
    {
        "id": "fact_03",
        "category": "facts",
        "query": "Коли був останній платіж за Netflix?",
        "expected_behavior": "Returns exact date of the last Netflix payment",
        "must_contain": ["Netflix", "date"],
        "ground_truth_hint": "Should use get_merchant_summary or query_transactions for Netflix",
    },
    {
        "id": "fact_04",
        "category": "facts",
        "query": "Загальні витрати за березень 2025?",
        "expected_behavior": "Returns total expenses for March 2025",
        "must_contain": ["total", "March 2025"],
        "ground_truth_hint": "Should use get_income_vs_expenses with date range 2025-03-01 to 2025-03-31",
    },
    {
        "id": "fact_05",
        "category": "facts",
        "query": "Скільки разів я замовляв через Glovo?",
        "expected_behavior": "Returns exact count of Glovo transactions",
        "must_contain": ["Glovo", "count"],
        "ground_truth_hint": "Should use get_merchant_summary for Glovo",
    },
    {
        "id": "fact_06",
        "category": "facts",
        "query": "Яка середня сума покупки в ATB?",
        "expected_behavior": "Returns average transaction amount at ATB",
        "must_contain": ["ATB", "average"],
        "ground_truth_hint": "Should use get_merchant_summary for ATB",
    },
    # ── Category 2: Savings Advice ───────────────────────────────────
    {
        "id": "advice_01",
        "category": "advice",
        "query": "Де можна зекономити $200 цього місяця?",
        "expected_behavior": "Provides specific, data-backed savings opportunities totaling ~$200",
        "must_contain": ["specific amounts", "actionable steps"],
        "ground_truth_hint": "Should identify delivery (late-night pattern), Sportlife (forgotten), coffee reduction",
    },
    {
        "id": "advice_02",
        "category": "advice",
        "query": "Які підписки зайві та які я можу відмінити?",
        "expected_behavior": "Lists subscriptions, MUST flag Sportlife as potentially forgotten",
        "must_contain": ["Sportlife", "forgotten/inactive"],
        "ground_truth_hint": "Sportlife last payment ~4 months ago — must be flagged",
    },
    {
        "id": "advice_03",
        "category": "advice",
        "query": "Як швидше виплатити кредитну картку?",
        "expected_behavior": "Analyzes credit card payment pattern, notes minimum payments, suggests strategy",
        "must_contain": ["credit card", "payment pattern", "strategy"],
        "ground_truth_hint": "2 of 3 months minimum $50, 1 of 3 full payment",
    },
    {
        "id": "advice_04",
        "category": "advice",
        "query": "Порадь як зменшити витрати на доставку їжі",
        "expected_behavior": "Identifies late-night delivery pattern, suggests specific reduction",
        "must_contain": ["late-night", "after 21:00", "specific amount"],
        "ground_truth_hint": "~50-60% of delivery orders are after 21:00 — impulse pattern",
    },
    # ── Category 3: Multi-step Analysis ──────────────────────────────
    {
        "id": "multi_01",
        "category": "multi_step",
        "query": "Порівняй витрати вересня і жовтня 2025 — що змінилось?",
        "expected_behavior": "Compares both months category by category, highlights differences",
        "must_contain": ["September", "October", "comparison", "differences"],
        "ground_truth_hint": "Should use get_monthly_comparison",
    },
    {
        "id": "multi_02",
        "category": "multi_step",
        "query": "Чи буде жовтень 2025 закрито у плюс?",
        "expected_behavior": "Calculates income vs expenses for October, gives verdict",
        "must_contain": ["income", "expenses", "net balance"],
        "ground_truth_hint": "Should use get_income_vs_expenses for 2025-10",
    },
    {
        "id": "multi_03",
        "category": "multi_step",
        "query": "Якщо зменшити витрати на доставку вдвічі — яка економія за рік?",
        "expected_behavior": "Calculates current delivery spend, halves it, projects annual savings",
        "must_contain": ["current delivery spend", "projected savings", "annual"],
        "ground_truth_hint": "Should get delivery category total, calculate monthly average, project",
    },
    # ── Category 4: Edge Cases ───────────────────────────────────────
    {
        "id": "edge_01",
        "category": "edge",
        "query": "На моїй карті $703 в Booking.com 15 січня, я не робила цю транзакцію",
        "expected_behavior": "Identifies as potential fraud, does NOT resolve, redirects to support",
        "must_contain": ["fraud", "support", "block card"],
        "ground_truth_hint": "Must escalate, provide card blocking instructions, suggest contacting support",
    },
    {
        "id": "edge_02",
        "category": "edge",
        "query": "Купи акції Apple на $500",
        "expected_behavior": "Politely declines, explains available capabilities",
        "must_contain": ["out of scope", "available features"],
        "ground_truth_hint": "Should explain what the assistant CAN do instead",
    },
    {
        "id": "edge_03",
        "category": "edge",
        "query": "Переведи $100 на картку подруги",
        "expected_behavior": "Politely declines, explains this is outside assistant's capabilities",
        "must_contain": ["cannot transfer", "available features"],
        "ground_truth_hint": "Money transfers are out of scope",
    },
    {
        "id": "edge_04",
        "category": "edge",
        "query": "У мене борг по кредитній картці і я не знаю що робити",
        "expected_behavior": "Empathetic response with data-backed advice on credit card debt",
        "must_contain": ["empathetic", "credit card data", "actionable"],
        "ground_truth_hint": "Should analyze credit card payments, suggest strategy, maintain empathetic tone",
    },
]


def get_golden_set() -> list[dict]:
    """Return the full golden set."""
    return GOLDEN_SET


def get_golden_set_by_category(category: str) -> list[dict]:
    """Return golden set filtered by category."""
    return [tc for tc in GOLDEN_SET if tc["category"] == category]
