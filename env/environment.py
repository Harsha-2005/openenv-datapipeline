"""
env/environment.py  —  OpenEnv Data Pipeline Debugger
=======================================================
Root-cause fix: Observation model requires task_id, step_count, max_steps,
pipeline_stage, data_sample, schema_info, error_log, metrics,
available_actions, hint, done.  It has NO success/message/reward/score fields.

All action dispatch now builds correct Observation objects from PipelineState.
StepRecord + env.history preserved for Replay Dashboard.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

import pandas as pd

from env.models import (
    Action,
    ActionType,
    Observation,
    PipelineMetrics,
    PipelineState,
    SchemaField,
)


# ─────────────────────────────────────────────────────────────────────────────
# StepRecord  — replay dashboard history entry
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class StepRecord:
    """One step snapshot for the Replay Dashboard."""
    step:              int
    action:            str
    params:            dict
    reward:            float
    cumulative_reward: float
    bugs_remaining:    int
    description:       str
    timestamp_ms:      float = field(default_factory=lambda: time.time() * 1000)

    def to_dict(self) -> dict:
        return {
            "step":              self.step,
            "action":            self.action,
            "params":            self.params,
            "reward":            round(self.reward, 4),
            "cumulative_reward": round(self.cumulative_reward, 4),
            "bugs_remaining":    self.bugs_remaining,
            "description":       self.description,
            "timestamp_ms":      round(self.timestamp_ms, 1),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Internal action result  (private — never returned to callers)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class _ActionResult:
    reward:      float
    message:     str
    score:       Optional[float] = None
    done:        bool            = False
    error_lines: List[str]       = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _clip(v: float) -> float:
    return max(0.001, min(0.999, v))


def _df_to_data(df: pd.DataFrame) -> List[dict]:
    return df.where(pd.notnull(df), None).to_dict(orient="records")


def _recompute_metrics(data: List[dict], schema: List[SchemaField]) -> PipelineMetrics:
    if not data:
        return PipelineMetrics()
    total = len(data)
    cols  = [s.name for s in schema]

    non_null     = sum(1 for row in data for c in cols if row.get(c) is not None)
    completeness = non_null / (total * len(cols)) if cols else 0.0

    seen, unique = set(), 0
    for row in data:
        key = tuple(sorted((k, str(v)) for k, v in row.items()))
        if key not in seen:
            seen.add(key); unique += 1
    uniqueness = unique / total

    import random
    return PipelineMetrics(
        completeness  = round(min(1.0, completeness), 4),
        uniqueness    = round(min(1.0, uniqueness),   4),
        validity      = round(min(1.0, completeness * uniqueness), 4),
        accuracy      = round(min(1.0, completeness), 4),
        sla_latency_ms= round(random.uniform(10, 80), 2),
    )


def _bug_count_df(df: pd.DataFrame, task_cfg: dict) -> int:
    count = int(df.isnull().any(axis=None)) + int(df.duplicated().any())
    for col, dtype in task_cfg.get("expected_schema", {}).items():
        if col in df.columns and str(df[col].dtype) != dtype:
            count += 1
    for rule in task_cfg.get("business_rules", []):
        if rule == "discount_lte_1" and "discount_pct" in df.columns:
            count += int((pd.to_numeric(df["discount_pct"], errors="coerce") > 1).any())
        elif rule == "fraud_score_lte_1" and "fraud_score" in df.columns:
            count += int((pd.to_numeric(df["fraud_score"], errors="coerce") > 1).any())
        elif rule == "currency_3char" and "currency" in df.columns:
            count += int(df["currency"].dropna().str.len().ne(3).any())
        elif rule == "country_2char" and "country_code" in df.columns:
            count += int(df["country_code"].dropna().str.len().ne(2).any())
    return count


def _describe(action: str, params: dict, result: _ActionResult) -> str:
    a = action
    if a == "inspect":            return f"Inspected state. {result.message}"
    if a == "cast_column":        return f'Cast "{params.get("column","?")}" → {params.get("dtype","?")}.'
    if a == "drop_nulls":         return f'Dropped null rows in "{params.get("column","all")}".'
    if a == "fill_nulls":         return f'Filled nulls in "{params.get("column","?")}" with {params.get("value","median")}.'
    if a == "drop_duplicates":    return f"Removed duplicates. {result.message}"
    if a == "filter_outliers":    return f'Filtered outliers in "{params.get("column","?")}". {result.message}'
    if a == "rename_column":      return f'Renamed "{params.get("old_name","?")}" → "{params.get("new_name","?")}".'
    if a == "reorder_stages":     return f'Stage order set to {params.get("order",[])}.'
    if a == "apply_business_rule":return f'Rule "{params.get("rule","?")}": {result.message}'
    if a == "validate":           return f"Validated. Score: {result.score:.4f}." if result.score else "Validated."
    if a == "submit":             return f"Submitted. Final score: {result.score:.4f}." if result.score else "Submitted."
    return f"{action}: {result.message}"


def _make_observation(state: PipelineState, hint: str = "") -> Observation:
    """Build a valid Observation from current PipelineState."""
    return Observation(
        task_id         = state.task_id,
        step_count      = state.step_count,
        max_steps       = state.max_steps,
        pipeline_stage  = state.pipeline_stage,
        data_sample     = state.data[:5],
        schema_info     = state.schema_info,
        error_log       = state.error_log[-10:],   # last 10 errors only
        metrics         = state.metrics,
        available_actions = [a.value for a in ActionType],
        hint            = hint,
        done            = state.done,
    )


# ─────────────────────────────────────────────────────────────────────────────
# DataPipelineEnv
# ─────────────────────────────────────────────────────────────────────────────

class DataPipelineEnv:
    """
    Core RL environment. Returns proper Observation objects on reset()/step().

    Public attributes
    -----------------
    state   : PipelineState | None
    history : list[StepRecord]   — populated each step, cleared on reset()
    """

    STEP_COST      = -0.02
    REPEAT_PENALTY = -0.05
    SUBMIT_BONUS   =  0.10

    def __init__(self, task_id: str, seed: int = 42):
        self.task_id = task_id
        self.seed    = seed
        self.state:  PipelineState | None = None
        self._df:    pd.DataFrame | None  = None

        self._cumulative_reward = 0.0
        self._step_count        = 0
        self._last_actions:     list[str]      = []
        self.history:           list[StepRecord] = []

    # ── lifecycle ─────────────────────────────────────────────────────────────

    def reset(self) -> Observation:
        from tasks.definitions import TASK_REGISTRY
        if self.task_id not in TASK_REGISTRY:
            raise KeyError(f"Unknown task '{self.task_id}'. "
                           f"Available: {list(TASK_REGISTRY.keys())}")

        self.state             = TASK_REGISTRY[self.task_id].build_state(seed=self.seed)
        self._df               = pd.DataFrame(self.state.data)
        self._cumulative_reward = 0.0
        self._step_count        = 0
        self._last_actions      = []
        self.history            = []

        return _make_observation(self.state, hint="Environment ready.")

    def step(self, action: Action) -> Observation:
        if self.state is None:
            raise RuntimeError("Call reset() before step().")

        self._step_count    += 1
        self.state.step_count = self._step_count

        # Support both .action_type (enum) and raw string
        if hasattr(action, "action_type"):
            raw_action = action.action_type
            if hasattr(raw_action, "value"):
                raw_action = raw_action.value
        else:
            raw_action = str(action)

        # Build params dict from Action fields
        params = {}
        if hasattr(action, "params") and action.params:
            params = action.params
        else:
            if getattr(action, "column", None):    params["column"]   = action.column
            if getattr(action, "value", None):     params["value"]    = action.value
            if getattr(action, "parameters", None): params.update(action.parameters or {})

        # Repeat penalty
        repeat = self._last_actions.count(raw_action) > 0
        self._last_actions.append(raw_action)
        if len(self._last_actions) > 5:
            self._last_actions.pop(0)

        # Dispatch
        result = self._dispatch(raw_action, params)

        # Compute final reward
        reward = result.reward + self.STEP_COST
        if repeat and raw_action not in ("validate", "submit"):
            reward += self.REPEAT_PENALTY
        self._cumulative_reward    += reward
        self.state.cumulative_reward = self._cumulative_reward

        # Sync df → state.data and recompute metrics
        if self._df is not None:
            self.state.data    = _df_to_data(self._df)
            self.state.metrics = _recompute_metrics(self.state.data, self.state.schema_info)

        # Terminal
        done = result.done or self._step_count >= self.state.max_steps
        self.state.done = done

        # Bug count for history
        task_cfg = self._get_task_cfg()
        bugs = _bug_count_df(self._df, task_cfg) if self._df is not None else 0

        # Append error lines to state
        if result.error_lines:
            self.state.error_log.extend(result.error_lines)

        # StepRecord
        desc = _describe(raw_action, params, result)
        self.history.append(StepRecord(
            step              = self._step_count,
            action            = raw_action,
            params            = params,
            reward            = reward,
            cumulative_reward = _clip(self._cumulative_reward),
            bugs_remaining    = bugs,
            description       = desc,
        ))

        return _make_observation(self.state, hint=result.message)

    # ── dispatch ──────────────────────────────────────────────────────────────

    def _dispatch(self, action: str, params: dict) -> _ActionResult:
        df = self._df

        # ── inspect ──
        if action == ActionType.INSPECT.value:
            nulls = int(df.isnull().sum().sum())
            dups  = int(df.duplicated().sum())
            msg   = f"Rows:{len(df)} Cols:{len(df.columns)} Nulls:{nulls} Dups:{dups}"
            return _ActionResult(reward=0.0, message=msg)

        # ── cast_column ──
        if action == ActionType.CAST_COLUMN.value:
            col   = params.get("column") or params.get("col")
            dtype = params.get("dtype")  or params.get("type")
            if not col or col not in df.columns:
                return _ActionResult(reward=-0.01, message=f"Column '{col}' not found.")
            try:
                self._df[col] = df[col].astype(dtype)
                return _ActionResult(reward=0.06, message=f"Cast '{col}'→{dtype}.")
            except Exception as e:
                return _ActionResult(reward=-0.01, message=str(e))

        # ── drop_nulls ──
        if action == ActionType.DROP_NULLS.value:
            col    = params.get("column")
            before = len(df)
            self._df = df.dropna(subset=[col]) if col and col in df.columns else df.dropna()
            dropped  = before - len(self._df)
            return _ActionResult(
                reward  = 0.06 if dropped else -0.01,
                message = f"Dropped {dropped} null rows.",
            )

        # ── fill_nulls ──
        if action == ActionType.FILL_NULLS.value:
            col   = params.get("column")
            value = params.get("value", "median")
            if not col or col not in df.columns:
                return _ActionResult(reward=-0.01, message=f"Column '{col}' not found.")
            num = pd.to_numeric(df[col], errors="coerce")
            fill_val = num.median() if value == "median" else value
            self._df[col] = df[col].fillna(fill_val)
            return _ActionResult(reward=0.08, message=f"Filled nulls in '{col}' with {fill_val}.")

        # ── drop_duplicates ──
        if action == ActionType.DROP_DUPLICATES.value:
            before   = len(df)
            self._df = df.drop_duplicates()
            dropped  = before - len(self._df)
            return _ActionResult(
                reward  = 0.08 if dropped else -0.01,
                message = f"Removed {dropped} duplicates.",
            )

        # ── filter_outliers ──
        if action == ActionType.FILTER_OUTLIERS.value:
            col = params.get("column")
            if not col or col not in df.columns:
                return _ActionResult(reward=-0.01, message=f"Column '{col}' not found.")
            num = pd.to_numeric(df[col], errors="coerce")
            q1, q3   = num.quantile(0.25), num.quantile(0.75)
            iqr      = q3 - q1
            mask     = num.between(q1 - 1.5*iqr, q3 + 1.5*iqr) | num.isna()
            before   = len(df)
            self._df = df[mask]
            removed  = before - len(self._df)
            return _ActionResult(
                reward  = 0.08 if removed else -0.01,
                message = f"Removed {removed} outliers from '{col}'.",
            )

        # ── rename_column ──
        if action == ActionType.RENAME_COLUMN.value:
            old = params.get("old_name") or params.get("old")
            new = params.get("new_name") or params.get("new")
            if not old or old not in df.columns:
                return _ActionResult(reward=-0.01, message=f"Column '{old}' not found.")
            self._df = df.rename(columns={old: new})
            return _ActionResult(reward=0.06, message=f"Renamed '{old}'→'{new}'.")

        # ── reorder_stages ──
        if action == ActionType.REORDER_STAGES.value:
            order = params.get("order", [])
            self.state.stage_order = order
            correct = ["ingest","validate","transform","enrich","load"]
            reward  = 0.12 if order == correct else 0.02
            return _ActionResult(reward=reward, message=f"Stage order set to {order}.")

        # ── apply_business_rule ──
        if action == ActionType.APPLY_BUSINESS_RULE.value:
            rule = params.get("rule", "")
            return self._apply_rule(rule)

        # ── validate ──
        if action == ActionType.VALIDATE.value:
            score = self._score_current()
            return _ActionResult(reward=0.02, message=f"Score: {score:.4f}", score=score)

        # ── submit ──
        if action == ActionType.SUBMIT.value:
            score = _clip(self._score_current())
            return _ActionResult(
                reward  = self.SUBMIT_BONUS * score,
                message = f"Final score: {score:.4f}",
                score   = score,
                done    = True,
            )

        return _ActionResult(reward=-0.01, message=f"Unknown action: {action}")

    # ── business rules ────────────────────────────────────────────────────────

    def _apply_rule(self, rule: str) -> _ActionResult:
        df = self._df
        if rule == "discount_lte_1" and "discount_pct" in df.columns:
            vals = pd.to_numeric(df["discount_pct"], errors="coerce")
            n    = int((vals > 1).sum())
            self._df["discount_pct"] = vals.clip(upper=1.0)
            return _ActionResult(reward=0.10 if n else -0.01, message=f"Clipped {n} discount rows.")

        if rule == "fraud_score_lte_1" and "fraud_score" in df.columns:
            vals = pd.to_numeric(df["fraud_score"], errors="coerce")
            n    = int((vals > 1).sum())
            self._df["fraud_score"] = vals.clip(upper=1.0)
            return _ActionResult(reward=0.10 if n else -0.01, message=f"Clipped {n} fraud_score rows.")

        if rule == "currency_3char" and "currency" in df.columns:
            mask = df["currency"].dropna().str.len().ne(3)
            n    = int(mask.sum())
            self._df.loc[df["currency"].notna() & df["currency"].str.len().ne(3), "currency"] = \
                df.loc[df["currency"].notna() & df["currency"].str.len().ne(3), "currency"].str[:3].str.upper()
            return _ActionResult(reward=0.10 if n else -0.01, message=f"Fixed {n} currency codes.")

        if rule == "country_2char" and "country_code" in df.columns:
            mask = df["country_code"].dropna().str.len().ne(2)
            n    = int(mask.sum())
            self._df.loc[df["country_code"].notna() & df["country_code"].str.len().ne(2), "country_code"] = \
                df.loc[df["country_code"].notna() & df["country_code"].str.len().ne(2), "country_code"].str[:2].str.upper()
            return _ActionResult(reward=0.10 if n else -0.01, message=f"Fixed {n} country codes.")

        return _ActionResult(reward=-0.01, message=f"Rule '{rule}' had no effect.")

    # ── scoring ───────────────────────────────────────────────────────────────

    def _score_current(self) -> float:
        from graders.graders import score_pipeline
        if self._df is not None:
            self.state.data    = _df_to_data(self._df)
            self.state.metrics = _recompute_metrics(self.state.data, self.state.schema_info)
        return score_pipeline(self.state, self.task_id)

    def _get_task_cfg(self) -> dict:
        try:
            from tasks.definitions import TASK_REGISTRY
            return TASK_REGISTRY[self.task_id].config
        except Exception:
            return {}