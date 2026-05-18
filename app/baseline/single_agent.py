"""
Single-Agent Baseline — plain Anthropic SDK with tool_use loop.

No framework, no LangGraph — just direct API calls with tool use.
This is the baseline to compare against the multi-agent crew.
"""
from __future__ import annotations

import json
import time
from typing import Any

import anthropic

from app.config import ANTHROPIC_API_KEY, MODEL_SMART, TEMPERATURE
from app.tools import get_anthropic_tool_schemas, execute_tool_by_name

SYSTEM_PROMPT = """Ти — фінансовий помічник у мобільному банківському застосунку.

Ти допомагаєш користувачу з:
1. **Статистика та факти** — скільки витрачено, топ категорій, порівняння місяців
2. **Поради щодо економії** — де зекономити, забуті підписки, імпульсні покупки
3. **Ескалація** — підозрілі транзакції направляються до служби підтримки

Правила:
- Говори дружньо, на "ти", без менторства
- Числа бери ВИКЛЮЧНО з реальних даних (використовуй інструменти!)
- НІКОЛИ не вигадуй цифри — якщо даних немає, скажи про це
- Поради повинні бути actionable: конкретний крок + конкретні числа
- НЕ давай generic рекомендації ("consider reducing dining out")
- Правильно: "Glovo — $180/міс, 60% після 21:00. Зменшення вдвічі = $90."
- Для fraud: НЕ вирішуй сам → направляй до служби підтримки
- Для out-of-scope (купівля акцій тощо): ввічливо відхили
- Відповідай українською мовою

Ти маєш доступ до бази транзакцій користувача за 12 місяців.
Використовуй інструменти для кожної відповіді — не покладайся на здогадки.
"""


def run_baseline(query: str, history: list[dict] | None = None) -> dict[str, Any]:
    """Run a query through the single-agent baseline.

    Args:
        query: User's question
        history: Optional conversation history

    Returns:
        Dict with 'response', 'latency_ms', 'tool_calls', 'messages'
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    tools = get_anthropic_tool_schemas()

    # Build messages
    messages = []
    if history:
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": query})

    tool_calls_log = []
    all_messages = list(messages)
    start = time.time()

    # Tool use loop
    max_iterations = 10
    for _ in range(max_iterations):
        response = client.messages.create(
            model=MODEL_SMART,
            max_tokens=4096,
            temperature=TEMPERATURE,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=all_messages,
        )

        # Check if we need to call tools
        if response.stop_reason == "tool_use":
            # Process tool calls
            assistant_content = response.content
            all_messages.append({"role": "assistant", "content": assistant_content})

            tool_results = []
            for block in assistant_content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input
                    tool_id = block.id

                    tool_calls_log.append({
                        "tool": tool_name,
                        "input": tool_input,
                    })

                    result = execute_tool_by_name(tool_name, tool_input)

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": result,
                    })

            all_messages.append({"role": "user", "content": tool_results})

        else:
            # Final response — extract text
            latency_ms = (time.time() - start) * 1000
            response_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    response_text += block.text

            return {
                "response": response_text,
                "latency_ms": round(latency_ms, 1),
                "tool_calls": tool_calls_log,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
            }

    # Fallback if max iterations reached
    latency_ms = (time.time() - start) * 1000
    return {
        "response": "Вибач, не вдалося обробити запит за допустиму кількість кроків.",
        "latency_ms": round(latency_ms, 1),
        "tool_calls": tool_calls_log,
        "usage": {},
    }
