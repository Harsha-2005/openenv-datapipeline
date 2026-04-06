"""
OpenEnv Data Pipeline Debugger — FastAPI Application
Exposes reset(), step(), state() as REST endpoints.
"""

from __future__ import annotations
import os
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from env.environment import DataPipelineEnv
from env.models import Action, ActionType


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

# Single global environment instance (stateful per session)
_env = DataPipelineEnv(seed=42)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ResetRequest(BaseModel):
    task_id: str = "task_easy_schema_fix"
    seed:    Optional[int] = 42


class StepRequest(BaseModel):
    action_type: str
    column:      Optional[str]         = None
    value:       Optional[str]         = None
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
    return {"tasks": _env.tasks()}


@app.post("/reset")
def reset(req: ResetRequest):
    """Reset the environment for a given task. Returns initial Observation."""
    try:
        obs = _env.reset(task_id=req.task_id, seed=req.seed)
        return obs.dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
        result = _env.step(action)
        return result.dict()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/state")
def state():
    """Return full internal state (superset of observation)."""
    try:
        s = _env.state()
        return s.dict()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/")
def root():
    return {
        "name":        "OpenEnv — Data Pipeline Debugger",
        "version":     "1.0.0",
        "description": "Debug broken ETL pipelines. Real-world agent benchmark.",
        "endpoints": {
            "GET  /health":  "Health check",
            "GET  /tasks":   "List all tasks",
            "POST /reset":   "Reset environment for a task",
            "POST /step":    "Apply an action",
            "GET  /state":   "Get full internal state",
            "GET  /docs":    "Interactive API docs (Swagger)",
        },
        "tasks": [t["task_id"] for t in _env.tasks()],
    }


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
