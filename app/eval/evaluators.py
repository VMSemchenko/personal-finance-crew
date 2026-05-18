"""
Custom evaluators for LangSmith Experiments.

Three evaluators:
1. success_rate — LLM judge: does the response correctly address the query?
2. tool_selection_accuracy — Were the right tools called?
3. groundedness — Are numbers in the response traceable to real data?
"""
from __future__ import annotations

import json
import anthropic

from app.config import ANTHROPIC_API_KEY, MODEL_FAST


def _llm_judge(prompt: str) -> dict:
    """Run an LLM judge evaluation."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=MODEL_FAST,
        max_tokens=512,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract score from text
        score = 1.0 if any(w in text.lower() for w in ["pass", "correct", "yes", "true"]) else 0.0
        return {"score": score, "reasoning": text}


def evaluate_success(query: str, response: str, expected_behavior: str) -> dict:
    """Evaluate if the response successfully addresses the query.

    Returns:
        Dict with 'score' (0.0-1.0) and 'reasoning'
    """
    prompt = f"""You are evaluating a financial assistant's response. 
Judge whether the response correctly and helpfully addresses the user's query.

USER QUERY: {query}

EXPECTED BEHAVIOR: {expected_behavior}

ASSISTANT RESPONSE: {response}

Evaluate on these criteria:
1. Does the response address the query? (not off-topic)
2. Does it match the expected behavior?
3. Is the tone appropriate (friendly, empathetic where needed)?
4. Does it contain specific data rather than generic advice?

Return a JSON object with:
- "score": float 0.0 to 1.0 (1.0 = perfect, 0.0 = complete failure)
- "reasoning": brief explanation of score

Return ONLY valid JSON, no other text."""

    return _llm_judge(prompt)


def evaluate_groundedness(query: str, response: str) -> dict:
    """Evaluate if numbers in the response are grounded in real data.

    Returns:
        Dict with 'score' (0.0-1.0) and 'reasoning'
    """
    prompt = f"""You are evaluating whether a financial assistant's response contains 
hallucinated numbers or if all numerical claims appear grounded.

USER QUERY: {query}

ASSISTANT RESPONSE: {response}

Check:
1. Does the response contain specific numbers (amounts, counts, dates)?
2. Do the numbers seem precise (not round estimates)?
3. Are there any obvious contradictions or impossible values?
4. Does the response acknowledge when data is unavailable rather than guessing?

Return a JSON object with:
- "score": float 0.0 to 1.0 (1.0 = all numbers appear grounded, 0.0 = obvious hallucinations)
- "reasoning": brief explanation
- "numbers_found": list of numerical claims in the response

Return ONLY valid JSON, no other text."""

    return _llm_judge(prompt)


def evaluate_tool_selection(query: str, tool_calls: list[dict], expected_hint: str) -> dict:
    """Evaluate if the agent selected appropriate tools.

    Returns:
        Dict with 'score' (0.0-1.0) and 'reasoning'
    """
    tools_used = [tc.get("tool", tc.get("name", "unknown")) for tc in tool_calls] if tool_calls else []

    prompt = f"""You are evaluating whether a financial assistant selected the right tools for a query.

USER QUERY: {query}

EXPECTED APPROACH: {expected_hint}

TOOLS ACTUALLY USED: {json.dumps(tools_used)}

Available tools: query_transactions, get_category_summary, get_top_categories, 
get_merchant_summary, get_subscriptions, get_monthly_comparison, get_time_pattern, 
get_weekend_vs_weekday, get_income_vs_expenses, get_savings_potential, 
check_suspicious_transactions, get_credit_card_behavior

Evaluate:
1. Were the right tools chosen for this query?
2. Were unnecessary tools called?
3. Were any critical tools missed?

Return a JSON object with:
- "score": float 0.0 to 1.0 (1.0 = perfect tool selection)
- "reasoning": brief explanation

Return ONLY valid JSON, no other text."""

    return _llm_judge(prompt)
