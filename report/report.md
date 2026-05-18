# Personal Finance Coach — Evaluation Report

## Executive Summary

Порівняльний аналіз двох архітектур AI-помічника для мобільного банківського застосунку:
1. **Multi-Agent Crew** (LangGraph) — supervisor + 3 спеціалізовані агенти (Gemini 2.5 Flash/Pro)
2. **Single-Agent Baseline** (Google GenAI SDK) — один агент Gemini 2.5 Pro з усіма 12 інструментами

**Результат:** Baseline перемагає по success rate (78.5% vs 40.0%) та tool selection (75.3% vs 5.9%), але crew показує кращу groundedness (70.6% vs 29.4%). Crew виграє у latency (P50: 3.9s vs 9.1s) завдяки використанню Flash для routing.

---

## Performance Metrics

### Quality

| Metric | 🤖 Crew | 📝 Baseline | Winner |
|--------|---------|-------------|--------|
| **Success Rate** | 40.0% | **78.5%** | Baseline |
| **Groundedness** | **70.6%** | 29.4% | Crew |
| **Tool Selection** | 5.9% | **75.3%** | Baseline |

### Latency

| Metric | 🤖 Crew | 📝 Baseline | Winner |
|--------|---------|-------------|--------|
| **P50 (ms)** | **3,869** | 9,053 | Crew |
| **P95 (ms)** | 30,724 | **24,479** | Baseline |
| **Average (ms)** | **10,001** | 10,549 | Crew |

### Reliability

| Metric | 🤖 Crew | 📝 Baseline |
|--------|---------|-------------|
| **Errors** | 0 / 17 | 1 / 17 |
| **Error Rate** | 0% | 5.9% |

---

## Results by Category

### Facts & Statistics (6 queries)

| Metric | Crew | Baseline |
|--------|------|----------|
| Avg Success | 20.0% | **65.8%** |

Baseline значно перевершує crew у фактичних запитах. Crew часто повертає неповну відповідь через overhead supervisor → agent routing.

### Savings Advice (4 queries)

| Metric | Crew | Baseline |
|--------|------|----------|
| Avg Success | 30.0% | **75.0%** |

Baseline показує більш послідовну якість порад. Crew іноді втрачає контекст при передачі між supervisor і savings_advisor.

### Multi-step Analysis (3 queries)

| Metric | Crew | Baseline |
|--------|------|----------|
| Avg Success | 46.7% | **80.0%** |

Crew теоретично мав би перевершувати у multi-step завданнях (координація кількох агентів), але на практиці baseline з одним потужним моделем справляється краще.

### Edge Cases (4 queries) 

| Metric | Crew | Baseline |
|--------|------|----------|
| Avg Success | 75.0% | **100.0%** |

Обидві архітектури добре справляються з edge cases (fraud, out-of-scope). Baseline ідеальний тут — правильно ескалює fraud і ввічливо відхиляє out-of-scope запити.

---

## Analysis

### Where Crew Wins
1. **Latency (P50)** — 3.9s vs 9.1s. Crew використовує Flash для routing і простих запитів, що дає 2.3x прискорення на типових запитах.
2. **Groundedness** — 70.6% vs 29.4%. Спеціалізовані агенти з вузьким набором інструментів менше "галюцинують", бо мають менше context noise.
3. **Reliability** — 0 помилок vs 1 помилка (503 від API). Менший payload per request знижує ризик timeout.

### Where Baseline Wins
1. **Success Rate** — 78.5% vs 40.0%. Один потужний агент послідовніше вирішує задачі без overhead міжагентної комунікації.
2. **Tool Selection** — 75.3% vs 5.9%. Baseline має прямий доступ до всіх інструментів і краще обирає правильні.
3. **Edge Cases** — 100% perfect scores. Простіша архітектура = менше точок відмови.

### Trade-offs

| Aspect | Crew | Baseline |
|--------|------|----------|
| **Cost per query** | Нижча (Flash для routing) | Вища (Pro для всього) |
| **Scalability** | Кожен агент масштабується окремо | Один bottleneck |
| **Maintainability** | Складніша (4 промпти) | Простіша (1 промпт) |
| **Extensibility** | Легко додати агента | Промпт росте лінійно |
| **Debugging** | Trace по агентах | Один послідовний лог |

---

## Conclusions & Production Recommendations

### Рекомендована архітектура: **Hybrid**

Для production рекомендую гібридний підхід:

1. **Використовувати baseline як основу** — один потужний агент для 80% запитів
2. **Escalation як окремий агент** — fraud і security запити виносити в окремий pipeline з більш strict guardrails
3. **Crew для batch analytics** — періодичний аналіз патернів витрат (Savings Advisor) може працювати async

### Оптимізації для production

1. **Caching** — кешувати DB queries (підписки рідко змінюються)
2. **Streaming** — Gemini підтримує streaming для кращого UX у чаті
3. **Retry з exponential backoff** — baseline мав 1 помилку через 503
4. **Prompt optimization** — crew потребує значного prompt tuning для покращення success rate

### Key Takeaway

> Multi-agent архітектура **НЕ є срібною кулею**. Для задач з обмеженим scope (фінансовий помічник з 12 інструментами), один добре налаштований агент перевершує crew по якості. Crew дає переваги у latency та cost, але за рахунок складності та потенційної втрати контексту між агентами.

---

*Golden Set Evaluation — 17 test cases × 2 architectures | Gemini 2.5 Flash + Pro | May 2025*
