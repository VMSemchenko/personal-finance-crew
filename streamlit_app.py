"""
Streamlit UI for Personal Finance Coach demo.

Features:
- Query input with architecture selector (crew / baseline)
- Response display with expandable trace
- Eval tab: run golden set, show results table
"""
from __future__ import annotations

import json
import time
import streamlit as st
import pandas as pd
from pathlib import Path

# Ensure DB exists
DB_PATH = Path(__file__).parent / "data" / "finance.db"
if not DB_PATH.exists():
    from data.init_db import init_db
    init_db()

from app.agents.orchestrator import run_crew
from app.baseline.single_agent import run_baseline
from app.eval.golden_set import get_golden_set
from app.eval.run_eval import run_single_eval, summarize_results


# ── Page Config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="💰 Personal Finance Coach",
    page_icon="💰",
    layout="wide",
)

# ── Sidebar ──────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Settings")

    architecture = st.radio(
        "Architecture",
        options=["crew", "baseline"],
        format_func=lambda x: "🤖 Multi-Agent Crew" if x == "crew" else "📝 Single Agent Baseline",
        help="Compare multi-agent (LangGraph) vs single-agent (plain SDK) approaches",
    )

    st.divider()
    st.markdown("""
    **Multi-Agent Crew** (LangGraph)
    - 🔍 Data Analyst (Gemini Flash)
    - 💡 Savings Advisor (Gemini Pro)
    - 🚨 Escalation (Gemini Flash)
    - 🎯 Supervisor Router (Gemini Flash)

    **Single Agent Baseline** (Google GenAI SDK)
    - One Gemini Pro agent with all tools
    """)

    st.divider()
    st.caption("Lesson 11 — AI Agents & Tool Orchestration")


# ── Tabs ─────────────────────────────────────────────────────────────
tab_chat, tab_eval = st.tabs(["💬 Chat", "📊 Evaluation"])


# ── Chat Tab ─────────────────────────────────────────────────────────
with tab_chat:
    st.title("💰 Personal Finance Coach")
    st.caption(f"Architecture: {'Multi-Agent Crew' if architecture == 'crew' else 'Single Agent Baseline'}")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about your finances..."):
        # Display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    history = st.session_state.messages[:-1]  # exclude current

                    if architecture == "crew":
                        result = run_crew(prompt, history if history else None)
                    else:
                        result = run_baseline(prompt, history if history else None)

                    response = result.get("response", "Sorry, something went wrong.")
                    st.markdown(response)

                    # Show trace in expander
                    with st.expander("🔍 Trace", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Latency", f"{result.get('latency_ms', 0):.0f} ms")
                        with col2:
                            if "usage" in result:
                                usage = result["usage"]
                                st.metric("Tokens", f"{usage.get('input_tokens', 0) + usage.get('output_tokens', 0)}")

                        if architecture == "crew":
                            st.subheader("Agent Trace")
                            for step in result.get("agent_trace", []):
                                agent = step.get("agent", "unknown")
                                msg_type = step.get("type", "")
                                content = step.get("content", "")[:300]
                                if content.strip():
                                    st.markdown(f"**{agent}** ({msg_type})")
                                    st.code(content, language=None)
                        else:
                            st.subheader("Tool Calls")
                            for tc in result.get("tool_calls", []):
                                st.markdown(f"🔧 **{tc.get('tool', 'unknown')}**")
                                st.json(tc.get("input", {}))

                    st.session_state.messages.append({"role": "assistant", "content": response})

                except Exception as e:
                    st.error(f"Error: {e}")
                    import traceback
                    st.code(traceback.format_exc())

    # Clear chat button
    if st.session_state.messages:
        if st.button("🗑️ Clear Chat", type="secondary"):
            st.session_state.messages = []
            st.rerun()


# ── Eval Tab ─────────────────────────────────────────────────────────
with tab_eval:
    st.title("📊 Golden Set Evaluation")
    st.markdown("Run the golden set (17 test cases) through both architectures and compare results.")

    # Show golden set
    golden_set = get_golden_set()

    with st.expander("📋 Golden Set Test Cases", expanded=False):
        df_golden = pd.DataFrame([
            {
                "ID": tc["id"],
                "Category": tc["category"],
                "Query": tc["query"],
                "Expected": tc["expected_behavior"],
            }
            for tc in golden_set
        ])
        st.dataframe(df_golden, use_container_width=True, hide_index=True)

    # Run evaluation
    col1, col2 = st.columns(2)
    with col1:
        run_crew_eval = st.button("🚀 Run Crew Eval", type="primary")
    with col2:
        run_baseline_eval = st.button("🚀 Run Baseline Eval", type="primary")

    if "eval_results" not in st.session_state:
        st.session_state.eval_results = []

    if run_crew_eval or run_baseline_eval:
        arch = "crew" if run_crew_eval else "baseline"
        progress = st.progress(0, text=f"Running {arch} evaluation...")

        for i, tc in enumerate(golden_set):
            progress.progress((i + 1) / len(golden_set), text=f"[{i+1}/{len(golden_set)}] {tc['id']}")
            try:
                result = run_single_eval(tc, arch)
                # Remove old result for same test_id + arch
                st.session_state.eval_results = [
                    r for r in st.session_state.eval_results
                    if not (r["test_id"] == tc["id"] and r["architecture"] == arch)
                ]
                st.session_state.eval_results.append(result)
            except Exception as e:
                st.error(f"Error on {tc['id']}: {e}")

        progress.empty()
        st.success(f"✅ {arch} evaluation complete!")

    # Display results
    if st.session_state.eval_results:
        results = st.session_state.eval_results
        summary = summarize_results(results)

        st.subheader("Summary")
        cols = st.columns(len(summary))
        for i, (arch, stats) in enumerate(summary.items()):
            with cols[i]:
                st.markdown(f"### {'🤖 Crew' if arch == 'crew' else '📝 Baseline'}")
                st.metric("Success Rate", f"{stats['avg_success_rate']:.1%}")
                st.metric("Groundedness", f"{stats['avg_groundedness']:.1%}")
                st.metric("Tool Selection", f"{stats['avg_tool_selection']:.1%}")
                st.metric("P50 Latency", f"{stats['latency_p50_ms']:.0f} ms")
                st.metric("P95 Latency", f"{stats['latency_p95_ms']:.0f} ms")

        st.subheader("Detailed Results")
        df = pd.DataFrame([
            {
                "ID": r["test_id"],
                "Category": r["category"],
                "Arch": r["architecture"],
                "Query": r["query"][:60] + "...",
                "Success": f"{r['success_score']:.1f}",
                "Grounded": f"{r['groundedness_score']:.1f}",
                "Tools": f"{r['tool_selection_score']:.1f}",
                "Latency (ms)": f"{r['latency_ms']:.0f}",
            }
            for r in results
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Response details
        st.subheader("Response Details")
        for r in results:
            with st.expander(f"{r['architecture']} | {r['test_id']} — {r['query'][:50]}..."):
                st.markdown(f"**Response:**\n\n{r['response']}")
                st.markdown(f"**Success:** {r['success_score']:.1f} — {r.get('success_reasoning', '')}")
                st.markdown(f"**Groundedness:** {r['groundedness_score']:.1f} — {r.get('groundedness_reasoning', '')}")
                st.markdown(f"**Tool Selection:** {r['tool_selection_score']:.1f} — {r.get('tool_selection_reasoning', '')}")
