---
title: OpenEnv Data Pipeline Debugger
emoji: 🔧
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
license: mit
tags:
  - openenv
  - data-engineering
  - etl
  - agent-benchmark
  - reinforcement-learning
---

# 🔧 OpenEnv — Data Pipeline Debugger

> **A real-world OpenEnv environment where AI agents debug broken ETL pipelines.**

[![OpenEnv](https://img.shields.io/badge/OpenEnv-compliant-blue)](https://openenv.dev)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## Environment Description & Motivation

Every company running data pipelines deals with the same set of recurring problems: columns arrive with the wrong type, records get duplicated during ingestion, nulls propagate silently, business constraints get violated, and sometimes entire pipeline stages run in the wrong order.

This environment models **exactly that**. Agents must act like a senior data engineer: inspect the pipeline state, diagnose issues systematically, apply the right fixes in the right order, and validate their work before declaring success.

Unlike toy grid-worlds, the metrics here — completeness, uniqueness, validity, accuracy — are the same KPIs real data teams track in production dashboards.

---

## 📐 Observation Space

```json
{
  "task_id":          "string   — active task identifier",
  "step_count":       "int      — steps taken",
  "max_steps":        "int      — episode budget",
  "pipeline_stage":   "string   — current stage [ingest|validate|transform|enrich|load|complete]",
  "data_sample":      "list[dict] — first 5 rows of current dataset",
  "schema_info":      "list[{name, expected_type, actual_type, nullable}]",
  "error_log":        "list[str]  — last 6 pipeline errors/warnings",
  "metrics": {
    "completeness":   "float [0,1] — fraction of non-null cells",
    "uniqueness":     "float [0,1] — fraction of unique rows",
    "validity":       "float [0,1] — fraction passing all business rules",
    "accuracy":       "float [0,1] — fraction with schema-correct types",
    "sla_latency_ms": "float       — simulated processing latency"
  },
  "available_actions": "list[str]",
  "hint":             "string   — guidance toward the next unfixed issue",
  "done":             "bool"
}
```

---

## 🎮 Action Space

| action_type | Required fields | Description |
|---|---|---|
| `inspect` | — | Examine data statistics (null count, duplicate count, stage order) |
| `cast_column` | `column`, `value` (type) | Fix column type: `"int"`, `"float"`, `"str"`, `"bool"` |
| `drop_nulls` | `column` (optional) | Drop rows with nulls (specific column or all required columns) |
| `fill_nulls` | `column`, `value` | Fill null cells with a constant |
| `drop_duplicates` | — | Remove exact duplicate rows |
| `filter_outliers` | `column`, `value="min,max"` | Filter rows outside numeric range |
| `apply_business_rule` | `value` (rule name) | Apply named constraint: `discount_lte_1`, `fraud_score_lte_1`, `currency_3char`, `country_2char` |
| `reorder_stages` | `parameters.stages` | Fix pipeline stage execution order (hard task) |
| `validate` | — | Run full schema + constraint validation, update metrics |
| `submit` | — | End episode and receive final score |

### Example actions

```json
{"action_type": "cast_column", "column": "customer_id", "value": "int"}
{"action_type": "filter_outliers", "column": "quantity", "value": "0,10000"}
{"action_type": "apply_business_rule", "value": "discount_lte_1"}
{"action_type": "reorder_stages", "parameters": {"stages": ["ingest","validate","transform","enrich","load"]}}
{"action_type": "submit"}
```

---

## 📋 Tasks

### Task 1 — Schema Mismatch Fix *(Easy)*
**ID:** `task_easy_schema_fix` | **Budget:** 10 steps

A customer CSV arrives with every numeric column stored as strings. The pipeline validator rejects the batch. The agent must identify the mistyped columns (`customer_id`, `age`, `revenue`) and cast them to the correct types, while also handling a handful of non-parseable values (`"not_a_number"`, `"N/A"`).

**Grading weights:** bug ratio 40% · accuracy 30% · completeness 20% · efficiency bonus 10%

**Expected baseline score:** ~0.65–0.78

---

### Task 2 — Data Quality Remediation *(Medium)*
**ID:** `task_medium_data_quality` | **Budget:** 20 steps

An order ingestion pipeline has four distinct quality problems that must be fixed in a sensible order: 5 exact duplicate rows, 9 null values across key columns, 3 rows with negative/absurd quantities, and 3 rows violating the `discount ≤ 1.0` business rule.

**Grading weights:** bug ratio 30% · completeness 25% · uniqueness 25% · validity 15% · efficiency bonus 5%

**Expected baseline score:** ~0.55–0.72

---

### Task 3 — Full Pipeline Orchestration Debug *(Hard)*
**ID:** `task_hard_pipeline_orchestration` | **Budget:** 40 steps

A transaction fraud-detection pipeline has 13 distinct bugs across all five pipeline stages:
- **Stage order scrambled** — the pipeline runs `transform` before `validate`
- **Type errors** — `txn_id`, `user_id`, `amount`, `fraud_score` all arrive as strings
- **7 duplicate transactions**
- **12 null values** in `merchant`, `category`, `fraud_score`, `country_code`
- **3 negative amounts**
- **3 fraud_scores > 1.0**
- **Invalid ISO currency and country codes**
- **SLA breach** — latency starts at 320ms (threshold: 100ms), improves as bugs are fixed

This task requires the agent to reason about fix *ordering* (fix stage order before transforms, validate before submit) and apply 10+ distinct fixes under a step budget. Frontier models score ~0.45–0.60 without chain-of-thought.

**Grading weights:** stage order 20% · bug ratio 25% · completeness 20% · uniqueness 15% · validity 10% · accuracy 10% · SLA penalty

**Expected baseline score:** ~0.35–0.55

---

## 🏆 Reward Function

Rewards are shaped to provide dense signal throughout the episode:

```
step_reward = progress + step_cost + repeat_penalty + submit_bonus

  progress       = new_grade_score - prev_grade_score   (can be negative)
  step_cost      = -0.02  per step (encourages efficiency)
  repeat_penalty = -0.05  if same action repeated 3+ consecutive times
  submit_bonus   = +0.10 × final_score  on submit action
```

This means:
- Every fix that measurably improves metrics gives immediate positive reward
- Wasting steps on useless repeated actions is penalized
- High-quality submissions are rewarded with a bonus proportional to their score

---

## 🚀 Setup & Usage

### Option 1 — Docker

```bash
git clone https://huggingface.co/spaces/YOUR_USERNAME/openenv-datapipeline
cd openenv-datapipeline

docker build -t openenv-datapipeline .
docker run -p 7860:7860 openenv-datapipeline
```

### Option 2 — Local Python

```bash
pip install -r requirements.txt
python app.py
```

API available at `http://localhost:7860`. Interactive docs at `http://localhost:7860/docs`.

### Quick API example

```python
import requests

BASE = "http://localhost:7860"

# Reset
obs = requests.post(f"{BASE}/reset", json={"task_id": "task_easy_schema_fix"}).json()
print(obs["error_log"])

# Step
result = requests.post(f"{BASE}/step", json={
    "action_type": "cast_column",
    "column": "customer_id",
    "value": "int"
}).json()
print(result["reward"])  # {"value": 0.12, "cumulative": 0.12, ...}

# State
state = requests.get(f"{BASE}/state").json()
```

### Running the baseline

```bash
export API_BASE_URL="https://api-inference.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export HF_TOKEN="hf_your_token_here"
export ENV_BASE_URL="http://localhost:7860"

python inference.py
```

---

## 📊 Baseline Scores

Measured with `Qwen/Qwen2.5-72B-Instruct` via HuggingFace Inference API, seed=42:

| Task | Difficulty | Score | Steps Used |
|------|-----------|-------|-----------|
| Schema Mismatch Fix | Easy | 0.72 | 7 |
| Data Quality Remediation | Medium | 0.61 | 15 |
| Full Pipeline Orchestration | Hard | 0.43 | 35 |
| **Average** | | **0.59** | |

---

## 🔌 OpenEnv API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/tasks` | GET | List all tasks |
| `/reset` | POST | Reset for a task |
| `/step` | POST | Apply an action |
| `/state` | GET | Full internal state |
| `/docs` | GET | Swagger UI |

---

## 📁 Project Structure

```
openenv-datapipeline/
├── app.py                    # FastAPI application
├── inference.py              # Baseline inference script
├── openenv.yaml              # OpenEnv metadata
├── requirements.txt
├── Dockerfile
├── README.md
├── env/
│   ├── __init__.py
│   ├── models.py             # Typed Pydantic models
│   └── environment.py        # Core step/reset/state engine
├── tasks/
│   ├── __init__.py
│   └── definitions.py        # Task data generators + configs
├── graders/
│   ├── __init__.py
│   └── graders.py            # Deterministic graders (0.0–1.0)
└── tests/
    ├── __init__.py
    └── test_env.py           # Validation tests
```

---

## License

MIT — see [LICENSE](LICENSE)
