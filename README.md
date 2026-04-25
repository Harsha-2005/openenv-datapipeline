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
---

# 🔧 OpenEnv — Data Pipeline Debugger

> **A real-world OpenEnv environment where AI agents learn to debug broken ETL pipelines across 5 difficulty levels — with curriculum learning, multi-agent cooperation, and a live step-by-step Replay Dashboard.**

[![OpenEnv](https://img.shields.io/badge/OpenEnv-compliant-blue)](https://openenv.dev)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Tasks](https://img.shields.io/badge/tasks-5-orange)](https://huggingface.co/spaces/Harsha-2005/openenv-datapipeline)
[![HF Space](https://img.shields.io/badge/🤗%20Space-Live-yellow)](https://huggingface.co/spaces/Harsha-2005/openenv-datapipeline)
[![Tests](https://img.shields.io/badge/tests-47%20passed-brightgreen)](#testing)

---

## 🏆 Meta PyTorch Hackathon × Scaler SST — Grand Finale

**Team:** Harsha Pavan M · Challa Lakshmi Thrinayanani · Brahmadevuni Gagan Kumar Reddy  
**Submission:** Phase 1 ✅ · Phase 2 ✅ · Grand Finale 🎯  
**Live Space:** [huggingface.co/spaces/Harsha-2005/openenv-datapipeline](https://huggingface.co/spaces/Harsha-2005/openenv-datapipeline)

---

## 📖 What This Project Does

Every company running data pipelines faces the same recurring nightmares: columns arrive with wrong types, records get duplicated during ingestion, nulls propagate silently, business constraints get violated, and pipeline stages run in the wrong order.

**OpenEnv Data Pipeline Debugger** turns this real-world problem into a rigorous RL environment. An AI agent observes a broken pipeline, selects repair actions step-by-step, receives shaped rewards for each fix, and is scored on how well it restores data quality — all under a step budget and SLA constraint.

### What makes it novel

- **5 difficulty tiers** (Easy → Expert) with progressively complex bug patterns
- **Curriculum learning** that auto-advances the agent when it masters each tier
- **Multi-agent cooperation** — Inspector → Fixer → Validator pipeline
- **Replay Dashboard** — step through any training episode frame-by-frame in a browser
- **11 action types** including business rule enforcement and stage reordering
- **Shaped reward** with step cost, repeat penalty, and submit bonus

---

## 🗂️ Project Structure

```
openenv-datapipeline/
├── app.py                    # FastAPI server — OpenEnv HTTP API
├── server/app.py             # Uvicorn entry point (server=server.app:main)
├── env/
│   ├── environment.py        # DataPipelineEnv + StepRecord (Replay Dashboard)
│   └── models.py             # Pydantic models: Action, Observation, PipelineState
├── tasks/
│   ├── definitions.py        # 3 base tasks + TASK_REGISTRY + TASK_INFO
│   └── extra_tasks.py        # VeryHard + Expert tasks
├── graders/
│   └── graders.py            # 5 graders + score_pipeline() entry point
├── train.py                  # Curriculum training loop + Replay Dashboard hooks
├── curriculum.py             # CurriculumManager + AgentSkillProfile
├── multi_agent.py            # Inspector → Fixer → Validator cooperative pipeline
├── visualize.py              # generate_reward_chart() + generate_replay_html()
├── tests/
│   └── test_env.py           # 49 tests — 47 pass, 2 skip
├── Dockerfile
├── pyproject.toml
└── requirements.txt
```

---

## 🎯 Task Difficulty Tiers

| Task | Difficulty | Steps | Rows | Bugs | Score |
|------|-----------|-------|------|------|-------|
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

## 💰 Reward Function

```
R(t) = Δprogress(t) − 0.02×step_cost − 0.05×repeat_penalty + 0.10×score×submit_bonus
```

- **Step cost** `-0.02` — every action costs, encouraging efficiency
- **Repeat penalty** `-0.05` — penalises calling the same action twice in a row (except validate/submit)
- **Submit bonus** `+0.10 × score` — big reward for correct submission
- Scores clipped to open interval `(0.001, 0.999)` per OpenEnv spec

---

## 🧠 New Features (Grand Finale)

### 1. Replay & Step Debugger Dashboard
After every training episode, `generate_replay_html()` produces a standalone HTML file showing:
- **Timeline** — every step as a clickable dot; click any step to jump to it
- **Step detail** — action taken, reward received, bugs remaining
- **Live reward curve** — grows as you step through the episode
- **Action log** — last 6 actions with reward delta

```python
# Auto-generated during training:
from visualize import generate_replay_html
generate_replay_html(env.history, episode_num=69,
                     task_id="task_hard_pipeline_orchestration",
                     output_path="replay_ep69.html")
# Open replay_ep69.html in Chrome — no server needed
```

### 2. Curriculum Learning
Agent auto-advances through difficulty tiers when it achieves ≥0.90 rolling average for 3 consecutive episodes.

```
Easy (0.82→0.90) → Medium (0.85→0.95) → Hard (0.629→0.981) → VeryHard → Expert
```

Training results: **+0.36 score improvement** over 102 episodes. Notable dip at episode 69 = curriculum advancing to Hard task, then recovery to 0.981 — demonstrating transfer learning.

### 3. Multi-Agent Cooperation
`Inspector → Fixer → Validator` cooperative pipeline via `MessageBus`.

```python
from multi_agent import run_multi_agent_episode
result = run_multi_agent_episode(task_id="task_hard_pipeline_orchestration")
```

### 4. Noise-Decay Exploration
```python
noise = 0.80  # start with high exploration
# decays by ×0.96 each episode → 0.05 at convergence
```

---

## 🚀 Running the Project

### Prerequisites
```bash
# Windows (PowerShell or Git Bash)
cd openenv-datapipeline
python -m venv venv
venv\Scripts\activate          # PowerShell
# source venv/Scripts/activate # Git Bash

pip install -r requirements.txt
```

### Step 1 — Run all tests (verify everything works)
```bash
set PYTHONPATH=.               # PowerShell / CMD
# export PYTHONPATH=.          # Git Bash

python -m pytest tests/test_env.py -v
# Expected: 47 passed, 2 skipped, 0 failed
```

### Step 2 — Test the Replay Dashboard (offline, no token needed)
```bash
python train_replay_patch.py
# Creates: replay_ep_test.html
start replay_ep_test.html      # opens in default browser
```

### Step 3 — Start the FastAPI server locally
```bash
set PYTHONPATH=.
uvicorn server.app:main --host 0.0.0.0 --port 7860 --reload
# API docs: http://localhost:7860/docs
```

### Step 4 — Run a quick 5-episode smoke test
```bash
set HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
set ENV_BASE_URL=https://Harsha-2005-openenv-datapipeline.hf.space
set MODEL_NAME=Qwen/Qwen2.5-72B-Instruct

python train.py --steps 5 --task task_easy_schema_fix --replay-every 1 --replay-dir replays/
# Creates: replays/replay_ep0.html ... replay_ep4.html + training_results.html
```

### Step 5 — Full curriculum training (Grand Finale run)
```bash
python train.py --curriculum --steps 1000 --replay-dir replays/
# Creates: training_results.html + replays/replay_ep*.html
```

### Step 6 — Open demo files in browser
```bash
start training_results.html       # reward curve across all episodes
start replays\replay_ep0.html     # baseline — agent before training
start replays\replay_final.html   # best episode — agent after training
```

---

## 🎬 3-Minute Judge Demo Script

| Time | Say | Show |
|------|-----|------|
| 0:00–0:30 | "Our environment simulates a broken ETL pipeline with 13 injected bugs. The agent must fix them in ≤40 steps." | Open `replay_ep0.html` — Hard task, Episode 0 |
| 0:30–1:00 | "Early in training, the agent wastes steps inspecting repeatedly — it gets a −0.05 repeat penalty. Score: 0.63." | Step through first 5 actions, show red penalty values |
| 1:00–1:45 | "By episode 69 the agent has learned: cast types → remove duplicates → fill nulls → reorder stages → apply business rules → submit. Same task, 14 fewer steps, score 0.981." | Open `replay_ep69.html`, hit Play, let it run |
| 1:45–2:15 | "The reward curve shows the dip at episode 69 — that's the curriculum advancing to VeryHard. The agent briefly struggles then transfers its learning and recovers." | Open `training_results.html`, point to dip |
| 2:15–3:00 | "This is fully interactive — you can step through any episode, see exact rewards, and verify the agent is learning genuine data engineering strategy." | Hand to judge to click through |

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
  -d '{"action_type": "inspect", "column": null}'

# Submit
curl -X POST $BASE/step \
  -H "Content-Type: application/json" \
  -d '{"action_type": "submit", "column": null}'
```

---

## 🧪 Testing

```bash
python -m pytest tests/test_env.py -v

# Test classes:
# TestReset          — 6 tests  ✅
# TestStep           — 8 tests  ✅
# TestState          — 4 tests  ✅
# TestActions        — 7 tests  ✅ (2 skipped — task-specific columns)
# TestGraders        — 6 tests  ✅
# TestRewardFunction — 4 tests  ✅
# TestTaskInfo       — 3 tests  ✅
# TestHistory        — 7 tests  ✅  (NEW — Replay Dashboard)
# TestReplayIntegration — 4 tests ✅ (NEW — Replay Dashboard)
# Total: 47 passed, 2 skipped
```

---

## 🏗️ Architecture

```
Agent (LLM: Qwen2.5-72B via HF Router)
    │
    ▼
DataPipelineEnv (env/environment.py)
    │  reset() → Observation
    │  step(Action) → Observation + StepRecord appended to env.history
    │
    ├── TASK_REGISTRY (tasks/definitions.py)
    │       └── build_state(seed) → PipelineState
    │
    ├── Action Dispatch (11 handlers)
    │       └── pandas operations on live DataFrame
    │
    ├── score_pipeline (graders/graders.py)
    │       └── grade_easy / grade_medium / grade_hard / grade_veryhard / grade_expert
    │
    └── StepRecord → env.history → generate_replay_html() → replay_ep{N}.html
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

# Deploy to HF Space (uses HfApi — no git auth needed)
python -c "
from huggingface_hub import HfApi
HfApi().upload_folder(
    folder_path='.',
    repo_id='Harsha-2005/openenv-datapipeline',
    repo_type='space',
    ignore_patterns=['venv/', '__pycache__/', '.git/', '*.pyc', 'replays/']
)
"
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

MIT © 2025 OpenEnv Data Pipeline Debugger Team