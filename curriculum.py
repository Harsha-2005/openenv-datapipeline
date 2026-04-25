"""
curriculum.py — Curriculum Learning & Self-Improvement System
Theme 4: Self-Improving Agent Systems

The agent:
  1. Starts on Easy tasks
  2. Auto-advances when it masters them (score >= threshold)
  3. Generates harder variants of tasks it struggles with
  4. Tracks skill growth across all 5 difficulty levels

This directly addresses Theme 4 (Self-Improvement) and the
Scaler AI Labs sub-theme for Enterprise Workflows.
"""

from __future__ import annotations
import json
import os
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ── Curriculum configuration ─────────────────────────────────────────────────

TASK_PROGRESSION = [
    ("task_easy_schema_fix",            0.80),  # advance when score >= 0.80
    ("task_medium_data_quality",         0.75),  # advance when score >= 0.75
    ("task_hard_pipeline_orchestration", 0.70),  # advance when score >= 0.70
    ("task_veryhard_streaming_pipeline", 0.65),  # advance when score >= 0.65
    ("task_expert_multi_source_join",    0.60),  # mastered the environment
]

DIFFICULTY_NAMES = {
    "task_easy_schema_fix":            "Easy",
    "task_medium_data_quality":         "Medium",
    "task_hard_pipeline_orchestration": "Hard",
    "task_veryhard_streaming_pipeline": "Very Hard",
    "task_expert_multi_source_join":    "Expert",
}


@dataclass
class AgentSkillProfile:
    """Tracks an agent's skill growth across all tasks."""
    agent_id:       str                          = "default_agent"
    total_episodes: int                          = 0
    task_scores:    Dict[str, List[float]]       = field(default_factory=dict)
    current_level:  int                          = 0   # index into TASK_PROGRESSION
    level_history:  List[Tuple[str, int, float]] = field(default_factory=list)
    # (task_id, episode_number, score_when_advanced)

    @property
    def current_task(self) -> str:
        return TASK_PROGRESSION[min(self.current_level,
                                    len(TASK_PROGRESSION)-1)][0]

    @property
    def advancement_threshold(self) -> float:
        return TASK_PROGRESSION[min(self.current_level,
                                    len(TASK_PROGRESSION)-1)][1]

    @property
    def mastery_level(self) -> str:
        return DIFFICULTY_NAMES.get(self.current_task, "Unknown")

    def record_score(self, task_id: str, score: float):
        if task_id not in self.task_scores:
            self.task_scores[task_id] = []
        self.task_scores[task_id].append(round(score, 4))
        self.total_episodes += 1

    def recent_avg(self, task_id: str, window: int = 5) -> float:
        scores = self.task_scores.get(task_id, [])
        if not scores:
            return 0.0
        recent = scores[-window:]
        return sum(recent) / len(recent)

    def should_advance(self) -> bool:
        """Check if agent has mastered current task."""
        if self.current_level >= len(TASK_PROGRESSION) - 1:
            return False
        task_id   = self.current_task
        threshold = self.advancement_threshold
        avg_score = self.recent_avg(task_id, window=5)
        episodes_on_task = len(self.task_scores.get(task_id, []))
        # Need at least 5 episodes and average >= threshold
        return episodes_on_task >= 5 and avg_score >= threshold

    def advance(self):
        """Move agent to the next difficulty level."""
        task_id   = self.current_task
        avg_score = self.recent_avg(task_id)
        self.level_history.append((task_id, self.total_episodes, avg_score))
        self.current_level = min(self.current_level + 1, len(TASK_PROGRESSION) - 1)

    def summary(self) -> Dict:
        return {
            "agent_id":       self.agent_id,
            "mastery_level":  self.mastery_level,
            "current_task":   self.current_task,
            "total_episodes": self.total_episodes,
            "level_history":  [
                {"task": t, "episode": e, "score": s}
                for t, e, s in self.level_history
            ],
            "task_averages": {
                task: round(self.recent_avg(task, 10), 4)
                for task in self.task_scores
            },
        }

    def to_json(self) -> str:
        return json.dumps(self.summary(), indent=2)

    def record_advancement(self, from_task: str, to_task: str, episode: int):
        """Record a curriculum advancement event."""
        avg_score = self.recent_avg(from_task)
        self.level_history.append((from_task, episode, avg_score))


class CurriculumManager:
    """
    Manages curriculum learning for one or more agents.
    Implements auto-advancement and difficulty scaling.
    """

    def __init__(self, seed: int = 42):
        self.rng     = random.Random(seed)
        self.agents: Dict[str, AgentSkillProfile] = {}

    def register_agent(self, agent_id: str) -> AgentSkillProfile:
        profile = AgentSkillProfile(agent_id=agent_id)
        self.agents[agent_id] = profile
        return profile

    def get_task_for_agent(self, agent_id: str) -> str:
        """Return the appropriate task for this agent's current level."""
        profile = self.agents.get(agent_id)
        if profile is None:
            profile = self.register_agent(agent_id)
        return profile.current_task

    def record_episode(self, agent_id: str, task_id: str,
                       score: float) -> Dict:
        """
        Record an episode result and check for advancement.
        Returns dict with advancement info.
        """
        profile = self.agents.get(agent_id)
        if profile is None:
            profile = self.register_agent(agent_id)

        profile.record_score(task_id, score)
        advanced = False
        new_task  = task_id

        if profile.should_advance():
            old_task = profile.current_task
            profile.advance()
            new_task = profile.current_task
            advanced  = True
            print(f"  🎓 Agent '{agent_id}' ADVANCED: "
                  f"{DIFFICULTY_NAMES[old_task]} → {DIFFICULTY_NAMES[new_task]} "
                  f"(avg score: {profile.recent_avg(old_task):.4f})")

        return {
            "agent_id":   agent_id,
            "task_id":    task_id,
            "score":      score,
            "advanced":   advanced,
            "next_task":  new_task,
            "level":      profile.mastery_level,
            "avg_score":  profile.recent_avg(task_id),
        }

    def run_curriculum(self, agent_id: str,
                       total_episodes: int = 100,
                       score_fn=None,
                       verbose: bool = True) -> AgentSkillProfile:
        """
        Run full curriculum for an agent.

        score_fn: callable(task_id, episode) -> float
                  If None, uses a simulated improving agent.
        """
        profile = self.register_agent(agent_id)

        if score_fn is None:
            # Simulate an agent that improves with experience
            def score_fn(task_id: str, episode: int) -> float:
                difficulty_penalty = {
                    "task_easy_schema_fix":            0.00,
                    "task_medium_data_quality":         0.10,
                    "task_hard_pipeline_orchestration": 0.20,
                    "task_veryhard_streaming_pipeline": 0.30,
                    "task_expert_multi_source_join":    0.40,
                }.get(task_id, 0.25)

                episodes_on_task = len(profile.task_scores.get(task_id, []))
                # Score improves with practice, up to a ceiling
                learning_gain = min(0.45, episodes_on_task * 0.04)
                base = 0.50 - difficulty_penalty + learning_gain
                noise = self.rng.gauss(0, 0.03)
                return round(min(0.999, max(0.001, base + noise)), 4)

        if verbose:
            print(f"\nCurriculum Learning — Agent: {agent_id}")
            print(f"Total episodes: {total_episodes}")
            print("-" * 50)

        for ep in range(total_episodes):
            task_id = profile.current_task
            score   = score_fn(task_id, ep)
            result  = self.record_episode(agent_id, task_id, score)

            if verbose and ep % 10 == 0:
                print(f"  Ep {ep:3d} | Task: {DIFFICULTY_NAMES[task_id]:10s} | "
                      f"Score: {score:.4f} | "
                      f"Avg(5): {profile.recent_avg(task_id):.4f} | "
                      f"Level: {profile.mastery_level}")

            # Stop if mastered everything
            if (profile.current_level == len(TASK_PROGRESSION) - 1 and
                    profile.recent_avg(profile.current_task, 5) >= 0.60):
                if verbose:
                    print(f"\n  ✅ Agent mastered all levels at episode {ep}!")
                break

        if verbose:
            print("\n" + "=" * 50)
            print("CURRICULUM COMPLETE")
            print(profile.to_json())

        return profile

    def leaderboard(self) -> List[Dict]:
        """Rank all agents by mastery level and score."""
        entries = []
        for agent_id, profile in self.agents.items():
            entries.append({
                "agent_id":      agent_id,
                "mastery_level": profile.mastery_level,
                "level_index":   profile.current_level,
                "total_episodes":profile.total_episodes,
                "best_task_avg": max(
                    (profile.recent_avg(t, 10) for t in profile.task_scores),
                    default=0.0
                ),
            })
        return sorted(entries,
                      key=lambda x: (x["level_index"], x["best_task_avg"]),
                      reverse=True)

    def suggest_task(self, profile: AgentSkillProfile) -> Optional[str]:
        """Suggest the best task for the agent based on its skill profile."""
        if profile.should_advance():
            next_level = min(profile.current_level + 1, len(TASK_PROGRESSION) - 1)
            return TASK_PROGRESSION[next_level][0]
        return profile.current_task


# ── Self-play difficulty scaler ───────────────────────────────────────────────

class AdaptiveDifficultyScaler:
    """
    Automatically scales task difficulty based on agent performance.
    Theme 4: Self-Improving Agent Systems.

    If agent is doing too well  → increase noise/complexity
    If agent is doing too poorly → decrease complexity, provide hints
    """

    def __init__(self, target_score: float = 0.70):
        self.target_score   = target_score
        self.recent_scores: List[float] = []
        self.current_seeds  = [42, 123, 777, 2024, 9999]
        self.seed_index     = 0

    def record(self, score: float):
        self.recent_scores.append(score)
        if len(self.recent_scores) > 10:
            self.recent_scores.pop(0)

    def next_seed(self) -> int:
        """Rotate through seeds for variety."""
        seed = self.current_seeds[self.seed_index % len(self.current_seeds)]
        self.seed_index += 1
        return seed

    def get_difficulty_params(self) -> Dict:
        """
        Returns parameters for next episode based on recent performance.
        """
        if len(self.recent_scores) < 3:
            return {"hint_level": "full", "noise": 0.0, "seed": self.next_seed()}

        avg = sum(self.recent_scores) / len(self.recent_scores)

        if avg > self.target_score + 0.15:
            # Agent is doing great → make it harder
            return {
                "hint_level": "none",
                "noise": 0.1,
                "seed": self.next_seed(),
                "message": f"Increasing difficulty (avg={avg:.3f})",
            }
        elif avg < self.target_score - 0.15:
            # Agent is struggling → give more hints
            return {
                "hint_level": "full",
                "noise": 0.0,
                "seed": 42,  # use known easy seed
                "message": f"Reducing difficulty (avg={avg:.3f})",
            }
        else:
            # On target
            return {
                "hint_level": "partial",
                "noise": 0.0,
                "seed": self.next_seed(),
                "message": f"On target (avg={avg:.3f})",
            }


# ── Demo ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== Curriculum Learning Demo ===\n")

    manager = CurriculumManager(seed=42)

    # Run curriculum for a single agent
    profile = manager.run_curriculum(
        agent_id       = "baseline_agent",
        total_episodes = 80,
        verbose        = True,
    )

    print("\n=== Leaderboard ===")
    for entry in manager.leaderboard():
        print(f"  {entry['agent_id']:20s} | "
              f"Level: {entry['mastery_level']:10s} | "
              f"Episodes: {entry['total_episodes']:3d}")

    print("\n=== Adaptive Difficulty Demo ===")
    scaler = AdaptiveDifficultyScaler(target_score=0.70)
    for score in [0.50, 0.55, 0.65, 0.72, 0.80, 0.88, 0.91]:
        scaler.record(score)
        params = scaler.get_difficulty_params()
        print(f"  Score: {score:.2f} → {params.get('message','on target')}")
