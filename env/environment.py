"""
DataPipelineEnv — Core environment engine.
Implements reset(), step(), state() following OpenEnv spec.
"""

from __future__ import annotations
import copy
import random
from typing import Any, Dict, List, Optional, Tuple

from env.models import (
    Action, ActionType, Observation, PipelineMetrics,
    PipelineState, Reward, SchemaField, StepResult,
)
from tasks.definitions import TASK_BUILDERS, TASK_INFO
from graders.graders import grade
from tasks.definitions import (
    MEDIUM_RULES, HARD_RULES,
    _compute_metrics, HARD_STAGE_ORDER_CORRECT, HARD_WRONG_STAGE_ORDER,
)


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

class DataPipelineEnv:
    """
    OpenEnv-compliant environment for Data Pipeline Debugging.

    Lifecycle:
        env = DataPipelineEnv()
        obs = env.reset(task_id="task_easy_schema_fix")
        result = env.step(action)   # StepResult
        state  = env.state()        # PipelineState
    """

    def __init__(self, seed: int = 42):
        self._seed = seed
        self._state: Optional[PipelineState] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reset(self, task_id: str = "task_easy_schema_fix", seed: int = None) -> Observation:
        """Reset environment to initial state for the given task."""
        if seed is not None:
            self._seed = seed
        builder = TASK_BUILDERS.get(task_id)
        if builder is None:
            raise ValueError(f"Unknown task_id: {task_id!r}. "
                             f"Available: {list(TASK_BUILDERS.keys())}")
        self._state = builder(seed=self._seed)
        return self._make_observation()

    def step(self, action: Action) -> StepResult:
        """Apply an action and return (observation, reward, done, info)."""
        if self._state is None:
            raise RuntimeError("Call reset() before step().")

        state = self._state
        if state.done:
            obs = self._make_observation()
            return StepResult(
                observation=obs,
                reward=Reward(value=0.0, cumulative=state.cumulative_reward,
                              explanation="Episode already done."),
                done=True,
                info={"warning": "Episode is already finished."},
            )

        state.step_count += 1
        info: Dict[str, Any] = {}

        # Apply action
        prev_score = grade(state)
        action_result = self._apply_action(action, state)
        info["action_result"] = action_result
        new_score   = grade(state)

        # Reward computation
        reward_val, components, explanation = self._compute_reward(
            prev_score, new_score, action, state, action_result
        )
        state.cumulative_reward = round(state.cumulative_reward + reward_val, 4)
        state.applied_actions.append(action.action_type)

        # Episode termination checks
        done = False
        final_score = new_score

        if action.action_type == ActionType.SUBMIT:
            done = True
            final_score = grade(state)
            info["final_score"] = final_score
            info["bugs_fixed"]  = state.bugs_fixed
            state.pipeline_stage = "complete"
        elif state.step_count >= state.max_steps:
            done = True
            final_score = grade(state)
            info["truncated"]   = True
            info["final_score"] = final_score

        state.done = done

        reward = Reward(
            value=round(reward_val, 4),
            cumulative=state.cumulative_reward,
            components=components,
            explanation=explanation,
        )
        obs = self._make_observation()
        return StepResult(observation=obs, reward=reward, done=done, info=info)

    def state(self) -> PipelineState:
        """Return full internal state (superset of observation)."""
        if self._state is None:
            raise RuntimeError("Call reset() first.")
        return copy.deepcopy(self._state)

    def tasks(self) -> List[Dict]:
        return copy.deepcopy(TASK_INFO)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _make_observation(self) -> Observation:
        s = self._state
        sample = s.data[:5] if s.data else []
        available = self._available_actions(s)
        hint = self._get_hint(s)
        return Observation(
            task_id         = s.task_id,
            step_count      = s.step_count,
            max_steps       = s.max_steps,
            pipeline_stage  = s.pipeline_stage,
            data_sample     = sample,
            schema_info     = s.schema_info,
            error_log       = s.error_log[-6:],  # last 6 errors
            metrics         = s.metrics,
            available_actions= available,
            hint            = hint,
            done            = s.done,
        )

    def _available_actions(self, s: PipelineState) -> List[str]:
        actions = ["inspect", "validate", "submit"]
        actions += ["cast_column", "drop_nulls", "fill_nulls",
                    "drop_duplicates", "filter_outliers",
                    "rename_column", "apply_business_rule"]
        if s.task_id == "task_hard_pipeline_orchestration":
            actions.append("reorder_stages")
        return actions

    def _get_hint(self, s: PipelineState) -> str:
        unfixed = [k for k, v in s.bugs_fixed.items() if not v]
        if not unfixed:
            return "All tracked issues resolved. Consider calling submit."
        # Give a gentle hint toward the first unfixed bug
        hint_map = {
            "cast_customer_id_to_int":   "Try cast_column on 'customer_id' → 'int'",
            "cast_age_to_int":           "Try cast_column on 'age' → 'int'",
            "cast_revenue_to_float":     "Try cast_column on 'revenue' → 'float'",
            "handle_bad_age":            "Some age values are non-numeric strings — use filter_outliers or fill_nulls",
            "handle_bad_revenue":        "Some revenue='N/A' — use fill_nulls or filter_outliers",
            "drop_duplicates":           "Duplicate rows detected — use drop_duplicates",
            "fill_or_drop_nulls":        "Null values remain — use fill_nulls or drop_nulls",
            "filter_negative_qty":       "Negative quantity detected — use filter_outliers on 'quantity'",
            "filter_outlier_qty":        "Extreme quantity values detected — use filter_outliers",
            "fix_invalid_discount":      "discount > 1.0 is invalid — use apply_business_rule",
            "fix_negative_price":        "Negative unit_price — use filter_outliers on 'unit_price'",
            "fix_stage_order":           "Pipeline stages are in the wrong order — use reorder_stages",
            "cast_txn_id_to_int":        "txn_id should be int — use cast_column",
            "cast_user_id_to_int":       "user_id should be int — use cast_column",
            "cast_amount_to_float":      "amount should be float — use cast_column",
            "cast_fraud_score_to_float": "fraud_score should be float — use cast_column",
            "fill_nulls_merchant":       "Null merchants found — use fill_nulls",
            "fill_nulls_fraud_score":    "Null fraud_score found — use fill_nulls",
            "filter_negative_amounts":   "Negative amounts violate business rules",
            "fix_invalid_fraud_scores":  "fraud_score > 1.0 is invalid",
            "fix_currency_codes":        "Currency codes must be exactly 3 characters",
            "fix_country_codes":         "Country codes must be exactly 2 characters",
            "validate_final":            "Run validate to confirm all fixes, then submit",
        }
        return hint_map.get(unfixed[0], f"Fix remaining issue: {unfixed[0]}")

    # ------------------------------------------------------------------
    # Action application
    # ------------------------------------------------------------------

    def _apply_action(self, action: Action, state: PipelineState) -> str:
        at = action.action_type

        if at == ActionType.INSPECT:
            return self._action_inspect(state)
        elif at == ActionType.CAST_COLUMN:
            return self._action_cast(action, state)
        elif at == ActionType.DROP_NULLS:
            return self._action_drop_nulls(action, state)
        elif at == ActionType.FILL_NULLS:
            return self._action_fill_nulls(action, state)
        elif at == ActionType.DROP_DUPLICATES:
            return self._action_drop_duplicates(state)
        elif at == ActionType.FILTER_OUTLIERS:
            return self._action_filter_outliers(action, state)
        elif at == ActionType.RENAME_COLUMN:
            return self._action_rename_column(action, state)
        elif at == ActionType.REORDER_STAGES:
            return self._action_reorder_stages(action, state)
        elif at == ActionType.APPLY_BUSINESS_RULE:
            return self._action_apply_business_rule(action, state)
        elif at == ActionType.VALIDATE:
            return self._action_validate(state)
        elif at == ActionType.SUBMIT:
            return "Episode submitted for final grading."
        return f"Unknown action: {at}"

    # ---- Individual action implementations ----

    def _action_inspect(self, state: PipelineState) -> str:
        n_null = sum(1 for row in state.data
                     for v in row.values() if v is None or v == "")
        n_dup  = len(state.data) - len({tuple(sorted(r.items())) for r in state.data})
        return (f"Inspection: {len(state.data)} rows, "
                f"{n_null} null cells, "
                f"{n_dup} duplicate rows, "
                f"stage_order={state.stage_order}")

    def _action_cast(self, action: Action, state: PipelineState) -> str:
        col      = action.column
        to_type  = (action.value or "").lower()
        if not col or not to_type:
            return "cast_column requires 'column' and 'value' (target type)."

        converters = {
            "int":   lambda x: int(float(x)) if x not in (None, "") else None,
            "float": lambda x: float(x) if x not in (None, "") else None,
            "str":   lambda x: str(x) if x is not None else None,
            "bool":  lambda x: str(x).lower() in ("true","1","yes") if x not in (None,"") else None,
        }
        conv = converters.get(to_type)
        if conv is None:
            return f"Unsupported target type: {to_type!r}"

        converted = failed = 0
        for row in state.data:
            if col in row:
                try:
                    row[col] = conv(row[col])
                    converted += 1
                except (ValueError, TypeError):
                    row[col] = None   # coerce failures to null
                    failed += 1

        # Update schema actual_type
        for sf in state.schema_info:
            if sf.name == col:
                sf.actual_type = to_type
                break

        # Mark bugs fixed
        task  = state.task_id
        key_map = {
            ("task_easy_schema_fix",           "customer_id", "int"):   "cast_customer_id_to_int",
            ("task_easy_schema_fix",           "age",         "int"):   "cast_age_to_int",
            ("task_easy_schema_fix",           "revenue",     "float"): "cast_revenue_to_float",
            ("task_hard_pipeline_orchestration","txn_id",      "int"):   "cast_txn_id_to_int",
            ("task_hard_pipeline_orchestration","user_id",     "int"):   "cast_user_id_to_int",
            ("task_hard_pipeline_orchestration","amount",      "float"): "cast_amount_to_float",
            ("task_hard_pipeline_orchestration","fraud_score", "float"): "cast_fraud_score_to_float",
        }
        bug_key = key_map.get((task, col, to_type))
        if bug_key and bug_key in state.bugs_fixed:
            state.bugs_fixed[bug_key] = True

        self._refresh_metrics(state)
        state.error_log.append(f"cast_column: {col}→{to_type}: {converted} ok, {failed} failed→null")
        return f"Cast '{col}' to {to_type}: {converted} converted, {failed} coerced to null."

    def _action_drop_nulls(self, action: Action, state: PipelineState) -> str:
        col = action.column  # None = drop any row with any null
        before = len(state.data)
        if col:
            state.data = [r for r in state.data if r.get(col) not in (None, "")]
        else:
            cols = [sf.name for sf in state.schema_info if not sf.nullable]
            state.data = [
                r for r in state.data
                if all(r.get(c) not in (None, "") for c in cols)
            ]
        removed = before - len(state.data)
        # Mark bug fixed if relevant
        if state.task_id == "task_medium_data_quality":
            state.bugs_fixed["fill_or_drop_nulls"] = True
        self._refresh_metrics(state)
        state.error_log.append(f"drop_nulls on {col or 'required cols'}: removed {removed} rows")
        return f"Dropped {removed} null rows (col={col or 'all required'})."

    def _action_fill_nulls(self, action: Action, state: PipelineState) -> str:
        col   = action.column
        value = action.value
        if not col:
            return "fill_nulls requires 'column'."
        filled = 0
        for row in state.data:
            if row.get(col) in (None, ""):
                row[col] = value if value is not None else "UNKNOWN"
                filled += 1

        # Bug tracking
        task = state.task_id
        if task == "task_medium_data_quality":
            state.bugs_fixed["fill_or_drop_nulls"] = True
        elif task == "task_hard_pipeline_orchestration":
            if col == "merchant":
                state.bugs_fixed["fill_nulls_merchant"] = True
            elif col == "fraud_score":
                state.bugs_fixed["fill_nulls_fraud_score"] = True
        elif task == "task_easy_schema_fix" and col in ("age","revenue"):
            # Filling bad values counts as handling them
            state.bugs_fixed[f"handle_bad_{col}"] = True

        self._refresh_metrics(state)
        state.error_log.append(f"fill_nulls: {col} filled {filled} nulls with {value!r}")
        return f"Filled {filled} nulls in '{col}' with {value!r}."

    def _action_drop_duplicates(self, state: PipelineState) -> str:
        before = len(state.data)
        seen   = set()
        deduped= []
        for row in state.data:
            key = tuple(sorted((k, str(v)) for k, v in row.items()))
            if key not in seen:
                seen.add(key)
                deduped.append(row)
        state.data = deduped
        removed = before - len(state.data)
        if state.task_id in ("task_medium_data_quality","task_hard_pipeline_orchestration"):
            state.bugs_fixed["drop_duplicates"] = True
        self._refresh_metrics(state)
        state.error_log.append(f"drop_duplicates: removed {removed} exact duplicates")
        return f"Removed {removed} duplicate rows."

    def _action_filter_outliers(self, action: Action, state: PipelineState) -> str:
        col   = action.column
        params= action.parameters or {}
        if not col:
            return "filter_outliers requires 'column'."

        # Parse min/max from parameters or infer from value
        min_val = params.get("min")
        max_val = params.get("max")
        if min_val is None and max_val is None and action.value:
            parts = action.value.split(",")
            min_val = float(parts[0]) if len(parts) > 0 and parts[0].strip() else None
            max_val = float(parts[1]) if len(parts) > 1 and parts[1].strip() else None

        before = len(state.data)
        def keep(row):
            v = row.get(col)
            if v is None:
                return True
            try:
                v = float(v)
                if min_val is not None and v < min_val:
                    return False
                if max_val is not None and v > max_val:
                    return False
                return True
            except (ValueError, TypeError):
                return False  # non-numeric → remove

        state.data = [r for r in state.data if keep(r)]
        removed = before - len(state.data)

        # Bug tracking
        task = state.task_id
        if task == "task_easy_schema_fix" and col == "age":
            state.bugs_fixed["handle_bad_age"] = True
        elif task == "task_easy_schema_fix" and col == "revenue":
            state.bugs_fixed["handle_bad_revenue"] = True
        elif task == "task_medium_data_quality":
            if col == "quantity" and min_val is not None and min_val >= 0:
                state.bugs_fixed["filter_negative_qty"] = True
            if col == "quantity" and max_val is not None and max_val <= 1000:
                state.bugs_fixed["filter_outlier_qty"] = True
            if col == "unit_price" and min_val is not None and min_val >= 0:
                state.bugs_fixed["fix_negative_price"] = True
        elif task == "task_hard_pipeline_orchestration":
            if col == "amount" and min_val is not None and min_val >= 0:
                state.bugs_fixed["filter_negative_amounts"] = True

        self._refresh_metrics(state)
        state.error_log.append(f"filter_outliers: {col} [{min_val},{max_val}] removed {removed}")
        return f"Filtered outliers in '{col}': removed {removed} rows."

    def _action_rename_column(self, action: Action, state: PipelineState) -> str:
        col     = action.column
        new_name= action.value
        if not col or not new_name:
            return "rename_column requires 'column' (old name) and 'value' (new name)."
        for row in state.data:
            if col in row:
                row[new_name] = row.pop(col)
        for sf in state.schema_info:
            if sf.name == col:
                sf.name = new_name
                break
        self._refresh_metrics(state)
        return f"Renamed column '{col}' → '{new_name}'."

    def _action_reorder_stages(self, action: Action, state: PipelineState) -> str:
        """Agent provides new stage order via parameters.stages or value."""
        if state.task_id != "task_hard_pipeline_orchestration":
            return "reorder_stages only applies to the hard task."
        params = action.parameters or {}
        stages = params.get("stages")
        if stages is None and action.value:
            stages = [s.strip() for s in action.value.split(",")]
        if stages is None:
            stages = HARD_STAGE_ORDER_CORRECT  # default to correct

        state.stage_order = list(stages)
        if state.stage_order == HARD_STAGE_ORDER_CORRECT:
            state.bugs_fixed["fix_stage_order"] = True
            state.error_log.append("reorder_stages: stage order corrected ✓")
            return "Stage order corrected to: " + " → ".join(stages)
        else:
            state.error_log.append(f"reorder_stages: still wrong: {stages}")
            return f"Stage order set to {stages} — this is NOT the correct order."

    def _action_apply_business_rule(self, action: Action, state: PipelineState) -> str:
        """Apply a named business rule to filter/fix rows."""
        rule_name = action.value or (action.parameters or {}).get("rule", "")
        col       = action.column
        task      = state.task_id
        before    = len(state.data)

        if rule_name == "discount_lte_1" or (col == "discount"):
            state.data = [r for r in state.data
                          if r.get("discount") is None or
                          (isinstance(r.get("discount"),(int,float)) and r["discount"] <= 1.0)]
            if task == "task_medium_data_quality":
                state.bugs_fixed["fix_invalid_discount"] = True

        elif rule_name == "fraud_score_lte_1" or col == "fraud_score":
            state.data = [r for r in state.data
                          if r.get("fraud_score") is None or
                          (isinstance(r.get("fraud_score"),(int,float)) and r["fraud_score"] <= 1.0)]
            if task == "task_hard_pipeline_orchestration":
                state.bugs_fixed["fix_invalid_fraud_scores"] = True

        elif rule_name == "currency_3char" or col == "currency":
            def fix_currency(row):
                c = row.get("currency","")
                if isinstance(c, str) and len(c) != 3:
                    row["currency"] = None  # nullify invalid
                return row
            state.data = [fix_currency(r) for r in state.data]
            if task == "task_hard_pipeline_orchestration":
                state.bugs_fixed["fix_currency_codes"] = True

        elif rule_name == "country_2char" or col == "country_code":
            def fix_country(row):
                c = row.get("country_code","")
                if isinstance(c, str) and len(c) != 2:
                    row["country_code"] = None
                return row
            state.data = [fix_country(r) for r in state.data]
            if task == "task_hard_pipeline_orchestration":
                state.bugs_fixed["fix_country_codes"] = True

        else:
            return f"Unknown business rule: {rule_name!r}. Known: discount_lte_1, fraud_score_lte_1, currency_3char, country_2char"

        removed = before - len(state.data)
        self._refresh_metrics(state)
        state.error_log.append(f"apply_business_rule '{rule_name}': {removed} rows affected")
        return f"Applied rule '{rule_name}': {removed} rows affected."

    def _action_validate(self, state: PipelineState) -> str:
        self._refresh_metrics(state)
        m = state.metrics
        issues = []
        for sf in state.schema_info:
            if sf.actual_type != sf.expected_type:
                issues.append(f"  • '{sf.name}': expected {sf.expected_type}, got {sf.actual_type}")
        if state.task_id == "task_hard_pipeline_orchestration":
            if state.stage_order != HARD_STAGE_ORDER_CORRECT:
                issues.append(f"  • Stage order WRONG: {state.stage_order}")
            if state.bugs_fixed.get("fix_invalid_fraud_scores") is False:
                issues.append("  • fraud_score > 1.0 still present")
        if state.task_id == "task_hard_pipeline_orchestration":
            state.bugs_fixed["validate_final"] = len(issues) == 0

        summary = (f"Validation: completeness={m.completeness:.3f} "
                   f"uniqueness={m.uniqueness:.3f} "
                   f"validity={m.validity:.3f} "
                   f"accuracy={m.accuracy:.3f}")
        if issues:
            state.error_log.append("validate: issues found")
            return summary + "\nIssues:\n" + "\n".join(issues)
        state.error_log.append("validate: PASSED ✓")
        return summary + "\nAll schema checks PASSED ✓"

    # ------------------------------------------------------------------
    # Reward computation
    # ------------------------------------------------------------------

    def _compute_reward(
        self,
        prev_score: float,
        new_score:  float,
        action:     Action,
        state:      PipelineState,
        action_result: str,
    ) -> Tuple[float, Dict[str, float], str]:
        """
        Multi-component reward:
          progress   = new_score - prev_score  (can be negative)
          efficiency = -0.01 per step (small step cost encourages concision)
          repeat_pen = -0.05 if same action used 3+ times consecutively
          submit_bon =  0.1 * new_score on submit (quality bonus)
        """
        progress   = new_score - prev_score
        step_cost  = -0.02

        # Penalize repeating the same action many times
        recent = state.applied_actions[-3:] if state.applied_actions else []
        repeat_pen = -0.05 if len(recent) == 3 and len(set(recent)) == 1 else 0.0

        submit_bon = 0.0
        if action.action_type == ActionType.SUBMIT:
            submit_bon = 0.1 * new_score

        total = progress + step_cost + repeat_pen + submit_bon

        components = {
            "progress":   round(progress,   4),
            "step_cost":  step_cost,
            "repeat_pen": repeat_pen,
            "submit_bon": round(submit_bon, 4),
        }
        explanation = (
            f"progress={progress:+.4f}, step_cost={step_cost}, "
            f"repeat_pen={repeat_pen}, submit_bonus={submit_bon:.4f} → total={total:.4f}"
        )
        return round(total, 4), components, explanation

    # ------------------------------------------------------------------
    # Metrics refresh
    # ------------------------------------------------------------------

    def _refresh_metrics(self, state: PipelineState):
        task = state.task_id
        if task == "task_easy_schema_fix":
            rules = None
        elif task == "task_medium_data_quality":
            rules = MEDIUM_RULES
        else:
            rules = HARD_RULES
        state.metrics = _compute_metrics(state.data, state.schema_info, rules)
        # SLA penalty for hard task: more bugs left → higher latency
        if task == "task_hard_pipeline_orchestration":
            unfixed = sum(1 for v in state.bugs_fixed.values() if not v)
            state.metrics.sla_latency_ms = round(30 + unfixed * 25.0, 2)
