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

> **A real-world OpenEnv environment where AI agents debug broken ETL pipelines across 5 difficulty levels.**

[![Phase 1](https://img.shields.io/badge/Phase%201-PASSED-green)](https://huggingface.co/spaces/Harsha-2005/openenv-datapipeline)
[![Phase 2](https://img.shields.io/badge/Phase%202-PASSED-green)](https://huggingface.co/spaces/Harsha-2005/openenv-datapipeline)
[![OpenEnv](https://img.shields.io/badge/OpenEnv-compliant-blue)](https://openenv.dev)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Tasks](https://img.shields.io/badge/tasks-5-orange)](https://huggingface.co/spaces/Harsha-2005/openenv-datapipeline)
[![HF Space](https://img.shields.io/badge/🤗%20Space-Live-yellow)](https://huggingface.co/spaces/Harsha-2005/openenv-datapipeline)

---

## 📖 Environment Description & Motivation

Every company running data pipelines faces the same recurring nightmares: columns arrive with wrong types, records get duplicated during ingestion, nulls propagate silently, business constraints get violated, and sometimes entire pipeline stages run in the wrong order.

This environment models **exactly that reality**. Agents must act like a senior data engineer: inspect the pipeline state, diagnose issues systematically, apply the right fixes in the right order, and validate their work before declaring success.

Unlike toy grid-worlds or synthetic benchmarks, the metrics here — completeness, uniqueness, validity, accuracy, SLA latency — are the same KPIs real data teams track in production dashboards every day.

**5 difficulty levels** from quick schema fixes to expert-level multi-source join repairs with 17 interconnected bugs ensure meaningful differentiation between weak and strong agents.

---

## 🏗️ Project Structure

```
openenv-datapipeline/
├── app.py                    FastAPI REST server (all OpenEnv endpoints)
├── inference.py              Baseline agent script (OpenAI client)
├── openenv.yaml              OpenEnv metadata specification
├── Dockerfile                HF Spaces-compatible container
├── pyproject.toml            Package metadata + openenv-core dependency
├── uv.lock                   Locked dependency versions
├── requirements.txt          Runtime dependencies
├── README.md                 This file
├── env/
│   ├── models.py             Typed Pydantic models: Action, Observation, Reward, State
│   └── environment.py        Core engine: reset() / step() / state()
├── tasks/
│   ├── definitions.py        3 base task generators (easy/medium/hard)
│   └── extra_tasks.py        2 advanced tasks (very_hard/expert)
├── graders/
│   └── graders.py            Deterministic graders → float in (0.0, 1.0)
├── server/
│   └── app.py                OpenEnv server entry point (main())
└── tests/
    └── test_env.py           38 tests covering full OpenEnv spec
```

---

## 🎮 Action Space

Agents choose one action per step from the following action types:

| Action | Required Fields | Description |
|---|---|---|
| `inspect` | — | Examine data: row count, null count, duplicates, stage order |
| `cast_column` | `column`, `value` (type) | Fix column type: `int`, `float`, `str`, `bool` |
| `drop_nulls` | `column` (optional) | Drop rows with null values |
| `fill_nulls` | `column`, `value` | Fill null cells with a constant |
| `drop_duplicates` | — | Remove exact duplicate rows |
| `filter_outliers` | `column`, `value="min,max"` | Remove rows outside numeric range |
| `apply_business_rule` | `value` (rule name) | Apply named constraint rule |
| `reorder_stages` | `parameters.stages` | Fix pipeline stage execution order |
| `validate` | — | Run full schema + constraint validation |
| `submit` | — | End episode and receive final score |

**Available business rules:** `discount_lte_1`, `fraud_score_lte_1`, `currency_3char`, `country_2char`, `value_gte_0`, `qty_gt_0`, `price_gt_0`, `tax_rate_lte_0.5`

### Example actions

```json
{"action_type": "cast_column", "column": "customer_id", "value": "int"}
{"action_type": "filter_outliers", "column": "quantity", "value": "0,10000"}
{"action_type": "apply_business_rule", "value": "discount_lte_1"}
{"action_type": "reorder_stages", "parameters": {"stages": ["ingest","validate","transform","enrich","load"]}}
{"action_type": "submit"}
```

---

## 👁️ Observation Space

```json
{
  "task_id":          "string   — active task identifier",
  "step_count":       "int      — steps taken so far",
  "max_steps":        "int      — step budget for this task",
  "pipeline_stage":   "string   — [ingest|validate|transform|enrich|load|complete]",
  "data_sample":      "list[dict] — first 5 rows of the current dataset",
  "schema_info": [
    {
      "name":           "string — column name",
      "expected_type":  "string — correct type (int/float/str/bool)",
      "actual_type":    "string — current type in data",
      "nullable":       "bool   — whether nulls are allowed"
    }
  ],
  "error_log":        "list[str]  — last 6 pipeline errors and warnings",
  "metrics": {
    "completeness":   "float [0.001,0.999] — fraction of non-null cells",
    "uniqueness":     "float [0.001,0.999] — fraction of unique rows",
    "validity":       "float [0.001,0.999] — fraction passing business rules",
    "accuracy":       "float [0.001,0.999] — fraction with correct schema types",
    "sla_latency_ms": "float               — simulated processing latency"
  },
  "available_actions": "list[str] — valid action_type values",
  "hint":             "string    — guidance toward next unfixed issue",
  "done":             "bool      — whether episode is complete"
}
```

---

## 📋 Tasks

### Task 1 — Schema Mismatch Fix *(Easy)*
**ID:** `task_easy_schema_fix` | **Budget:** 10 steps | **Rows:** 30 | **Bugs:** 5 | **Schema:** 5 cols

A customer CSV arrives with every numeric column stored as strings. The agent must identify all mistyped columns (`customer_id`, `age`, `revenue`) and cast them to correct types, while handling non-parseable values like `"not_a_number"` and `"N/A"`.

**Grading:** bug ratio 40% · accuracy 30% · completeness 20% · efficiency 10%
**Baseline score (Qwen-72B):** `0.900`

---

### Task 2 — Data Quality Remediation *(Medium)*
**ID:** `task_medium_data_quality` | **Budget:** 20 steps | **Rows:** 65 | **Bugs:** 6 | **Schema:** 8 cols

An order ingestion pipeline has 4 distinct quality problems: 5 duplicate rows, 9 null values, rows with negative/absurd quantities, and discount values violating `discount ≤ 1.0`. Agent must apply fixes in sensible order.

**Grading:** bug ratio 30% · completeness 25% · uniqueness 25% · validity 15% · efficiency 5%
**Baseline score (Qwen-72B):** `0.999`

---

### Task 3 — Full Pipeline Orchestration Debug *(Hard)*
**ID:** `task_hard_pipeline_orchestration` | **Budget:** 40 steps | **Rows:** 107 | **Bugs:** 13 | **Schema:** 10 cols

A transaction fraud-detection pipeline has 13 interconnected bugs: scrambled stage order, 4 type errors, 7 duplicates, 12 nulls, 3 negative amounts, 3 invalid fraud scores, and malformed ISO currency/country codes. Agent must reason about fix *ordering* and meet SLA thresholds.

**Grading:** stage order 20% · bug ratio 25% · completeness 20% · uniqueness 15% · validity 10% · accuracy 10%
**Baseline score (Qwen-72B):** `0.999`

---

### Task 4 — Streaming Pipeline Debug *(Very Hard)*
**ID:** `task_veryhard_streaming_pipeline` | **Budget:** 50 steps | **Rows:** 160 | **Bugs:** 13 | **Schema:** 10 cols

A real-time event streaming pipeline with 13 bugs: wrong stage ordering, 4 type mismatches across all numeric columns, 10 duplicate events, 22 null values, 5 invalid event_type strings, 3 negative values, 3 extreme latency outliers, and a 200ms SLA threshold. Frontier models score ~0.55–0.70 without careful planning.

**Grading:** stage order 20% · bug ratio 30% · completeness 20% · validity 15% · uniqueness 10% · accuracy 5%
**Baseline score (Qwen-72B):** `~0.600`

---

### Task 5 — Multi-Source Join Repair *(Expert)*
**ID:** `task_expert_multi_source_join` | **Budget:** 60 steps | **Rows:** 212 | **Bugs:** 17 | **Schema:** 12 cols

The most complex task: a joined dataset from 3 data sources has 17 bugs including wrong stage order, 8 type mismatches, 12 duplicate rows from merge collisions, 24 null values across customer/product fields, 4 negative quantities, 3 negative prices, 4 discount violations, 3 tax_rate violations, and a tight 150ms SLA. Requires 25+ correct sequential actions.

**Grading:** stage order 15% · bug ratio 35% · completeness 20% · validity 15% · uniqueness 10% · accuracy 5%
**Baseline score (Qwen-72B):** `~0.500`

---

## 🏆 Reward Function

Dense reward signal throughout every episode:

```
step_reward = progress + step_cost + repeat_penalty + submit_bonus

  progress       = new_grade_score − prev_grade_score  (positive when improving)
  step_cost      = −0.02  per step  (encourages efficiency)
  repeat_penalty = −0.05  if same action repeated 3+ consecutive times
  submit_bonus   = +0.10 × final_score  on submit action
```

**Key properties:**
- Every bug fix gives immediate positive reward proportional to metric improvement
- Wasting steps on useless repeated actions is penalized
- High-quality submissions earn a bonus proportional to final score
- Scores clipped to strictly open interval `(0.001, 0.999)` — never exactly 0 or 1

---

## 📊 Baseline Scores

Measured with `Qwen/Qwen2.5-72B-Instruct` via HuggingFace router, seed=42:

| Task | Difficulty | Bugs | Score | Steps | Success |
|---|---|---|---|---|---|
| Schema Mismatch Fix | Easy | 5/5 | **0.900** | 7 | ✅ |
| Data Quality Remediation | Medium | 6/6 | **0.999** | 7 | ✅ |
| Full Pipeline Orchestration | Hard | 13/13 | **0.999** | 17 | ✅ |
| Streaming Pipeline Debug | Very Hard | ~10/13 | **~0.600** | 45 | ✅ |
| Multi-Source Join Repair | Expert | ~8/17 | **~0.500** | 55 | ⚠️ |
| **Average** | | | **0.800** | | |

---

## 🚀 Setup & Usage

### Option 1 — HuggingFace Space (Live)

The environment is deployed at:
```
https://Harsha-2005-openenv-datapipeline.hf.space
```

Test immediately:
```bash
curl https://Harsha-2005-openenv-datapipeline.hf.space/health
curl -X POST https://Harsha-2005-openenv-datapipeline.hf.space/reset \
  -H "Content-Type: application/json" -d "{}"
```

### Option 2 — Docker

```bash
git clone https://huggingface.co/spaces/Harsha-2005/openenv-datapipeline
cd openenv-datapipeline

docker build -t openenv-datapipeline .
docker run -p 7860:7860 openenv-datapipeline
```

### Option 3 — Local Python

```bash
pip install -r requirements.txt
python app.py
# API at http://localhost:7860
# Swagger UI at http://localhost:7860/docs
```

---

## 🔌 API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check — returns `{"status":"ok"}` |
| `/tasks` | GET | List all 5 tasks with metadata |
| `/reset` | POST | Reset for a task — body: `{"task_id":"...", "seed":42}` |
| `/step` | POST | Apply an action — body: `{"action_type":"...", ...}` |
| `/state` | GET | Full internal state (superset of observation) |
| `/docs` | GET | Swagger UI — interactive API testing |

### Quick Python example

```python
import requests

BASE = "https://Harsha-2005-openenv-datapipeline.hf.space"

# List all tasks
tasks = requests.get(f"{BASE}/tasks").json()

# Reset on expert task
obs = requests.post(f"{BASE}/reset", json={
    "task_id": "task_expert_multi_source_join",
    "seed": 42
}).json()
print(obs["error_log"])   # see what's broken

# Apply a fix
result = requests.post(f"{BASE}/step", json={
    "action_type": "cast_column",
    "column": "customer_id",
    "value": "int"
}).json()
print(result["reward"])   # {"value": 0.06, "cumulative": 0.06, ...}

# Check state
state = requests.get(f"{BASE}/state").json()
print(state["bugs_fixed"])  # which bugs are resolved

# Submit
result = requests.post(f"{BASE}/step", json={"action_type": "submit"}).json()
print(result["info"]["final_score"])
```

---

## 🤖 Running the Baseline Agent

```bash
# Set credentials
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
export HF_TOKEN=hf_your_token_here
export ENV_BASE_URL=https://Harsha-2005-openenv-datapipeline.hf.space

# Run inference (outputs [START]/[STEP]/[END] blocks to stdout)
python inference.py

# Save results
python inference.py > baseline_output.txt 2>debug.log
```

### Expected stdout format

```
[START] task=task_easy_schema_fix seed=42 max_steps=10
[STEP] task=task_easy_schema_fix step=1 action=cast_column reward=0.0600 cumulative_reward=0.0600 done=false completeness=0.960 validity=0.933 accuracy=0.933
[STEP] task=task_easy_schema_fix step=2 action=cast_column reward=0.0600 cumulative_reward=0.1200 done=false completeness=0.953 validity=0.967 accuracy=0.967
...
[END] task=task_easy_schema_fix score=0.9000 steps=9 total_reward=0.1600 bugs_fixed=5 success=true
[SUMMARY] model=Qwen/Qwen2.5-72B-Instruct tasks=5 avg_score=0.8000 scores=0.9000,0.9990,0.9990,0.6000,0.5000
```

---

## 🧪 Running Tests

```bash
pip install pytest
PYTHONPATH=. python -m pytest tests/test_env.py -v
# 38/38 tests passing
```

---

## 📐 OpenEnv Spec Compliance

| Requirement | Status |
|---|---|
| Typed Pydantic models (Action, Observation, Reward, State) | ✅ |
| `reset()` → Observation | ✅ |
| `step(action)` → (observation, reward, done, info) | ✅ |
| `state()` → PipelineState | ✅ |
| `openenv.yaml` metadata | ✅ |
| `pyproject.toml` with `openenv-core>=0.2.0` | ✅ |
| `server/app.py` with `main()` entry point | ✅ |
| `uv.lock` dependency lock | ✅ |
| Grader scores in strictly open interval `(0, 1)` | ✅ |
| Deterministic graders (same state → same score) | ✅ |
| `[START]/[STEP]/[END]` stdout format | ✅ |
| Dockerfile builds and runs on port 7860 | ✅ |
| HuggingFace Space deploys and responds | ✅ |
| Phase 1 automated validation | ✅ PASSED |
| Phase 2 deep validation | ✅ PASSED |

---

## 🔧 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `API_BASE_URL` | Yes | LLM API endpoint (e.g. `https://router.huggingface.co/v1`) |
| `MODEL_NAME` | Yes | Model identifier (e.g. `Qwen/Qwen2.5-72B-Instruct`) |
| `HF_TOKEN` | Yes | HuggingFace API token with inference permissions |
| `ENV_BASE_URL` | No | Environment server URL (default: `http://localhost:7860`) |
| `PORT` | No | Server port (default: `7860`) |

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

*Built for the Meta PyTorch Hackathon × Scaler School of Technology — OpenEnv Track*
*Submission #8 — Phase 1 ✅ Phase 2 ✅ — Officially in judging queue*