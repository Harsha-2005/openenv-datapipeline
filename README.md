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
  - curriculum-learning
  - multi-agent
  - replay-dashboard
  - explainable-ai
---

# 🔧 OpenEnv — Data Pipeline Debugger

> **A real-world OpenEnv environment where AI agents learn to debug broken ETL pipelines across 5 difficulty levels — with curriculum learning, multi-agent cooperation, advanced reward shaping, explainable AI, and a live Interactive Dashboard.**

[![OpenEnv](https://img.shields.io/badge/OpenEnv-compliant-blue)](https://openenv.dev)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Tasks](https://img.shields.io/badge/tasks-5-orange)](https://huggingface.co/spaces/Harsha-2005/openenv-datapipeline)
[![HF Space](https://img.shields.io/badge/🤗%20Space-Live-yellow)](https://huggingface.co/spaces/Harsha-2005/openenv-datapipeline)
[![Tests](https://img.shields.io/badge/tests-47%20passed-brightgreen)](#testing)
[![CI](https://img.shields.io/badge/CI-GitHub%20Actions-blue)](#ci)

---

## 🏆 Meta PyTorch Hackathon × Scaler SST — Grand Finale

**Team:** Harsha Pavan M · Challa Lakshmi Thrinayanani · Brahmadevuni Gagan Kumar Reddy  
**Submission:** Phase 1 ✅ · Phase 2 ✅ · Grand Finale 🎯  
**Live Space:** [huggingface.co/spaces/Harsha-2005/openenv-datapipeline](https://huggingface.co/spaces/Harsha-2005/openenv-datapipeline)

---

## 📖 What This Project Does

Every company running data pipelines faces recurring nightmares: columns arrive with wrong types, records get duplicated during ingestion, nulls propagate silently, business constraints get violated, and pipeline stages run in the wrong order.

**OpenEnv Data Pipeline Debugger** turns this real-world problem into a rigorous RL environment. An AI agent observes a broken pipeline, selects repair actions step-by-step, receives shaped rewards for each fix, and is scored on how well it restores data quality — all under a step budget and SLA constraint.

### What Makes It Novel

| Feature | Description |
|---------|-------------|
| **5 Difficulty Tiers** | Easy → Expert with progressively complex bug patterns |
| **Curriculum Learning** | Auto-advances the agent when it masters each tier |
| **Multi-Agent Cooperation** | Inspector → Fixer → Validator pipeline |
| **Interactive Web Dashboard** | Live task runner, benchmarks, system docs — all in-browser |
| **Competition Mode** | Side-by-side agent arena with split-screen comparison |
| **Auto-Demo Mode** | Self-running tabbed presentation for judges — no CLI needed |
| **Dynamic Bug Injection** | Procedural generation of pipeline breakages (nulls, duplicates, schema drift, outliers) |
| **Advanced Shaped Rewards** | Novelty bonuses, cascade bonuses, regression penalties, efficiency multipliers |
| **Explainable AI Output** | Per-step reasoning, observation summaries, reward component breakdowns |
| **Benchmark Baselines** | Random, Greedy, Fixed-Strategy agents for comparison |
| **Comprehensive Analytics** | Auto-generated HTML reports with mastery timelines, efficiency charts |
| **CI/CD Pipeline** | GitHub Actions for lint, test, and server health checks |

---

## 🗂️ Project Structure

```
openenv-datapipeline/
├── app.py                    # FastAPI server — REST API + HTML endpoints
├── dashboard.py              # Interactive Web Dashboard (sidebar nav, runner, benchmarks)
├── demo.py                   # Self-running Auto-Demo Mode for judges
├── compete.py                # Side-by-side Agent Competition Arena
├── analytics.py              # Training Report generator (Chart.js)
├── bug_injector.py           # Dynamic Data Quality Fault Injection
├── visualize.py              # Reward chart + Replay Dashboard generators
├── benchmarks/
│   ├── agents.py             # RandomAgent, GreedyAgent, FixedStrategyAgent
│   └── run_benchmarks.py     # Evaluation runner + HTML export
├── env/
│   ├── environment.py        # DataPipelineEnv + StepRecord (Explainable AI)
│   └── models.py             # Pydantic models: Action, Observation, PipelineState
├── tasks/
│   ├── definitions.py        # 3 base tasks + TASK_REGISTRY + TASK_INFO
│   └── extra_tasks.py        # VeryHard + Expert tasks
├── graders/
│   └── graders.py            # 5 graders + score_pipeline() entry point
├── train.py                  # Curriculum training loop + replay + analytics
├── inference.py              # LLM-powered inference + rule-based fallback
├── curriculum.py             # CurriculumManager + AgentSkillProfile
├── multi_agent.py            # Inspector → Fixer → Validator cooperative pipeline
├── server/app.py             # Uvicorn entry point
├── tests/
│   └── test_env.py           # 49 tests — 47 pass, 2 skip
├── .github/workflows/ci.yml  # GitHub Actions CI pipeline
├── Makefile                  # One-command setup, test, serve, train, bench
├── Dockerfile
├── pyproject.toml
├── requirements.txt
├── .env.example              # Environment variable documentation
└── .gitignore
```

---

## 🎯 Task Difficulty Tiers

| Task | Difficulty | Steps | Rows | Bugs | Best Score |
|------|-----------|-------|------|------|------------|
| `task_easy_schema_fix` | Easy | 10 | 30 | 5 | 0.900 |
| `task_medium_data_quality` | Medium | 20 | 65 | 6 | 0.999 |
| `task_hard_pipeline_orchestration` | Hard | 40 | 107 | 13 | 0.981 |
| `task_veryhard_streaming_pipeline` | Very Hard | 50 | 160 | 13 | — |
| `task_expert_multi_source_join` | Expert | 60 | 212 | 17 | — |

---

## ⚙️ Action Space (11 actions)

| Action | What it does |
|--------|-------------|
| `inspect` | Observe current pipeline state, null counts, duplicates |
| `cast_column` | Fix type mismatches (str→int, object→float64) |
| `drop_nulls` | Remove rows with null values in a column |
| `fill_nulls` | Fill nulls with median or a specified value |
| `drop_duplicates` | Remove duplicate rows |
| `filter_outliers` | Remove IQR outliers from a numeric column |
| `rename_column` | Fix column naming violations |
| `reorder_stages` | Fix pipeline stage ordering (Hard+) |
| `apply_business_rule` | Enforce `discount_lte_1`, `fraud_score_lte_1`, `currency_3char`, `country_2char` |
| `validate` | Score current state without submitting |
| `submit` | Final submission — ends episode, returns score |

---

## 💰 Advanced Reward Function

```
R(t) = Δprogress(t)
     − 0.02 × step_cost
     − 0.05 × repeat_penalty
     + 0.02 × novelty_bonus          ← NEW: reward for productive novel actions
     + 0.03 × cascade_bonus          ← NEW: bonus for chaining consecutive fixes
     − 0.01 × regression_penalty     ← NEW: penalty if action caused negative reward
     + 0.05 × efficiency_bonus       ← NEW: bonus for high score in fewer steps
     + 0.10 × score × submit_bonus
```

- **Step cost** `−0.02` — every action costs, encouraging efficiency
- **Repeat penalty** `−0.05` — penalises calling the same action twice (except validate/submit)
- **Novelty bonus** `+0.02` — rewards productive actions not recently used
- **Cascade bonus** `+0.03` — rewards chaining multiple successful fixes
- **Regression penalty** `−0.01` — penalises actions that worsen the pipeline
- **Efficiency bonus** `+0.05` — scales with how few steps were needed for a high score
- **Submit bonus** `+0.10 × score` — big reward for correct submission
- Scores clipped to open interval `(0.001, 0.999)` per OpenEnv spec

---

## 🧠 Grand Finale Features

### 1. Interactive Web Dashboard
A fully interactive dashboard served at `/dashboard`:
- **Overview Panel** — system status, task list, stats
- **Episode Runner** — select any task, click "Run Episode", watch the agent debug in real-time
- **Benchmarks** — run baseline comparisons (Random vs Greedy vs Fixed Strategy)
- **System Docs** — architecture overview and reward formula

### 2. Auto-Demo Mode (`/demo`)
Self-running presentation for judges with tabbed views:
- Training curves, replay episodes (Easy/Medium/Hard), interactive dashboard
- **No CLI needed** — judges just open the URL

### 3. Competition Mode (`/compete`)
Side-by-side split-screen arena comparing two agents on the same task.

### 4. Explainable AI
Every `StepRecord` includes:
- **Reasoning** — *"Schema mismatch detected on column 'age'. Casting to int64 to fix type alignment."*
- **Observation Summary** — what the agent saw before acting
- **Reward Components** — `{"action_reward": 0.06, "step_cost": -0.02, "repeat_penalty": 0.0, "total": 0.04}`
- **Alternatives** — other actions the agent considered

### 5. Dynamic Bug Injection
`DynamicBugInjector` procedurally generates pipeline breakages:
- Null injection, duplicate injection, schema drift, outlier injection
- Severity presets: easy, medium, hard

### 6. Benchmark Baselines
Three baseline agents for comparison:
- **RandomAgent** — picks random valid actions
- **GreedyAgent** — always picks the highest expected immediate reward
- **FixedStrategyAgent** — follows a hardcoded optimal sequence

### 7. Replay & Step Debugger Dashboard
Standalone HTML replays (`replay_ep{N}.html`) with:
- Clickable timeline — jump to any step
- Step detail — action, reward, bugs remaining, reasoning
- Live reward curve — grows as you step through
- Action log with colour-coded chips
- Play/Pause with keyboard shortcuts (←→ and Space)

### 8. Curriculum Learning
Auto-advances through difficulty tiers when score ≥ 0.90 for 3 consecutive episodes:
```
Easy (0.82→0.90) → Medium (0.85→0.95) → Hard (0.629→0.981) → VeryHard → Expert
```

### 9. Multi-Agent Cooperation
`Inspector → Fixer → Validator` cooperative pipeline via `MessageBus`:
```python
from multi_agent import run_multi_agent_episode
result = run_multi_agent_episode(task_id="task_hard_pipeline_orchestration")
```

### 10. Comprehensive Analytics
Auto-generated HTML training reports with:
- Curriculum Reward Trajectory (scatter plot)
- Efficiency Chart (steps to completion)
- Task Mastery Timeline (moving average)

---

## 🚀 Running the Project

### Quick Start (3 commands)
```bash
cd openenv-datapipeline
python -m venv venv
venv\Scripts\activate          # Windows PowerShell
# source venv/bin/activate     # Linux/Mac

pip install -r requirements.txt
```

Or use the Makefile:
```bash
make setup
```

### Step 1 — Run all tests
```bash
set PYTHONPATH=.
python -m pytest tests/test_env.py -v
# Expected: 47 passed, 2 skipped, 0 failed
```

### Step 2 — Start the server
```bash
set PYTHONPATH=.
python app.py
# Server at: http://localhost:7860
# API docs:  http://localhost:7860/docs
# Dashboard: http://localhost:7860/dashboard
# Demo:      http://localhost:7860/demo
# Compete:   http://localhost:7860/compete
```

### Step 3 — Run a quick training smoke test
```bash
set HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
set ENV_BASE_URL=https://Harsha-2005-openenv-datapipeline.hf.space
set MODEL_NAME=Qwen/Qwen2.5-72B-Instruct

python train.py --steps 5 --task task_easy_schema_fix --replay-every 1 --replay-dir replays/
```

### Step 4 — Full curriculum training
```bash
python train.py --curriculum --steps 1000 --replay-dir replays/
```

### Step 5 — Run benchmarks
```bash
python benchmarks/run_benchmarks.py
```

---

## 🎬 3-Minute Judge Demo Script

| Time | Say | Show |
|------|-----|------|
| 0:00–0:30 | "Our environment simulates a broken ETL pipeline with 13 injected bugs. The agent must fix them in ≤40 steps." | Open `/dashboard` → Run Episode on Hard task |
| 0:30–1:00 | "Early in training, the agent wastes steps inspecting repeatedly — it gets a −0.05 repeat penalty. Score: 0.63." | Step through first 5 actions, show red penalty values |
| 1:00–1:45 | "By episode 69 the agent has learned: cast types → remove duplicates → fill nulls → reorder stages → apply business rules → submit. Score 0.981." | Open `/demo` → show training tab |
| 1:45–2:15 | "The reward curve shows the dip at episode 69 — that's the curriculum advancing to VeryHard. The agent recovers, demonstrating transfer learning." | Open training chart, point to dip |
| 2:15–3:00 | "This is fully interactive — try `/compete` for agent-vs-agent, or run the benchmarks to see our agent vs random/greedy baselines." | Hand to judge → `/compete` |

---

## 📊 Training Results

```
Episodes:         102
Starting score:   0.629  (Hard task, episode 1)
Best score:       0.9808 (Hard task, episode 69)
Final avg (20):   0.9663
Improvement:      +0.356

Easy task:   0.82 → 0.90  (curriculum advance at ep 18)
Medium task: 0.85 → 0.95  (curriculum advance at ep 41)
Hard task:   0.629→ 0.981 (episode 69 — best score)
```

---

## 🔌 API Reference

The live HF Space exposes a full OpenEnv-compliant HTTP API:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/tasks` | GET | List all available tasks |
| `/reset` | POST | Reset environment for a task |
| `/step` | POST | Apply an action |
| `/state` | GET | Get full internal PipelineState |
| `/dashboard` | GET | Interactive web dashboard |
| `/demo` | GET | Self-running auto-demo |
| `/compete` | GET | Multi-agent competition arena |
| `/api/benchmark` | GET | Run benchmark comparison |
| `/docs` | GET | Interactive Swagger API docs |

```bash
BASE=https://Harsha-2005-openenv-datapipeline.hf.space

# Health check
curl $BASE/health

# List all tasks
curl $BASE/tasks

# Reset environment
curl -X POST $BASE/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "task_hard_pipeline_orchestration", "seed": 42}'

# Take a step
curl -X POST $BASE/step \
  -H "Content-Type: application/json" \
  -d '{"action_type": "inspect"}'

# Submit
curl -X POST $BASE/step \
  -H "Content-Type: application/json" \
  -d '{"action_type": "submit"}'
```

---

## 🧪 Testing

```bash
python -m pytest tests/test_env.py -v

# Test classes:
# TestReset              — 6 tests  ✅
# TestStep               — 8 tests  ✅
# TestState              — 4 tests  ✅
# TestActions            — 7 tests  ✅ (2 skipped — task-specific columns)
# TestGraders            — 6 tests  ✅
# TestRewardFunction     — 4 tests  ✅
# TestTaskInfo           — 3 tests  ✅
# TestHistory            — 7 tests  ✅
# TestReplayIntegration  — 4 tests  ✅
# Total: 47 passed, 2 skipped
```

### CI/CD
GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push/PR:
- Python 3.10, 3.11, 3.12 matrix
- Compile check all modules
- Full test suite
- Server health check

---

## 🏗️ Architecture

```
Agent (LLM: Qwen2.5-72B via HF Router)
    │
    ▼
DataPipelineEnv (env/environment.py)
    │  reset() → Observation
    │  step(Action) → Observation + StepRecord
    │
    ├── TASK_REGISTRY (tasks/definitions.py)
    │       └── build_state(seed) → PipelineState
    │
    ├── Action Dispatch (11 handlers)
    │       └── pandas operations on live DataFrame
    │
    ├── Advanced Rewards
    │       └── novelty + cascade + regression + efficiency
    │
    ├── score_pipeline (graders/graders.py)
    │       └── grade_easy / grade_medium / grade_hard / grade_veryhard / grade_expert
    │
    ├── StepRecord → env.history → generate_replay_html()
    │       └── reasoning + observation_summary + reward_components
    │
    └── Web Endpoints
            ├── /dashboard  — Interactive Dashboard
            ├── /demo       — Auto-Demo Mode
            ├── /compete    — Competition Arena
            └── /api/benchmark — Baseline Evaluation
```

---

## 🐳 Docker / HF Space Deployment

```bash
# Build and run locally
docker build -t openenv-datapipeline .
docker run -p 7860:7860 \
  -e HF_TOKEN=hf_xxx \
  -e MODEL_NAME=Qwen/Qwen2.5-72B-Instruct \
  openenv-datapipeline

# Deploy to HF Space
python -c "
from huggingface_hub import HfApi
HfApi().upload_folder(
    folder_path='.',
    repo_id='Harsha-2005/openenv-datapipeline',
    repo_type='space',
    ignore_patterns=['venv/', '__pycache__/', '.git/', '*.pyc', 'replays/', '*.html', '*.zip']
)
"
```

---

## 📋 Makefile Commands

```bash
make setup    # Install dependencies
make test     # Run test suite
make serve    # Start environment server (uvicorn, port 7860)
make train    # Run 50-episode training with replays
make infer    # Run inference on all tasks
make bench    # Run benchmark comparison
make demo     # Generate sample replay
make lint     # Compile-check all modules
make clean    # Remove generated files
```

---

## 👥 Team

| Name | Role |
|------|------|
| Maddala Hema Narasimha Harsha Pavan | Team Lead — Environment Design, Training, Replay Dashboard |
| Challa Lakshmi Thrinayanani | Multi-Agent Architecture, Graders |
| Brahmadevuni Gagan Kumar Reddy | FastAPI Server, Docker, HF Deployment |

---

## 📄 License

MIT © 2026 OpenEnv Data Pipeline Debugger Team