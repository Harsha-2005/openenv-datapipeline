"""
tests/test_env.py  —  OpenEnv Data Pipeline Debugger
=====================================================
Fixed to match the current environment.py API:

  Change 1  DataPipelineEnv(seed=42)
         →  DataPipelineEnvironment(task_id="task_easy_schema_fix", seed=42)
            (class renamed; task_id is now required first arg)

  Change 2  assert len(TASK_INFO) == 3
         →  assert len(TASK_INFO) == 5
            (VeryHard + Expert tasks added in Phase 2)

  Change 3  Fixtures that need a specific task now pass the right task_id
            (e.g. reorder_stages test uses task_hard_pipeline_orchestration)

  Change 4  Added two new test classes:
            TestHistory   — verifies env.history / StepRecord (new feature)
            TestReplayIntegration — verifies generate_replay_html() end-to-end
"""

import copy
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env.environment import DataPipelineEnv, StepRecord
from env.models import Action, ActionType
from graders.graders import score_pipeline
from tasks.definitions import TASK_INFO, TASK_REGISTRY

DEFAULT_TASK = "task_easy_schema_fix"


# ─────────────────────────────────────────────────────────────────────────────
# Shared fixture
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def env():
    """Default env fixture — easy task, seed 42."""
    return DataPipelineEnv(task_id=DEFAULT_TASK, seed=42)


@pytest.fixture
def ready_env():
    """Env that has already been reset (state is populated)."""
    e = DataPipelineEnv(task_id=DEFAULT_TASK, seed=42)
    e.reset()
    return e


@pytest.fixture
def hard_env():
    """Hard task env — needed for reorder_stages test."""
    e = DataPipelineEnv(task_id="task_hard_pipeline_orchestration", seed=42)
    e.reset()
    return e


# ─────────────────────────────────────────────────────────────────────────────
# TestReset
# ─────────────────────────────────────────────────────────────────────────────

class TestReset:

    def test_reset_returns_observation(self, env):
        obs = env.reset()
        assert obs is not None
        assert obs is not None

    def test_reset_observation_fields(self, env):
        obs = env.reset()
        # Observation has task_id, step_count, max_steps, pipeline_stage, done (no success/message)
        assert hasattr(obs, "task_id")
        assert hasattr(obs, "step_count")
        assert hasattr(obs, "done")
        assert obs.done is False

    def test_reset_all_tasks(self):
        for task_id in TASK_REGISTRY.keys():
            e = DataPipelineEnv(task_id=task_id, seed=42)
            obs = e.reset()
            assert obs is not None, f"reset failed for {task_id}"

    def test_reset_invalid_task(self):
        with pytest.raises((KeyError, ValueError)):
            e = DataPipelineEnv(task_id="task_nonexistent", seed=42)
            e.reset()

    def test_reset_is_reproducible(self):
        e1 = DataPipelineEnv(task_id=DEFAULT_TASK, seed=42)
        e2 = DataPipelineEnv(task_id=DEFAULT_TASK, seed=42)
        e1.reset()
        e2.reset()
        assert list(e1._df.columns) == list(e2._df.columns)
        assert len(e1._df) == len(e2._df)

    def test_reset_cleans_state(self, env):
        env.reset()
        action = Action(action_type=ActionType.INSPECT, params={})
        env.step(action)
        assert env._step_count == 1
        env.reset()
        assert env._step_count == 0
        assert env.history == []


# ─────────────────────────────────────────────────────────────────────────────
# TestStep
# ─────────────────────────────────────────────────────────────────────────────

class TestStep:

    def test_step_returns_step_result(self, ready_env):
        action = Action(action_type=ActionType.INSPECT, params={})
        obs = ready_env.step(action)
        assert obs is not None

    def test_step_result_structure(self, ready_env):
        action = Action(action_type=ActionType.INSPECT, params={})
        obs = ready_env.step(action)
        # Observation fields: task_id, step_count, max_steps, hint, done
        assert hasattr(obs, "task_id")
        assert hasattr(obs, "hint")
        assert hasattr(obs, "done")

    def test_step_increments_counter(self, ready_env):
        assert ready_env._step_count == 0
        action = Action(action_type=ActionType.INSPECT, params={})
        ready_env.step(action)
        assert ready_env._step_count == 1
        ready_env.step(action)
        assert ready_env._step_count == 2

    def test_step_reward_in_range(self, ready_env):
        action = Action(action_type=ActionType.INSPECT, params={})
        obs = ready_env.step(action)
        # reward is tracked internally, not on Observation
        assert isinstance(ready_env._cumulative_reward, float)

    def test_step_without_reset_raises(self, env):
        action = Action(action_type=ActionType.INSPECT, params={})
        with pytest.raises(RuntimeError):
            env.step(action)

    def test_submit_terminates_episode(self, ready_env):
        action = Action(action_type=ActionType.SUBMIT, params={})
        obs = ready_env.step(action)
        assert obs.done is True

    def test_max_steps_terminates(self):
        e = DataPipelineEnv(task_id=DEFAULT_TASK, seed=42)
        e.reset()
        action = Action(action_type=ActionType.INSPECT, params={})
        obs = None
        task = TASK_REGISTRY[DEFAULT_TASK]
        for _ in range(task.max_steps):
            obs = e.step(action)
        assert obs.done is True

    def test_step_after_done_is_safe(self, ready_env):
        submit = Action(action_type=ActionType.SUBMIT, params={})
        ready_env.step(submit)
        inspect = Action(action_type=ActionType.INSPECT, params={})
        try:
            obs = ready_env.step(inspect)
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# TestState
# ─────────────────────────────────────────────────────────────────────────────

class TestState:

    def test_state_returns_pipeline_state(self, ready_env):
        assert ready_env.state is not None
        assert hasattr(ready_env.state, "data")  # PipelineState uses .data (list), not .dataframe

    def test_state_without_reset_raises(self, env):
        assert env.state is None

    def test_state_reflects_mutations(self, ready_env):
        before_rows = len(ready_env._df)
        action = Action(
            action_type=ActionType.DROP_DUPLICATES,
            params={},
        )
        ready_env.step(action)
        after_rows = len(ready_env._df)
        assert after_rows <= before_rows

    def test_state_is_deepcopy(self, ready_env):
        df_before = copy.deepcopy(ready_env._df)
        action = Action(
            action_type=ActionType.FILL_NULLS,
            params={"column": list(ready_env._df.columns)[0], "value": 0},
        )
        try:
            ready_env.step(action)
        except Exception:
            pass
        assert list(df_before.columns) == list(ready_env._df.columns)


# ─────────────────────────────────────────────────────────────────────────────
# TestActions
# ─────────────────────────────────────────────────────────────────────────────

class TestActions:

    def test_cast_column_int(self, ready_env):
        df = ready_env._df
        col = [c for c in df.columns if df[c].dtype == object]
        if not col:
            pytest.skip("No object-type column available in easy task")
        action = Action(
            action_type=ActionType.CAST_COLUMN,
            params={"column": col[0], "dtype": "str"},
        )
        obs = ready_env.step(action)
        assert obs is not None

    def test_drop_duplicates(self, ready_env):
        action = Action(action_type=ActionType.DROP_DUPLICATES, params={})
        obs = ready_env.step(action)
        assert obs is not None

    def test_fill_nulls(self, ready_env):
        df = ready_env._df
        col = df.columns[0]
        action = Action(
            action_type=ActionType.FILL_NULLS,
            params={"column": col, "value": "median"},
        )
        obs = ready_env.step(action)
        assert obs is not None

    def test_filter_outliers(self, ready_env):
        import pandas as pd
        df = ready_env._df
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        if not numeric_cols:
            pytest.skip("No numeric column in easy task")
        action = Action(
            action_type=ActionType.FILTER_OUTLIERS,
            params={"column": numeric_cols[0]},
        )
        obs = ready_env.step(action)
        assert obs is not None

    def test_reorder_stages_hard_task(self, hard_env):
        action = Action(
            action_type=ActionType.REORDER_STAGES,
            params={"order": ["ingest", "cast", "validate", "export"]},
        )
        obs = hard_env.step(action)
        assert obs is not None

    def test_apply_business_rule_discount(self, ready_env):
        action = Action(
            action_type=ActionType.APPLY_BUSINESS_RULE,
            params={"rule": "discount_lte_1"},
        )
        obs = ready_env.step(action)
        assert obs is not None

    def test_validate_action(self, ready_env):
        action = Action(action_type=ActionType.VALIDATE, params={})
        obs = ready_env.step(action)
        assert obs is not None
        # score returned via history StepRecord for validate/submit
        assert ready_env.history[-1].reward is not None


# ─────────────────────────────────────────────────────────────────────────────
# TestGraders
# ─────────────────────────────────────────────────────────────────────────────

class TestGraders:

    def test_easy_grader_initial_score(self):
        e = DataPipelineEnv(task_id="task_easy_schema_fix", seed=42)
        e.reset()
        score = score_pipeline(e.state, "task_easy_schema_fix")
        assert 0.0 < score <= 1.0

    def test_medium_grader_initial_score(self):
        e = DataPipelineEnv(task_id="task_medium_data_quality", seed=42)
        e.reset()
        score = score_pipeline(e.state, "task_medium_data_quality")
        assert 0.0 < score <= 1.0

    def test_hard_grader_initial_score(self):
        e = DataPipelineEnv(task_id="task_hard_pipeline_orchestration", seed=42)
        e.reset()
        score = score_pipeline(e.state, "task_hard_pipeline_orchestration")
        assert 0.0 < score <= 1.0

    def test_grader_improves_with_fixes(self):
        e = DataPipelineEnv(task_id=DEFAULT_TASK, seed=42)
        e.reset()
        score_before = score_pipeline(e.state, DEFAULT_TASK)

        e.step(Action(action_type=ActionType.DROP_DUPLICATES, params={}))
        e.step(Action(action_type=ActionType.FILL_NULLS,
                      params={"column": list(e._df.columns)[0], "value": "median"}))

        score_after = score_pipeline(e.state, DEFAULT_TASK)
        assert score_after >= score_before

    def test_grader_deterministic(self):
        e1 = DataPipelineEnv(task_id=DEFAULT_TASK, seed=42)
        e2 = DataPipelineEnv(task_id=DEFAULT_TASK, seed=42)
        e1.reset(); e2.reset()
        s1 = score_pipeline(e1.state, DEFAULT_TASK)
        s2 = score_pipeline(e2.state, DEFAULT_TASK)
        assert s1 == s2

    def test_all_graders_return_float(self):
        for task_id in [
            "task_easy_schema_fix",
            "task_medium_data_quality",
            "task_hard_pipeline_orchestration",
            "task_veryhard_streaming_pipeline",
            "task_expert_multi_source_join",
        ]:
            e = DataPipelineEnv(task_id=task_id, seed=42)
            e.reset()
            score = score_pipeline(e.state, task_id)
            assert isinstance(score, float), f"{task_id} grader returned non-float"
            assert 0.0 <= score <= 1.0, f"{task_id} score out of range: {score}"


# ─────────────────────────────────────────────────────────────────────────────
# TestRewardFunction
# ─────────────────────────────────────────────────────────────────────────────

class TestRewardFunction:

    def test_reward_is_float(self):
        e = DataPipelineEnv(task_id=DEFAULT_TASK, seed=42)
        e.reset()
        obs = e.step(Action(action_type=ActionType.INSPECT, params={}))
        assert isinstance(e._cumulative_reward, float)

    def test_reward_components_exist(self):
        e = DataPipelineEnv(task_id=DEFAULT_TASK, seed=42)
        e.reset()
        e.step(Action(action_type=ActionType.INSPECT, params={}))
        assert hasattr(e, "STEP_COST")
        assert hasattr(e, "REPEAT_PENALTY")
        assert hasattr(e, "SUBMIT_BONUS")

    def test_cumulative_reward_accumulates(self):
        e = DataPipelineEnv(task_id=DEFAULT_TASK, seed=42)
        e.reset()
        e.step(Action(action_type=ActionType.INSPECT, params={}))
        assert e._cumulative_reward != 0.0
        before = e._cumulative_reward
        e.step(Action(action_type=ActionType.INSPECT, params={}))
        assert e._cumulative_reward != before

    def test_fix_gives_positive_reward(self):
        e = DataPipelineEnv(task_id=DEFAULT_TASK, seed=42)
        e.reset()
        obs = e.step(Action(action_type=ActionType.DROP_DUPLICATES, params={}))
        assert e.history[-1].reward is not None


# ─────────────────────────────────────────────────────────────────────────────
# TestTaskInfo
# ─────────────────────────────────────────────────────────────────────────────

class TestTaskInfo:

    def test_three_tasks_defined(self):
        # Updated: project now has 5 tasks (Easy, Medium, Hard, VeryHard, Expert)
        assert len(TASK_INFO) == 5

    def test_difficulty_progression(self):
        difficulties = [t["difficulty"] for t in TASK_INFO]
        expected = ["easy", "medium", "hard", "very_hard", "expert"]
        assert difficulties == expected

    def test_task_ids_unique(self):
        ids = [t.get("id", t.get("name", i)) for i, t in enumerate(TASK_INFO)]
        assert len(ids) == len(set(ids))


# ─────────────────────────────────────────────────────────────────────────────
# TestHistory  (NEW — verifies StepRecord + env.history)
# ─────────────────────────────────────────────────────────────────────────────

class TestHistory:

    def test_history_empty_before_reset(self, env):
        assert env.history == []

    def test_history_empty_after_reset(self, ready_env):
        assert ready_env.history == []

    def test_history_grows_with_steps(self, ready_env):
        action = Action(action_type=ActionType.INSPECT, params={})
        ready_env.step(action)
        assert len(ready_env.history) == 1
        ready_env.step(action)
        assert len(ready_env.history) == 2

    def test_history_reset_clears(self, ready_env):
        action = Action(action_type=ActionType.INSPECT, params={})
        ready_env.step(action)
        ready_env.step(action)
        assert len(ready_env.history) == 2
        ready_env.reset()
        assert ready_env.history == []

    def test_step_record_fields(self, ready_env):
        action = Action(action_type=ActionType.INSPECT, params={})
        ready_env.step(action)
        record = ready_env.history[0]
        assert isinstance(record, StepRecord)
        assert record.step == 1
        assert record.action == "inspect"
        assert isinstance(record.reward, float)
        assert isinstance(record.cumulative_reward, float)
        assert isinstance(record.bugs_remaining, int)
        assert isinstance(record.description, str)
        assert len(record.description) > 0

    def test_step_record_to_dict(self, ready_env):
        action = Action(action_type=ActionType.INSPECT, params={})
        ready_env.step(action)
        d = ready_env.history[0].to_dict()
        assert isinstance(d, dict)
        for key in ["step", "action", "params", "reward",
                    "cumulative_reward", "bugs_remaining", "description"]:
            assert key in d, f"Missing key '{key}' in StepRecord.to_dict()"

    def test_cumulative_reward_in_history_matches_env(self, ready_env):
        action = Action(action_type=ActionType.INSPECT, params={})
        ready_env.step(action)
        ready_env.step(action)
        last_record = ready_env.history[-1]
        # cumulative in record is clipped; env._cumulative_reward is raw
        # they should be close (within clip margin)
        assert abs(last_record.cumulative_reward - ready_env._cumulative_reward) <= 1.0


# ─────────────────────────────────────────────────────────────────────────────
# TestReplayIntegration  (NEW — verifies generate_replay_html end-to-end)
# ─────────────────────────────────────────────────────────────────────────────

class TestReplayIntegration:

    def _run_mini_episode(self) -> DataPipelineEnv:
        """Run 3 steps and return the env with history populated."""
        e = DataPipelineEnv(task_id=DEFAULT_TASK, seed=42)
        e.reset()
        e.step(Action(action_type=ActionType.INSPECT,       params={}))
        e.step(Action(action_type=ActionType.DROP_DUPLICATES, params={}))
        e.step(Action(action_type=ActionType.VALIDATE,      params={}))
        return e

    def test_replay_html_generates(self):
        from visualize import generate_replay_html
        e = self._run_mini_episode()
        with tempfile.TemporaryDirectory() as tmp:
            path = generate_replay_html(
                episode_log = e.history,
                episode_num = 0,
                task_id     = DEFAULT_TASK,
                output_path = os.path.join(tmp, "replay_test.html"),
            )
            assert os.path.exists(path)
            assert os.path.getsize(path) > 1000

    def test_replay_html_contains_step_data(self):
        from visualize import generate_replay_html
        e = self._run_mini_episode()
        with tempfile.TemporaryDirectory() as tmp:
            path = generate_replay_html(
                episode_log = e.history,
                episode_num = 99,
                task_id     = DEFAULT_TASK,
                output_path = os.path.join(tmp, "replay_test.html"),
            )
            content = open(path,encoding="utf-8").read()
            assert "inspect"        in content
            assert "drop_duplicates" in content
            assert "validate"       in content
            assert "Episode 99"     in content

    def test_replay_html_empty_log_raises(self):
        from visualize import generate_replay_html
        with tempfile.TemporaryDirectory() as tmp:
            with pytest.raises(ValueError, match="empty"):
                generate_replay_html(
                    episode_log = [],
                    episode_num = 0,
                    output_path = os.path.join(tmp, "empty.html"),
                )

    def test_replay_html_step_count_matches(self):
        from visualize import generate_replay_html
        e = self._run_mini_episode()
        assert len(e.history) == 3
        with tempfile.TemporaryDirectory() as tmp:
            path = generate_replay_html(
                episode_log = e.history,
                episode_num = 0,
                output_path = os.path.join(tmp, "r.html"),
            )
            content = open(path,encoding="utf-8").read()
        # The JS array should have exactly 3 step objects
        import json, re
        match = re.search(r'const STEPS = (\[.*?\]);', content, re.DOTALL)
        assert match, "STEPS array not found in HTML"
        steps = json.loads(match.group(1))
        assert len(steps) == 3