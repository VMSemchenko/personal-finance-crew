# Personal Finance Coach 💰

**Lesson 11 — AI Agents & Tool Orchestration**

Multi-agent система "Personal Finance Coach" — команда спеціалізованих AI-агентів для аналізу витрат, порад щодо економії та обробки edge cases (fraud, out-of-scope).

## Architecture

```
┌──────────────────────────────────────────┐
│           Streamlit UI                   │
│  ┌─────────────┐  ┌──────────────────┐   │
│  │  Chat Tab   │  │   Eval Tab       │   │
│  └──────┬──────┘  └────────┬─────────┘   │
└─────────┼──────────────────┼─────────────┘
          │                  │
    ┌─────▼─────┐      ┌────▼─────┐
    │ crew /    │      │ Golden   │
    │ baseline  │      │ Set Eval │
    └─────┬─────┘      └──────────┘
          │
  ┌───────┴───────┐
  │               │
  ▼               ▼
┌─────────┐  ┌──────────┐
│  Crew   │  │ Baseline │
│ (Lang-  │  │ (plain   │
│  Graph) │  │  SDK)    │
└────┬────┘  └────┬─────┘
     │            │
     ▼            ▼
┌─────────────────────┐
│   Shared Tools      │
│   (12 tools)        │
└────────┬────────────┘
         │
         ▼
┌─────────────────┐
│    SQLite DB    │
│  (842 txns)     │
└─────────────────┘
```

### Multi-Agent Crew (LangGraph)
| Agent | Model | Role |
|-------|-------|------|
| Supervisor | Haiku | Route queries to specialists |
| Data Analyst | Haiku | Facts & statistics about spending |
| Savings Advisor | Sonnet | Actionable savings advice |
| Escalation | Haiku | Fraud & out-of-scope handling |

### Single-Agent Baseline (Anthropic SDK)
- One Sonnet agent with all 12 tools
- Plain `tool_use` loop — no framework

## Setup

```bash
# 1. Clone
git clone https://github.com/VMSemchenko/personal-finance-crew.git
cd personal-finance-crew

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 5. Initialize database
python data/init_db.py

# 6. Run Streamlit app
streamlit run streamlit_app.py
```

## Evaluation

Run the golden set (17 test cases) through both architectures:

```bash
python -m app.eval.run_eval
```

Results are saved to `report/eval_results.json`.

Or use the Streamlit UI → "Evaluation" tab for interactive comparison.

## Golden Set Categories

| Category | Count | Description |
|----------|-------|-------------|
| Facts | 6 | Verifiable spending queries |
| Advice | 4 | Actionable savings recommendations |
| Multi-step | 3 | Complex analysis requiring multiple tools |
| Edge cases | 4 | Fraud, out-of-scope, sensitive topics |

## Data

842 synthetic transactions over 12 months (Dec 2024 — Nov 2025). Key patterns:
- ☕ Coffee ritual: $80-95/month, weekday mornings
- 🏋️ Forgotten subscription: Sportlife $15/month, inactive 4+ months
- 🌙 Late-night delivery: ~50% of delivery orders after 21:00
- 📅 Weekend spike: ~50% higher avg transaction on weekends
- 💳 Credit card: mostly minimum payments ($50)
- 🚨 Suspicious foreign transactions on credit card

## Tech Stack

- **Python 3.11+**
- **LangGraph** — multi-agent supervisor orchestration
- **Anthropic SDK** — single-agent baseline
- **Claude Haiku** — fast routing & simple queries
- **Claude Sonnet** — complex reasoning & advice
- **SQLite** — transaction storage
- **Streamlit** — demo UI
- **LangSmith** — tracing & evaluation
