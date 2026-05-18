"""
Evaluation runner — runs golden set through both architectures and collects metrics.

Can be run standalone or from Streamlit UI.
Integrates with LangSmith for tracing when API key is available.
"""
from __future__ import annotations

import json
import time
from typing import Any

from app.eval.golden_set import get_golden_set
from app.eval.evaluators import evaluate_success, evaluate_groundedness, evaluate_tool_selection
from app.agents.orchestrator import run_crew
from app.baseline.single_agent import run_baseline


def run_single_eval(
    test_case: dict,
    architecture: str = "crew",
) -> dict[str, Any]:
    """Run a single test case through specified architecture.

    Args:
        test_case: Golden set test case dict
        architecture: "crew" or "baseline"

    Returns:
        Dict with response, metrics, and evaluation scores
    """
    query = test_case["query"]
    start = time.time()

    if architecture == "crew":
        result = run_crew(query)
        tool_calls = []  # Extract from trace
        for item in result.get("agent_trace", []):
            if "tool" in item.get("type", "").lower():
                tool_calls.append({"tool": item.get("agent", "unknown")})
    else:
        result = run_baseline(query)
        tool_calls = result.get("tool_calls", [])

    total_time = (time.time() - start) * 1000

    response = result.get("response", "")

    # Run evaluators
    success_eval = evaluate_success(
        query, response, test_case["expected_behavior"]
    )
    groundedness_eval = evaluate_groundedness(query, response)
    tool_eval = evaluate_tool_selection(
        query, tool_calls, test_case.get("ground_truth_hint", "")
    )

    return {
        "test_id": test_case["id"],
        "category": test_case["category"],
        "query": query,
        "architecture": architecture,
        "response": response,
        "latency_ms": result.get("latency_ms", total_time),
        "success_score": success_eval.get("score", 0),
        "success_reasoning": success_eval.get("reasoning", ""),
        "groundedness_score": groundedness_eval.get("score", 0),
        "groundedness_reasoning": groundedness_eval.get("reasoning", ""),
        "tool_selection_score": tool_eval.get("score", 0),
        "tool_selection_reasoning": tool_eval.get("reasoning", ""),
        "tool_calls": tool_calls,
    }


def run_full_eval(
    architectures: list[str] | None = None,
) -> list[dict]:
    """Run full golden set evaluation on specified architectures.

    Args:
        architectures: List of architectures to test. Default: ["crew", "baseline"]

    Returns:
        List of evaluation results for all test cases and architectures
    """
    if architectures is None:
        architectures = ["crew", "baseline"]

    golden_set = get_golden_set()
    results = []

    for arch in architectures:
        print(f"\n{'='*60}")
        print(f"Running evaluation: {arch}")
        print(f"{'='*60}")

        for i, tc in enumerate(golden_set, 1):
            print(f"\n[{i}/{len(golden_set)}] {tc['id']}: {tc['query'][:60]}...")
            try:
                result = run_single_eval(tc, arch)
                results.append(result)
                print(f"  ✓ Success: {result['success_score']:.1f} | "
                      f"Grounded: {result['groundedness_score']:.1f} | "
                      f"Tools: {result['tool_selection_score']:.1f} | "
                      f"Latency: {result['latency_ms']:.0f}ms")
            except Exception as e:
                print(f"  ✗ Error: {e}")
                results.append({
                    "test_id": tc["id"],
                    "category": tc["category"],
                    "query": tc["query"],
                    "architecture": arch,
                    "response": f"ERROR: {e}",
                    "latency_ms": 0,
                    "success_score": 0,
                    "groundedness_score": 0,
                    "tool_selection_score": 0,
                    "error": str(e),
                })

    return results


def summarize_results(results: list[dict]) -> dict:
    """Summarize evaluation results by architecture.

    Returns:
        Dict with summary statistics per architecture
    """
    summary = {}

    for arch in ["crew", "baseline"]:
        arch_results = [r for r in results if r["architecture"] == arch]
        if not arch_results:
            continue

        latencies = [r["latency_ms"] for r in arch_results if r["latency_ms"] > 0]
        success_scores = [r["success_score"] for r in arch_results]
        groundedness_scores = [r["groundedness_score"] for r in arch_results]
        tool_scores = [r["tool_selection_score"] for r in arch_results]

        summary[arch] = {
            "total_tests": len(arch_results),
            "avg_success_rate": round(sum(success_scores) / len(success_scores), 3) if success_scores else 0,
            "avg_groundedness": round(sum(groundedness_scores) / len(groundedness_scores), 3) if groundedness_scores else 0,
            "avg_tool_selection": round(sum(tool_scores) / len(tool_scores), 3) if tool_scores else 0,
            "latency_p50_ms": round(sorted(latencies)[len(latencies) // 2], 1) if latencies else 0,
            "latency_p95_ms": round(sorted(latencies)[int(len(latencies) * 0.95)], 1) if latencies else 0,
            "avg_latency_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0,
            "errors": sum(1 for r in arch_results if "error" in r),
            # By category
            "by_category": {},
        }

        for cat in ["facts", "advice", "multi_step", "edge"]:
            cat_results = [r for r in arch_results if r["category"] == cat]
            if cat_results:
                cat_success = [r["success_score"] for r in cat_results]
                summary[arch]["by_category"][cat] = {
                    "count": len(cat_results),
                    "avg_success": round(sum(cat_success) / len(cat_success), 3),
                }

    return summary


if __name__ == "__main__":
    print("Running full golden set evaluation...")
    results = run_full_eval()

    print("\n\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    summary = summarize_results(results)
    print(json.dumps(summary, indent=2))

    # Save results
    from pathlib import Path
    output_dir = Path(__file__).parent.parent.parent / "report"
    output_dir.mkdir(exist_ok=True)

    with open(output_dir / "eval_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    with open(output_dir / "eval_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nResults saved to {output_dir}")
