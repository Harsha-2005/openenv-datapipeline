"""
Graders for all three tasks.
Each grader takes the current PipelineState and returns a float in [0.0, 1.0].
Graders are deterministic and do not mutate state.
"""

from __future__ import annotations
from env.models import PipelineState


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _metric_score(actual: float, target: float) -> float:
    """Returns 0.0→1.0 based on how close actual is to target (capped at 1.0)."""
    if target <= 0:
        return 1.0
    return min(1.0, actual / target)


# ---------------------------------------------------------------------------
# Easy Task Grader — Schema Mismatch Fix
# ---------------------------------------------------------------------------

def grade_easy(state: PipelineState) -> float:
    """
    Scoring components (each 0-1, weighted):
      40%  bugs_fixed ratio  (how many of the 5 schema bugs are fixed)
      30%  accuracy metric   (fraction of rows matching expected types)
      20%  completeness      (non-null ratio preserved or improved)
      10%  efficiency        (bonus for finishing in ≤5 steps)

    Final score: weighted sum, clipped to [0.0, 1.0].
    """
    bugs     = state.bugs_fixed
    n_bugs   = len(bugs)
    n_fixed  = sum(1 for v in bugs.values() if v)
    bug_ratio= n_fixed / n_bugs if n_bugs else 0.0

    acc_score  = _metric_score(state.metrics.accuracy,     0.90)
    comp_score = _metric_score(state.metrics.completeness, 0.85)
    eff_bonus  = 0.1 if state.step_count <= 5 else 0.0

    raw = (0.40 * bug_ratio) + (0.30 * acc_score) + (0.20 * comp_score) + eff_bonus
    return round(min(1.0, max(0.0, raw)), 4)


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
       5%  efficiency   (bonus: ≤10 steps)
    """
    bugs      = state.bugs_fixed
    bug_ratio = sum(1 for v in bugs.values() if v) / len(bugs)

    comp_score  = _metric_score(state.metrics.completeness, 0.90)
    uniq_score  = _metric_score(state.metrics.uniqueness,   0.95)
    valid_score = _metric_score(state.metrics.validity,     0.88)
    eff_bonus   = 0.05 if state.step_count <= 10 else 0.0

    raw = (0.30 * bug_ratio + 0.25 * comp_score +
           0.25 * uniq_score + 0.15 * valid_score + eff_bonus)
    return round(min(1.0, max(0.0, raw)), 4)


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
      Penalty: -0.05 per SLA breach if latency > 100ms

    Hard task deliberately challenging: requires ALL components to score > 0.9.
    """
    correct_order = ["ingest","validate","transform","enrich","load"]
    order_score = 1.0 if state.stage_order == correct_order else 0.0

    bugs      = state.bugs_fixed
    bug_ratio = sum(1 for v in bugs.values() if v) / len(bugs)

    comp_score  = _metric_score(state.metrics.completeness, 0.92)
    uniq_score  = _metric_score(state.metrics.uniqueness,   0.97)
    valid_score = _metric_score(state.metrics.validity,     0.90)
    acc_score   = _metric_score(state.metrics.accuracy,     0.92)

    sla_penalty = -0.05 if state.metrics.sla_latency_ms > 100.0 else 0.0

    raw = (0.20 * order_score + 0.25 * bug_ratio +
           0.20 * comp_score  + 0.15 * uniq_score +
           0.10 * valid_score  + 0.10 * acc_score +
           sla_penalty)
    return round(min(1.0, max(0.0, raw)), 4)


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
