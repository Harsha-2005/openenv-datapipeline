#!/usr/bin/env python3
"""
benchmarks/agents.py — Baseline agents for benchmark comparison.

Provides three baseline agents to compare against the LLM-powered agent:
  1. RandomAgent     — picks random valid actions
  2. GreedyAgent     — follows a greedy heuristic (always picks highest-priority fix)
  3. FixedAgent      — follows a hardcoded optimal sequence per task
"""

from __future__ import annotations
import random
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """Abstract base class for benchmark agents."""

    name: str = "base"

    @abstractmethod
    def choose_action(self, obs: Dict[str, Any], step: int) -> Dict[str, Any]:
        """Given an observation, return an action dict."""
        ...

    def reset(self):
        """Reset agent state for a new episode."""
        pass


class RandomAgent(BaseAgent):
    """Picks random valid actions. Serves as a lower-bound baseline."""

    name = "Random"

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self._inspected = False

    def reset(self):
        self._inspected = False

    def choose_action(self, obs: Dict[str, Any], step: int) -> Dict[str, Any]:
        max_steps = obs.get("max_steps", 10)

        # Always submit on last step
        if step >= max_steps - 1:
            return {"action_type": "submit"}

        # Always inspect first
        if not self._inspected:
            self._inspected = True
            return {"action_type": "inspect"}

        schema_info = obs.get("schema_info", [])
        columns = []
        for sf in schema_info:
            name = sf.get("name", "") if isinstance(sf, dict) else getattr(sf, "name", "")
            if name:
                columns.append(name)

        action_pool = [
            {"action_type": "inspect"},
            {"action_type": "drop_duplicates"},
            {"action_type": "validate"},
        ]

        # Add column-specific actions
        if columns:
            col = self.rng.choice(columns)
            action_pool.extend([
                {"action_type": "cast_column", "column": col, "value": self.rng.choice(["int", "float", "str"])},
                {"action_type": "drop_nulls", "column": col},
                {"action_type": "fill_nulls", "column": col, "value": "0"},
                {"action_type": "filter_outliers", "column": col, "value": "0,9999"},
            ])

        action_pool.extend([
            {"action_type": "apply_business_rule", "value": self.rng.choice(["discount_lte_1", "fraud_score_lte_1", "currency_3char", "country_2char"])},
            {"action_type": "reorder_stages", "parameters": {"stages": ["ingest", "validate", "transform", "enrich", "load"]}},
        ])

        return self.rng.choice(action_pool)


class GreedyAgent(BaseAgent):
    """
    Follows a greedy heuristic: picks the highest-priority fix based on error log.
    Better than random but not optimal — doesn't plan ahead.
    """

    name = "Greedy"

    def __init__(self):
        self._step_actions: List[str] = []
        self._inspected = False

    def reset(self):
        self._step_actions = []
        self._inspected = False

    def choose_action(self, obs: Dict[str, Any], step: int) -> Dict[str, Any]:
        max_steps = obs.get("max_steps", 10)
        error_log = obs.get("error_log", [])
        errors_str = " ".join(error_log).lower()
        schema_info = obs.get("schema_info", [])

        # Always submit on last step
        if step >= max_steps - 1:
            return {"action_type": "submit"}

        # Always inspect first
        if not self._inspected:
            self._inspected = True
            return {"action_type": "inspect"}

        # Priority 1: Fix schema mismatches
        for sf in schema_info:
            name = sf.get("name", "") if isinstance(sf, dict) else getattr(sf, "name", "")
            exp = sf.get("expected_type", "") if isinstance(sf, dict) else getattr(sf, "expected_type", "")
            actual = sf.get("actual_type", "") if isinstance(sf, dict) else getattr(sf, "actual_type", "")
            if exp and actual and exp != actual and f"cast:{name}" not in self._step_actions:
                self._step_actions.append(f"cast:{name}")
                return {"action_type": "cast_column", "column": name, "value": exp}

        # Priority 2: Drop duplicates
        if "duplicate" in errors_str and "drop_duplicates" not in self._step_actions:
            self._step_actions.append("drop_duplicates")
            return {"action_type": "drop_duplicates"}

        # Priority 3: Business rules
        for rule_key, rule_val in [("discount", "discount_lte_1"), ("fraud", "fraud_score_lte_1"),
                                    ("currency", "currency_3char"), ("country", "country_2char")]:
            if rule_key in errors_str and f"rule:{rule_val}" not in self._step_actions:
                self._step_actions.append(f"rule:{rule_val}")
                return {"action_type": "apply_business_rule", "value": rule_val}

        # Priority 4: Validate then submit
        if "validate" not in self._step_actions[-3:]:
            self._step_actions.append("validate")
            return {"action_type": "validate"}

        return {"action_type": "submit"}


class FixedStrategyAgent(BaseAgent):
    """
    Follows a hardcoded optimal sequence per task.
    Represents the 'expert human' baseline — knows exactly what to do.
    """

    name = "Fixed-Strategy"

    TASK_SEQUENCES = {
        "task_easy_schema_fix": [
            {"action_type": "inspect"},
            {"action_type": "cast_column", "column": "age", "value": "int"},
            {"action_type": "cast_column", "column": "revenue", "value": "float"},
            {"action_type": "cast_column", "column": "is_active", "value": "bool"},
            {"action_type": "drop_duplicates"},
            {"action_type": "fill_nulls", "column": "age", "value": "0"},
            {"action_type": "fill_nulls", "column": "revenue", "value": "0.0"},
            {"action_type": "fill_nulls", "column": "email", "value": "unknown@example.com"},
            {"action_type": "validate"},
            {"action_type": "submit"},
        ],
        "task_medium_data_quality": [
            {"action_type": "inspect"},
            {"action_type": "cast_column", "column": "quantity", "value": "int"},
            {"action_type": "cast_column", "column": "unit_price", "value": "float"},
            {"action_type": "drop_duplicates"},
            {"action_type": "fill_nulls", "column": "quantity", "value": "1"},
            {"action_type": "fill_nulls", "column": "unit_price", "value": "0.0"},
            {"action_type": "fill_nulls", "column": "region", "value": "UNKNOWN"},
            {"action_type": "filter_outliers", "column": "quantity", "value": "0,9999"},
            {"action_type": "filter_outliers", "column": "unit_price", "value": "0,99999"},
            {"action_type": "apply_business_rule", "value": "discount_lte_1"},
            {"action_type": "validate"},
            {"action_type": "submit"},
        ],
        "task_hard_pipeline_orchestration": [
            {"action_type": "inspect"},
            {"action_type": "reorder_stages", "parameters": {"stages": ["ingest", "validate", "transform", "enrich", "load"]}},
            {"action_type": "cast_column", "column": "fraud_score", "value": "float"},
            {"action_type": "drop_duplicates"},
            {"action_type": "fill_nulls", "column": "merchant", "value": "UNKNOWN"},
            {"action_type": "fill_nulls", "column": "fraud_score", "value": "0.0"},
            {"action_type": "fill_nulls", "column": "category", "value": "UNKNOWN"},
            {"action_type": "fill_nulls", "column": "country_code", "value": "US"},
            {"action_type": "fill_nulls", "column": "currency", "value": "USD"},
            {"action_type": "filter_outliers", "column": "amount", "value": "0,999999"},
            {"action_type": "apply_business_rule", "value": "discount_lte_1"},
            {"action_type": "apply_business_rule", "value": "fraud_score_lte_1"},
            {"action_type": "apply_business_rule", "value": "currency_3char"},
            {"action_type": "apply_business_rule", "value": "country_2char"},
            {"action_type": "validate"},
            {"action_type": "submit"},
        ],
    }

    def __init__(self):
        self._step_idx = 0
        self._task_id = ""

    def reset(self):
        self._step_idx = 0

    def set_task(self, task_id: str):
        self._task_id = task_id
        self._step_idx = 0

    def choose_action(self, obs: Dict[str, Any], step: int) -> Dict[str, Any]:
        task_id = obs.get("task_id", self._task_id)
        sequence = self.TASK_SEQUENCES.get(task_id, [
            {"action_type": "inspect"},
            {"action_type": "validate"},
            {"action_type": "submit"},
        ])

        if self._step_idx < len(sequence):
            action = sequence[self._step_idx]
            self._step_idx += 1
            return action

        return {"action_type": "submit"}
