"""
Graders for all three tasks.
Each grader returns a float strictly in (0.0, 1.0) — open interval.
0.0 and 1.0 are NOT valid scores per hackathon spec.
Graders are deterministic and do not mutate state.
"""

from __future__ import annotations
from env.models import PipelineState

# Strict open interval bounds required by evaluator
_SCORE_MIN = 0.001
_SCORE_MAX = 0.999


def _clip(score: float) -> float:
    """Clip score to strictly open interval (0, 1) — never 0.0 or 1.0."""
    return round(min(_SCORE_MAX, max(_SCORE_MIN, score)), 4)


def _metric_score(actual: float, target: float) -> float:
    """Returns 0→1 based on how close actual is to target."""
    if target <= 0:
        return 1.0
    return min(1.0, actual / target)


# ---------------------------------------------------------------------------
# Easy Task Grader — Schema Mismatch Fix
# ---------------------------------------------------------------------------

def grade_easy(state: PipelineState) -> float:
    """
    Scoring components:
      40%  bugs_fixed ratio
      30%  accuracy metric
      20%  completeness
      10%  efficiency bonus (≤5 steps)
    Score clipped to strictly open interval (0.001, 0.999).
    """
    bugs      = state.bugs_fixed
    n_bugs    = len(bugs)
    n_fixed   = sum(1 for v in bugs.values() if v)
    bug_ratio = n_fixed / n_bugs if n_bugs else 0.0

    acc_score  = _metric_score(state.metrics.accuracy,     0.90)
    comp_score = _metric_score(state.metrics.completeness, 0.85)
    eff_bonus  = 0.1 if state.step_count <= 5 else 0.0

    raw = (0.40 * bug_ratio) + (0.30 * acc_score) + (0.20 * comp_score) + eff_bonus
    return _clip(raw)


# ---------------------------------------------------------------------------
# Medium Task Grader — Data Quality Remediation
# ---------------------------------------------------------------------------

def grade_medium(state: PipelineState) -> float:
    """
    Scoring components:
      30%  bugs_fixed ratio
      25%  completeness ≥ 0.90
      25%  uniqueness   ≥ 0.95
      15%  validity     ≥ 0.88
       5%  efficiency bonus (≤10 steps)
    Score clipped to strictly open interval (0.001, 0.999).
    """
    bugs      = state.bugs_fixed
    bug_ratio = sum(1 for v in bugs.values() if v) / len(bugs) if bugs else 0.0

    comp_score  = _metric_score(state.metrics.completeness, 0.90)
    uniq_score  = _metric_score(state.metrics.uniqueness,   0.95)
    valid_score = _metric_score(state.metrics.validity,     0.88)
    eff_bonus   = 0.05 if state.step_count <= 10 else 0.0

    raw = (0.30 * bug_ratio + 0.25 * comp_score +
           0.25 * uniq_score + 0.15 * valid_score + eff_bonus)
    return _clip(raw)


# ---------------------------------------------------------------------------
# Hard Task Grader — Full Pipeline Orchestration Debug
# ---------------------------------------------------------------------------

def grade_hard(state: PipelineState) -> float:
    """
    Scoring components:
      20%  stage order correct
      25%  bugs_fixed ratio
      20%  completeness ≥ 0.92
      15%  uniqueness   ≥ 0.97
      10%  validity     ≥ 0.90
      10%  accuracy     ≥ 0.92
      Penalty: -0.05 if SLA latency > 100ms
    Score clipped to strictly open interval (0.001, 0.999).
    """
    correct_order = ["ingest", "validate", "transform", "enrich", "load"]
    order_score   = 1.0 if state.stage_order == correct_order else 0.0

    bugs      = state.bugs_fixed
    bug_ratio = sum(1 for v in bugs.values() if v) / len(bugs) if bugs else 0.0

    comp_score  = _metric_score(state.metrics.completeness, 0.92)
    uniq_score  = _metric_score(state.metrics.uniqueness,   0.97)
    valid_score = _metric_score(state.metrics.validity,     0.90)
    acc_score   = _metric_score(state.metrics.accuracy,     0.92)
    sla_penalty = -0.05 if state.metrics.sla_latency_ms > 100.0 else 0.0

    raw = (0.20 * order_score + 0.25 * bug_ratio +
           0.20 * comp_score  + 0.15 * uniq_score +
           0.10 * valid_score + 0.10 * acc_score +
           sla_penalty)
    return _clip(raw)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

GRADERS = {
    "task_easy_schema_fix":            grade_easy,
    "task_medium_data_quality":         grade_medium,
    "task_hard_pipeline_orchestration": grade_hard,
}


def grade(state: PipelineState) -> float:
    grader = GRADERS.get(state.task_id)
    if grader is None:
        raise ValueError(f"No grader registered for task_id={state.task_id!r}")
    return grader(state)