"""
OpenEnv Data Pipeline Debugger — FastAPI Application
Exposes reset(), step(), state() as REST endpoints.

Fix applied: DataPipelineEnv now requires task_id as first arg.
_env is now a stateful session manager that tracks current task_id + seed.
"""

from __future__ import annotations
import os
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
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
        if _session._env and _session._env.history:
            last_reward = _session._env.history[-1].reward

        # Wrap in StepResult shape for backward compatibility with inference.py
        payload = {
            "observation": obs.model_dump(),
            "reward": {
                "value":       last_reward,
                "cumulative":  _session._env._cumulative_reward if _session._env else 0.0,
                "components":  {},
                "explanation": obs.hint,
            },
            "done": obs.done,
            "info": {
                "hint":         obs.hint,
                "step_count":   obs.step_count,
                "action_result": obs.hint,
            },
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

@app.get("/compete", response_class=HTMLResponse)
def compete_mode():
    """Serve the side-by-side competition mode."""
    from compete import get_compete_html
    return HTMLResponse(content=get_compete_html(), status_code=200)


@app.get("/api/benchmark")
def run_benchmark_api():
    """Run benchmark comparison agents and return results as JSON."""
    try:
        from benchmarks.run_benchmarks import run_all_benchmarks
        results = run_all_benchmarks(episodes=2)
        return {"status": "ok", "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e), "results": []}


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)