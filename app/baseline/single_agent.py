"""
Single-Agent Baseline — plain Google GenAI SDK with function calling loop.

No framework, no LangGraph — just direct API calls with tool use.
This is the baseline to compare against the multi-agent crew.
"""
from __future__ import annotations

import json
import time
from typing import Any

from google import genai
from google.genai import types

from app.config import GOOGLE_API_KEY, MODEL_SMART, TEMPERATURE
from app.tools import ALL_TOOLS, execute_tool_by_name

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


def _build_tool_declarations() -> list:
    """Build Gemini function declarations from LangChain tools."""
    declarations = []
    for t in ALL_TOOLS:
        schema = t.args_schema.model_json_schema() if t.args_schema else {"type": "object", "properties": {}}
        # Clean up schema for Gemini compatibility
        schema.pop("title", None)
        schema.pop("description", None)
        if "properties" in schema:
            for prop in schema["properties"].values():
                prop.pop("title", None)
                # Gemini doesn't support anyOf for optional params — simplify
                if "anyOf" in prop:
                    for variant in prop["anyOf"]:
                        if variant.get("type") != "null":
                            prop["type"] = variant.get("type", "string")
                            break
                    del prop["anyOf"]
                if "default" in prop:
                    del prop["default"]

        declarations.append(types.FunctionDeclaration(
            name=t.name,
            description=t.description or "",
            parameters=schema if schema.get("properties") else None,
        ))
    return declarations


def run_baseline(query: str, history: list[dict] | None = None) -> dict[str, Any]:
    """Run a query through the single-agent baseline.

    Args:
        query: User's question
        history: Optional conversation history

    Returns:
        Dict with 'response', 'latency_ms', 'tool_calls', 'usage'
    """
    client = genai.Client(api_key=GOOGLE_API_KEY)
    tool_declarations = _build_tool_declarations()
    tools = [types.Tool(function_declarations=tool_declarations)]

    # Build contents
    contents = []
    if history:
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg["content"])],
            ))
    contents.append(types.Content(
        role="user",
        parts=[types.Part.from_text(text=query)],
    ))

    tool_calls_log = []
    start = time.time()
    total_tokens = {"input": 0, "output": 0}

    # Tool use loop
    max_iterations = 10
    for _ in range(max_iterations):
        response = client.models.generate_content(
            model=MODEL_SMART,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=tools,
                temperature=TEMPERATURE,
                max_output_tokens=4096,
            ),
        )

        # Track usage
        if response.usage_metadata:
            total_tokens["input"] += response.usage_metadata.prompt_token_count or 0
            total_tokens["output"] += response.usage_metadata.candidates_token_count or 0

        candidate = response.candidates[0]
        parts = candidate.content.parts

        # Check for function calls
        function_calls = [p for p in parts if p.function_call]

        if function_calls:
            # Add model response to contents
            contents.append(candidate.content)

            # Execute each function call and build responses
            function_responses = []
            for part in function_calls:
                fc = part.function_call
                tool_name = fc.name
                tool_args = dict(fc.args) if fc.args else {}

                tool_calls_log.append({
                    "tool": tool_name,
                    "input": tool_args,
                })

                result = execute_tool_by_name(tool_name, tool_args)

                function_responses.append(types.Part.from_function_response(
                    name=tool_name,
                    response={"result": result},
                ))

            # Add function results
            contents.append(types.Content(
                role="user",
                parts=function_responses,
            ))
        else:
            # Final text response
            latency_ms = (time.time() - start) * 1000
            response_text = ""
            for part in parts:
                if part.text:
                    response_text += part.text

            return {
                "response": response_text,
                "latency_ms": round(latency_ms, 1),
                "tool_calls": tool_calls_log,
                "usage": {
                    "input_tokens": total_tokens["input"],
                    "output_tokens": total_tokens["output"],
                },
            }

    # Fallback if max iterations reached
    latency_ms = (time.time() - start) * 1000
    return {
        "response": "Вибач, не вдалося обробити запит за допустиму кількість кроків.",
        "latency_ms": round(latency_ms, 1),
        "tool_calls": tool_calls_log,
        "usage": total_tokens,
    }
