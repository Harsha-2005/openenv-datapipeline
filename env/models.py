"""
OpenEnv Data Pipeline Debugger — Typed Models
All Observation, Action, Reward, and State models following OpenEnv spec.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ActionType(str, Enum):
    INSPECT          = "inspect"
    CAST_COLUMN      = "cast_column"
    DROP_NULLS       = "drop_nulls"
    FILL_NULLS       = "fill_nulls"
    DROP_DUPLICATES  = "drop_duplicates"
    FILTER_OUTLIERS  = "filter_outliers"
    RENAME_COLUMN    = "rename_column"
    REORDER_STAGES   = "reorder_stages"
    APPLY_BUSINESS_RULE = "apply_business_rule"
    VALIDATE         = "validate"
    SUBMIT           = "submit"


class Difficulty(str, Enum):
    EASY   = "easy"
    MEDIUM = "medium"
    HARD   = "hard"


class PipelineStage(str, Enum):
    INGEST    = "ingest"
    VALIDATE  = "validate"
    TRANSFORM = "transform"
    ENRICH    = "enrich"
    LOAD      = "load"
    COMPLETE  = "complete"


# ---------------------------------------------------------------------------
# Action
# ---------------------------------------------------------------------------

class Action(BaseModel):
    """Action the agent takes at each step."""
    action_type: ActionType = Field(..., description="Type of action to perform")
    column: Optional[str]   = Field(None, description="Column name to operate on")
    value: Optional[str]    = Field(None, description="Value or type string (e.g. 'int', 'float', '0')")
    parameters: Optional[Dict[str, Any]] = Field(
        None, description="Extra parameters for complex actions"
    )

    model_config = ConfigDict(use_enum_values=True)


# ---------------------------------------------------------------------------
# Observation
# ---------------------------------------------------------------------------

class SchemaField(BaseModel):
    name: str
    expected_type: str
    actual_type: str
    nullable: bool = True


class PipelineMetrics(BaseModel):
    completeness: float = Field(0.0, ge=0.0, le=1.0, description="Fraction of non-null values")
    uniqueness:   float = Field(0.0, ge=0.0, le=1.0, description="Fraction of unique rows")
    validity:     float = Field(0.0, ge=0.0, le=1.0, description="Fraction passing all rules")
    accuracy:     float = Field(0.0, ge=0.0, le=1.0, description="Schema-correct fraction")
    sla_latency_ms: float = Field(0.0, description="Simulated processing latency in ms")


class Observation(BaseModel):
    """Full observation returned after reset() or step()."""
    task_id:          str                     = Field(..., description="Current task identifier")
    step_count:       int                     = Field(0,   description="Steps taken so far")
    max_steps:        int                     = Field(10,  description="Max steps before truncation")
    pipeline_stage:   str                     = Field("ingest", description="Current pipeline stage")
    data_sample:      List[Dict[str, Any]]    = Field(default_factory=list, description="Up to 5 sample rows")
    schema_info:      List[SchemaField]       = Field(default_factory=list, description="Schema field info")
    error_log:        List[str]               = Field(default_factory=list, description="Accumulated errors")
    metrics:          PipelineMetrics         = Field(default_factory=PipelineMetrics)
    available_actions: List[str]              = Field(default_factory=list)
    hint:             str                     = Field("", description="Optional guidance hint")
    done:             bool                    = Field(False)


# ---------------------------------------------------------------------------
# Reward
# ---------------------------------------------------------------------------

class Reward(BaseModel):
    """Reward signal returned with each step."""
    value:       float = Field(..., ge=-1.0, le=1.0, description="Step reward")
    cumulative:  float = Field(0.0,  description="Total reward so far")
    components:  Dict[str, float] = Field(
        default_factory=dict,
        description="Breakdown: completeness, uniqueness, validity, accuracy, efficiency"
    )
    explanation: str = Field("", description="Human-readable explanation of reward")


# ---------------------------------------------------------------------------
# State (internal, returned by state())
# ---------------------------------------------------------------------------

class PipelineState(BaseModel):
    """Full internal state (superset of Observation)."""
    task_id:        str
    step_count:     int
    max_steps:      int
    pipeline_stage: str
    data:           List[Dict[str, Any]]   # full dataset (not just sample)
    schema_info:    List[SchemaField]
    error_log:      List[str]
    metrics:        PipelineMetrics
    cumulative_reward: float
    done:           bool
    applied_actions: List[str]
    bugs_fixed:     Dict[str, bool]       # tracks which bugs have been addressed
    target_metrics: Dict[str, float]      # thresholds agent must reach
    stage_order:    List[str]             # for hard task: current stage ordering


# ---------------------------------------------------------------------------
# Step response
# ---------------------------------------------------------------------------

class StepResult(BaseModel):
    observation: Observation
    reward:      Reward
    done:        bool
    info:        Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Task descriptor
# ---------------------------------------------------------------------------

class TaskInfo(BaseModel):
    task_id:     str
    name:        str
    difficulty:  str
    description: str
    max_steps:   int
