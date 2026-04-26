"""
OpenEnv Data Pipeline Debugger — FastAPI Application
Exposes reset(), step(), state() as REST endpoints.

Fix applied: DataPipelineEnv now requires task_id as first arg.
_env is now a stateful session manager that tracks current task_id + seed.
"""

from __future__ import annotations
<<<<<<< HEAD
import os
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
=======
import asyncio, json, os, io, csv, time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
>>>>>>> 03d62d9 (updated the demo and dashboard file and added the training using the grpo)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel

from env.environment import DataPipelineEnv
from env.models import Action, ActionType
from tasks.definitions import TASK_INFO, TASK_REGISTRY


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="OpenEnv — Data Pipeline Debugger",
    description=(
        "A real-world OpenEnv environment where agents debug broken ETL pipelines. "
        "Implements reset(), step(), state() following the OpenEnv specification."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Session state
# FIX: DataPipelineEnv requires task_id — use a lazy wrapper instead of
#      instantiating at module load time with no task_id.
# ---------------------------------------------------------------------------

class _EnvSession:
    """
    Thin stateful wrapper around DataPipelineEnv.
    Holds the current task_id + seed so reset() can recreate the env
    without needing task_id passed to __init__.
    """
    def __init__(self):
        self._task_id = "task_easy_schema_fix"
        self._seed    = 42
        self._env: Optional[DataPipelineEnv] = None

    def reset(self, task_id: str, seed: int) -> Any:
        self._task_id = task_id
        self._seed    = seed
        self._env     = DataPipelineEnv(task_id=task_id, seed=seed)
        return self._env.reset()

    def step(self, action: Action) -> Any:
        if self._env is None:
            raise RuntimeError("Call /reset before /step.")
        return self._env.step(action)

    def state(self) -> Any:
        if self._env is None:
            raise RuntimeError("Call /reset before /state.")
        return self._env.state

    def tasks(self) -> list:
        return TASK_INFO


_session = _EnvSession()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ResetRequest(BaseModel):
    task_id: Optional[str] = "task_easy_schema_fix"
    seed:    Optional[int] = 42

    class Config:
        extra = "allow"


class StepRequest(BaseModel):
    action_type: str
    column:      Optional[str]            = None
    value:       Optional[str]            = None
    parameters:  Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "env": "data-pipeline-debugger", "version": "1.0.0"}


@app.get("/tasks")
def list_tasks():
    """List all available tasks with metadata."""
    return {"tasks": _session.tasks()}


@app.post("/reset")
def reset(req: Optional[ResetRequest] = None):
    """
    Reset the environment for a given task. Returns initial Observation.
    Accepts empty body {}, no body, or {task_id, seed}.
    """
    task_id = (req.task_id if req and req.task_id else None) or "task_easy_schema_fix"
    seed    = (req.seed    if req and req.seed is not None else None)
    seed    = seed if seed is not None else 42

    if task_id not in TASK_REGISTRY:
        valid = list(TASK_REGISTRY.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Unknown task_id {task_id!r}. Valid: {valid}",
        )

    try:
        obs = _session.reset(task_id=task_id, seed=seed)
        return obs.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


import math
import pandas as pd

def _sanitize_for_json(obj):
    """Recursively replaces NaN, Inf, and pd.NA with None for strict JSON serialization."""
    # pd.NA from nullable Int64/Float64 is not JSON serializable
    if obj is pd.NA:
        return None
    try:
        if pd.isna(obj):
            return None
    except (ValueError, TypeError):
        pass
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {str(k): _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [_sanitize_for_json(v) for v in obj]
    else:
        # Fallback for numpy float/int scalars escaping standard isinstance
        if hasattr(obj, 'item') and callable(getattr(obj, 'item')):
            val = obj.item()
            if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                return None
            return val
    return obj


@app.post("/step")
def step(req: StepRequest):
    """
    Apply an action. Returns StepResult:
      { observation, reward, done, info }
    """
    try:
        action_type = ActionType(req.action_type)
    except ValueError:
        valid = [a.value for a in ActionType]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action_type {req.action_type!r}. Valid: {valid}",
        )

    action = Action(
        action_type=action_type,
        column=req.column,
        value=req.value,
        parameters=req.parameters,
    )

    try:
        obs = _session.step(action)
        last_reward = 0.0
<<<<<<< HEAD
        if _session._env and _session._env.history:
            last_reward = _session._env.history[-1].reward
=======
        last_rec = None
        if _session._env and _session._env.history:
            last_rec = _session._env.history[-1]
            last_reward = last_rec.reward
>>>>>>> 03d62d9 (updated the demo and dashboard file and added the training using the grpo)

        # Wrap in StepResult shape for backward compatibility with inference.py
        payload = {
            "observation": obs.model_dump(),
            "reward": {
                "value":       last_reward,
                "cumulative":  _session._env._cumulative_reward if _session._env else 0.0,
<<<<<<< HEAD
                "components":  {},
=======
                "components":  last_rec.reward_components if last_rec else {},
>>>>>>> 03d62d9 (updated the demo and dashboard file and added the training using the grpo)
                "explanation": obs.hint,
            },
            "done": obs.done,
            "info": {
                "hint":         obs.hint,
                "step_count":   obs.step_count,
                "action_result": obs.hint,
            },
<<<<<<< HEAD
=======
            # Explainability fields
            "explainability": {
                "reasoning":          last_rec.reasoning if last_rec else "",
                "observation_summary": last_rec.observation_summary if last_rec else "",
                "reward_components":  last_rec.reward_components if last_rec else {},
                "alternatives":       last_rec.alternatives if last_rec else [],
            } if last_rec else None,
>>>>>>> 03d62d9 (updated the demo and dashboard file and added the training using the grpo)
        }
        return _sanitize_for_json(payload)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/state")
def state():
    """Return full internal PipelineState."""
    try:
        s = _session.state()
        if s is None:
            raise HTTPException(status_code=400, detail="Call /reset first.")
        return s.model_dump()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/")
def root():
    task_ids = [t["task_id"] for t in _session.tasks()]
    return {
        "name":        "OpenEnv — Data Pipeline Debugger",
        "version":     "1.0.0",
        "description": "Debug broken ETL pipelines. Real-world agent benchmark.",
        "endpoints": {
            "GET  /health":       "Health check",
            "GET  /tasks":        "List all tasks",
            "POST /reset":        "Reset environment for a task",
            "POST /step":         "Apply an action",
            "GET  /state":        "Get full internal state",
            "GET  /dashboard":    "Interactive web dashboard",
            "GET  /demo":         "Auto-running demo presentation",
            "GET  /compete":      "Multi-agent competition mode",
            "GET  /api/benchmark": "Run benchmark comparison",
            "GET  /docs":         "Interactive API docs (Swagger)",
        },
        "tasks": task_ids,
    }


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    """Serve the interactive web dashboard."""
    from dashboard import get_dashboard_html
    return HTMLResponse(content=get_dashboard_html(), status_code=200)

@app.get("/demo", response_class=HTMLResponse)
def demo_mode():
    """Serve the standalone auto-demo presentation."""
    from demo import get_demo_html
    return HTMLResponse(content=get_demo_html(), status_code=200)
    try:
        from demo import get_demo_html
        return HTMLResponse(content=get_demo_html(), status_code=200)
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"[ERROR] /demo failed: {e}\n{tb}", flush=True)
        return HTMLResponse(
            content=f"<html><body><h1>Demo Error</h1><pre>{tb}</pre></body></html>",
            status_code=500,
        )

@app.get("/compete", response_class=HTMLResponse)
def compete_mode():
    """Serve the side-by-side competition mode."""
    from compete import get_compete_html
    return HTMLResponse(content=get_compete_html(), status_code=200)
    try:
        from compete import get_compete_html
        return HTMLResponse(content=get_compete_html(), status_code=200)
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"[ERROR] /compete failed: {e}\n{tb}", flush=True)
        return HTMLResponse(
            content=f"<html><body><h1>Compete Error</h1><pre>{tb}</pre></body></html>",
            status_code=500,
        )


@app.get("/api/benchmark")
def run_benchmark_api():
    """Run benchmark comparison agents and return results as JSON."""
    try:
        from benchmarks.run_benchmarks import run_all_benchmarks
        results = run_all_benchmarks(episodes=2)
        return {"status": "ok", "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e), "results": []}


@app.get("/api/replay")
def get_replay():
    """Return full step history with explainability data for the last episode."""
    if _session._env is None or not _session._env.history:
        return {"steps": [], "task_id": None}
    return _sanitize_for_json({
        "task_id": _session._task_id,
        "steps": [rec.to_dict() for rec in _session._env.history],
    })


# ---------------------------------------------------------------------------
# Feature 2: WebSocket live training stream
# ---------------------------------------------------------------------------
_ws_clients: list[WebSocket] = []

@app.websocket("/ws/train")
async def ws_train(websocket: WebSocket):
    """Stream live training scores to the dashboard."""
    await websocket.accept()
    _ws_clients.append(websocket)
    try:
        while True:
            # Keep connection alive; client can send 'ping'
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        _ws_clients.remove(websocket)


async def broadcast_training_event(event: dict):
    """Called by training loops to push live updates to all connected dashboards."""
    dead = []
    for ws in _ws_clients:
        try:
            await ws.send_json(event)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _ws_clients.remove(ws)


@app.post("/api/train-episode")
async def train_episode_api():
    """Run one training episode and stream scores via WebSocket."""
    import random
    task_ids = list(TASK_REGISTRY.keys())
    task_id = random.choice(task_ids)
    seed = random.randint(1, 9999)

    env = DataPipelineEnv(task_id=task_id, seed=seed)
    obs = env.reset()

    actions_sequence = [
        "inspect", "cast_column", "drop_duplicates", "fill_nulls",
        "filter_outliers", "validate", "submit"
    ]

    episode_reward = 0.0
    step_num = 0
    done = False

    for act_name in actions_sequence:
        if done:
            break
        act = Action(action_type=ActionType(act_name))
        if act_name == "cast_column" and obs.schema_info:
            act.column = obs.schema_info[0].name
            act.value = obs.schema_info[0].expected_type
        elif act_name == "fill_nulls" and obs.schema_info:
            act.column = obs.schema_info[0].name
            act.value = "0"
        elif act_name == "filter_outliers" and obs.schema_info:
            for sf in obs.schema_info:
                if sf.expected_type in ("int", "float", "int64", "float64"):
                    act.column = sf.name
                    break
            if not act.column and obs.schema_info:
                act.column = obs.schema_info[0].name
            act.value = "0,99999"

        try:
            obs = env.step(act)
        except Exception:
            break
        step_num += 1
        done = obs.done
        if env.history:
            episode_reward = env.history[-1].cumulative_reward

        # Broadcast each step live
        await broadcast_training_event({
            "type": "step",
            "task_id": task_id,
            "step": step_num,
            "action": act_name,
            "reward": round(env.history[-1].reward, 4) if env.history else 0,
            "cumulative": round(episode_reward, 4),
        })
        await asyncio.sleep(0.15)  # Pacing for visual effect

    # Broadcast episode summary
    await broadcast_training_event({
        "type": "episode_end",
        "task_id": task_id,
        "total_steps": step_num,
        "final_score": round(episode_reward, 4),
    })
    return {"status": "ok", "task_id": task_id, "score": round(episode_reward, 4), "steps": step_num}


# ---------------------------------------------------------------------------
# Feature 3: CSV upload + auto-debug
# ---------------------------------------------------------------------------

@app.post("/api/upload-debug")
async def upload_debug(file: UploadFile = File(...)):
    """
    Upload a CSV file. The agent will auto-debug it using the easy schema task
    as a template, but with the user's data injected.
    Returns step-by-step debug results.
    """
    import pandas as pd

    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        return {"status": "error", "message": f"Failed to parse CSV: {e}", "steps": []}

    if len(df) == 0:
        return {"status": "error", "message": "CSV is empty.", "steps": []}

    # Create a custom environment with the user's data
    task_id = "task_easy_schema_fix"  # Use as template
    env = DataPipelineEnv(task_id=task_id, seed=42)
    obs = env.reset()

    # Inject user's data into the environment
    from env.environment import _df_to_data, _recompute_metrics
    env._df = df
    env.state.data = _df_to_data(df)
    # Build schema from CSV columns
    from env.models import SchemaField
    env.state.schema_info = [
        SchemaField(name=col, expected_type=str(df[col].dtype), actual_type=str(df[col].dtype))
        for col in df.columns
    ]
    env.state.metrics = _recompute_metrics(env.state.data, env.state.schema_info)

    # Auto-debug sequence
    actions_seq = ["inspect", "drop_duplicates", "validate"]
    # Add fill_nulls for columns with nulls
    for col in df.columns:
        if df[col].isnull().any():
            actions_seq.insert(2, "fill_nulls")
            break

    results = []
    for act_name in actions_seq:
        act = Action(action_type=ActionType(act_name))
        if act_name == "fill_nulls":
            for col in df.columns:
                if df[col].isnull().any():
                    act.column = col
                    act.value = "0"
                    break
        try:
            obs = env.step(act)
        except Exception as e:
            results.append({"action": act_name, "error": str(e)})
            break

        rec = env.history[-1] if env.history else None
        results.append({
            "step": len(results) + 1,
            "action": act_name,
            "description": rec.description if rec else "",
            "reasoning": rec.reasoning if rec else "",
            "reward": round(rec.reward, 4) if rec else 0,
            "observation_summary": rec.observation_summary if rec else "",
            "bugs_remaining": rec.bugs_remaining if rec else 0,
        })

    # Final submit
    try:
        act = Action(action_type=ActionType.SUBMIT)
        obs = env.step(act)
        rec = env.history[-1]
        results.append({
            "step": len(results) + 1,
            "action": "submit",
            "description": rec.description,
            "reasoning": rec.reasoning,
            "reward": round(rec.reward, 4),
            "observation_summary": rec.observation_summary,
            "bugs_remaining": rec.bugs_remaining,
        })
    except Exception:
        pass

    return _sanitize_for_json({
        "status": "ok",
        "filename": file.filename,
        "rows": len(df),
        "columns": list(df.columns),
        "null_counts": {col: int(df[col].isnull().sum()) for col in df.columns},
        "duplicate_count": int(df.duplicated().sum()),
        "steps": results,
        "final_score": round(env._cumulative_reward, 4),
    })


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
