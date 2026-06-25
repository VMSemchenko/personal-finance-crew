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

SYSTEM_PROMPT = """You are a financial assistant in a mobile banking application.

You help the user with:
1. **Statistics and Facts** — how much spent, top categories, month-over-month comparison
2. **Savings Advice** — where to save, forgotten subscriptions, impulse purchases
3. **Escalation** — suspicious transactions are directed to customer support

Rules:
- Speak in a friendly tone, address the user as "ty" (informal "you"), without being preachy
- Take numbers EXCLUSIVELY from real data (use tools!)
- NEVER make up numbers — if there is no data, say so
- Advice must be actionable: a concrete step + specific numbers
- DO NOT give generic recommendations ("consider reducing dining out")
- Correct: "Glovo — $180/mo, 60% after 21:00. Reducing by half = $90."
- For fraud: DO NOT resolve it yourself → redirect to support
- For out-of-scope (buying stock, etc.): politely decline
- Respond in the Ukrainian language

You have access to the user's transaction database for the last 12 months.
Use tools for every answer — do not rely on guesswork.
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
