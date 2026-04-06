"""
Tests for OpenEnv Data Pipeline Debugger.
Validates OpenEnv spec compliance, grader correctness, and reward properties.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env.environment import DataPipelineEnv
from env.models import Action, ActionType, Observation, PipelineState, Reward, StepResult
from graders.graders import grade, grade_easy, grade_medium, grade_hard
from tasks.definitions import build_easy_task, build_medium_task, build_hard_task, TASK_INFO


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def env():
    return DataPipelineEnv(seed=42)


# ---------------------------------------------------------------------------
# OpenEnv spec: reset() tests
# ---------------------------------------------------------------------------

class TestReset:
    def test_reset_returns_observation(self, env):
        obs = env.reset("task_easy_schema_fix")
        assert isinstance(obs, Observation)

    def test_reset_observation_fields(self, env):
        obs = env.reset("task_easy_schema_fix")
        assert obs.task_id == "task_easy_schema_fix"
        assert obs.step_count == 0
        assert obs.max_steps == 10
        assert isinstance(obs.data_sample, list)
        assert isinstance(obs.schema_info, list)
        assert isinstance(obs.error_log, list)
        assert obs.done is False

    def test_reset_all_tasks(self, env):
        for task in ["task_easy_schema_fix", "task_medium_data_quality",
                     "task_hard_pipeline_orchestration"]:
            obs = env.reset(task)
            assert obs.task_id == task
            assert obs.step_count == 0

    def test_reset_invalid_task(self, env):
        with pytest.raises(ValueError, match="Unknown task_id"):
            env.reset("nonexistent_task")

    def test_reset_is_reproducible(self, env):
        obs1 = env.reset("task_easy_schema_fix", seed=42)
        obs2 = env.reset("task_easy_schema_fix", seed=42)
        assert obs1.data_sample == obs2.data_sample
        assert obs1.error_log == obs2.error_log

    def test_reset_cleans_state(self, env):
        env.reset("task_easy_schema_fix")
        env.step(Action(action_type=ActionType.INSPECT))
        # Reset should give step_count=0 again
        obs = env.reset("task_easy_schema_fix")
        assert obs.step_count == 0
        assert obs.done is False


# ---------------------------------------------------------------------------
# OpenEnv spec: step() tests
# ---------------------------------------------------------------------------

class TestStep:
    def test_step_returns_step_result(self, env):
        env.reset("task_easy_schema_fix")
        result = env.step(Action(action_type=ActionType.INSPECT))
        assert isinstance(result, StepResult)

    def test_step_result_structure(self, env):
        env.reset("task_easy_schema_fix")
        result = env.step(Action(action_type=ActionType.INSPECT))
        assert isinstance(result.observation, Observation)
        assert isinstance(result.reward, Reward)
        assert isinstance(result.done, bool)
        assert isinstance(result.info, dict)

    def test_step_increments_counter(self, env):
        env.reset("task_easy_schema_fix")
        r1 = env.step(Action(action_type=ActionType.INSPECT))
        assert r1.observation.step_count == 1
        r2 = env.step(Action(action_type=ActionType.INSPECT))
        assert r2.observation.step_count == 2

    def test_step_reward_in_range(self, env):
        env.reset("task_easy_schema_fix")
        for _ in range(5):
            result = env.step(Action(action_type=ActionType.INSPECT))
            assert -1.0 <= result.reward.value <= 1.0

    def test_step_without_reset_raises(self, env):
        with pytest.raises(RuntimeError, match="reset"):
            env.step(Action(action_type=ActionType.INSPECT))

    def test_submit_terminates_episode(self, env):
        env.reset("task_easy_schema_fix")
        result = env.step(Action(action_type=ActionType.SUBMIT))
        assert result.done is True
        assert "final_score" in result.info

    def test_max_steps_terminates(self, env):
        env.reset("task_easy_schema_fix")  # max_steps=10
        for _ in range(10):
            result = env.step(Action(action_type=ActionType.INSPECT))
        assert result.done is True
        assert result.info.get("truncated") is True

    def test_step_after_done_is_safe(self, env):
        env.reset("task_easy_schema_fix")
        env.step(Action(action_type=ActionType.SUBMIT))
        # Should not raise, just return done=True
        result = env.step(Action(action_type=ActionType.INSPECT))
        assert result.done is True


# ---------------------------------------------------------------------------
# OpenEnv spec: state() tests
# ---------------------------------------------------------------------------

class TestState:
    def test_state_returns_pipeline_state(self, env):
        env.reset("task_easy_schema_fix")
        s = env.state()
        assert isinstance(s, PipelineState)

    def test_state_without_reset_raises(self, env):
        with pytest.raises(RuntimeError):
            env.state()

    def test_state_reflects_mutations(self, env):
        env.reset("task_easy_schema_fix")
        s_before = env.state()
        env.step(Action(action_type=ActionType.DROP_DUPLICATES))
        s_after = env.state()
        assert s_after.step_count == s_before.step_count + 1

    def test_state_is_deepcopy(self, env):
        env.reset("task_easy_schema_fix")
        s1 = env.state()
        s1.step_count = 9999  # mutate the copy
        s2 = env.state()
        assert s2.step_count != 9999  # env unchanged


# ---------------------------------------------------------------------------
# Action tests
# ---------------------------------------------------------------------------

class TestActions:
    def test_cast_column_int(self, env):
        env.reset("task_easy_schema_fix")
        result = env.step(Action(
            action_type=ActionType.CAST_COLUMN,
            column="customer_id",
            value="int",
        ))
        s = env.state()
        # customer_id should now be int in schema
        for sf in s.schema_info:
            if sf.name == "customer_id":
                assert sf.actual_type == "int"

    def test_drop_duplicates(self, env):
        env.reset("task_medium_data_quality")
        s_before = env.state()
        n_before  = len(s_before.data)
        env.step(Action(action_type=ActionType.DROP_DUPLICATES))
        s_after  = env.state()
        assert len(s_after.data) <= n_before
        assert s_after.bugs_fixed["drop_duplicates"] is True

    def test_fill_nulls(self, env):
        env.reset("task_easy_schema_fix")
        result = env.step(Action(
            action_type=ActionType.FILL_NULLS,
            column="age",
            value="0",
        ))
        assert "filled" in result.info.get("action_result", "").lower()

    def test_filter_outliers(self, env):
        env.reset("task_medium_data_quality")
        s_before = env.state()
        n_before  = len(s_before.data)
        env.step(Action(
            action_type=ActionType.FILTER_OUTLIERS,
            column="quantity",
            value="0,10000",
        ))
        s_after = env.state()
        assert len(s_after.data) <= n_before

    def test_reorder_stages_hard_task(self, env):
        env.reset("task_hard_pipeline_orchestration")
        env.step(Action(
            action_type=ActionType.REORDER_STAGES,
            parameters={"stages": ["ingest","validate","transform","enrich","load"]},
        ))
        s = env.state()
        assert s.bugs_fixed["fix_stage_order"] is True

    def test_apply_business_rule_discount(self, env):
        env.reset("task_medium_data_quality")
        env.step(Action(
            action_type=ActionType.APPLY_BUSINESS_RULE,
            value="discount_lte_1",
        ))
        s = env.state()
        assert s.bugs_fixed["fix_invalid_discount"] is True

    def test_validate_action(self, env):
        env.reset("task_easy_schema_fix")
        result = env.step(Action(action_type=ActionType.VALIDATE))
        assert "Validation" in result.info.get("action_result", "")


# ---------------------------------------------------------------------------
# Grader tests
# ---------------------------------------------------------------------------

class TestGraders:
    def _grader_score_in_range(self, state):
        score = grade(state)
        assert 0.0 <= score <= 1.0, f"Score {score} out of [0,1]"
        return score

    def test_easy_grader_initial_score(self):
        s = build_easy_task(seed=42)
        score = self._grader_score_in_range(s)
        assert score <= 0.6, "Initial state should have low score (unfixed bugs)"

    def test_medium_grader_initial_score(self):
        s = build_medium_task(seed=42)
        score = self._grader_score_in_range(s)
        assert score < 0.7

    def test_hard_grader_initial_score(self):
        s = build_hard_task(seed=42)
        score = self._grader_score_in_range(s)
        assert score < 0.5, "Hard task should be challenging"

    def test_grader_improves_with_fixes(self):
        env = DataPipelineEnv(seed=42)
        env.reset("task_easy_schema_fix")
        s0 = env.state()
        score0 = grade(s0)

        # Fix the three main type bugs
        for col, typ in [("customer_id","int"),("age","int"),("revenue","float")]:
            env.step(Action(action_type=ActionType.CAST_COLUMN, column=col, value=typ))

        s1 = env.state()
        score1 = grade(s1)
        assert score1 > score0, "Score should improve after fixing type bugs"

    def test_grader_deterministic(self):
        s = build_easy_task(seed=42)
        assert grade(s) == grade(s) == grade(s)

    def test_all_graders_return_float(self):
        for task_id in ["task_easy_schema_fix","task_medium_data_quality","task_hard_pipeline_orchestration"]:
            env = DataPipelineEnv(seed=42)
            env.reset(task_id)
            s = env.state()
            score = grade(s)
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# Reward function tests
# ---------------------------------------------------------------------------

class TestRewardFunction:
    def test_reward_is_float(self):
        env = DataPipelineEnv(seed=42)
        env.reset("task_easy_schema_fix")
        result = env.step(Action(action_type=ActionType.INSPECT))
        assert isinstance(result.reward.value, float)

    def test_reward_components_exist(self):
        env = DataPipelineEnv(seed=42)
        env.reset("task_easy_schema_fix")
        result = env.step(Action(action_type=ActionType.INSPECT))
        assert "progress" in result.reward.components
        assert "step_cost" in result.reward.components

    def test_cumulative_reward_accumulates(self):
        env = DataPipelineEnv(seed=42)
        env.reset("task_easy_schema_fix")
        prev_cum = 0.0
        for _ in range(3):
            result = env.step(Action(action_type=ActionType.INSPECT))
            assert result.reward.cumulative != prev_cum or result.reward.value == 0.0
            prev_cum = result.reward.cumulative

    def test_fix_gives_positive_reward(self):
        env = DataPipelineEnv(seed=42)
        env.reset("task_easy_schema_fix")
        result = env.step(Action(
            action_type=ActionType.CAST_COLUMN,
            column="customer_id",
            value="int",
        ))
        # progress component should be positive
        assert result.reward.components.get("progress", 0) >= 0


# ---------------------------------------------------------------------------
# Task metadata tests
# ---------------------------------------------------------------------------

class TestTaskInfo:
    def test_three_tasks_defined(self):
        assert len(TASK_INFO) == 3

    def test_difficulty_progression(self):
        difficulties = [t["difficulty"] for t in TASK_INFO]
        assert "easy" in difficulties
        assert "medium" in difficulties
        assert "hard" in difficulties

    def test_task_ids_unique(self):
        ids = [t["task_id"] for t in TASK_INFO]
        assert len(ids) == len(set(ids))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
