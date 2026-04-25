"""
train.py  —  OpenEnv Data Pipeline Debugger
============================================
Curriculum training script with TRL/Unsloth integration.

New in this version
-------------------
- Replay Dashboard: generates replay_ep{N}.html after key episodes
  (every 10 episodes + any episode scoring >= 0.95)
- All original logic (curriculum, noise decay, PPO snippet, CLI args) unchanged

Usage
-----
    python train.py --curriculum --steps 1000
    python train.py --steps 500 --task task_easy_schema_fix
    python train.py --curriculum --steps 1000 --replay-dir replays/
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import time
from dataclasses import dataclass, field
from typing import Optional

# ── path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import httpx

from curriculum import AgentSkillProfile, CurriculumManager
from env.environment import DataPipelineEnv
from inference import run_agent_episode
from visualize import generate_replay_html, generate_reward_chart

# ── constants ─────────────────────────────────────────────────────────────────

ENV_BASE_URL = os.environ.get("ENV_BASE_URL", "https://Harsha-2005-openenv-datapipeline.hf.space")
MODEL_NAME   = os.environ.get("MODEL_NAME",   "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN     = os.environ.get("HF_TOKEN",     "")

TASK_ORDER = [
    "task_easy_schema_fix",
    "task_medium_data_quality",
    "task_hard_pipeline_orchestration",
    "task_veryhard_streaming_pipeline",
    "task_expert_multi_source_join",
]

# Noise / exploration decay: starts high for exploration, decays to near-zero
NOISE_START = 0.80
NOISE_END   = 0.05
NOISE_DECAY = 0.96   # multiplied each episode

# Curriculum advancement threshold (rolling average over last N episodes)
ADVANCE_THRESHOLD   = 0.90
ADVANCE_WINDOW      = 3    # must hit threshold for this many consecutive episodes


# ── Argument parsing ──────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train agent on OpenEnv Data Pipeline Debugger")
    p.add_argument("--curriculum",  action="store_true",
                   help="Enable curriculum learning (auto-advance task difficulty)")
    p.add_argument("--steps",       type=int, default=500,
                   help="Total training episodes (default: 500)")
    p.add_argument("--task",        type=str, default="task_easy_schema_fix",
                   help="Starting task (ignored if --curriculum is set)")
    p.add_argument("--seed",        type=int, default=42,
                   help="Random seed for environment (default: 42)")
    p.add_argument("--noise-start", type=float, default=NOISE_START,
                   help=f"Initial exploration noise (default: {NOISE_START})")
    p.add_argument("--noise-end",   type=float, default=NOISE_END,
                   help=f"Final exploration noise (default: {NOISE_END})")
    p.add_argument("--replay-dir",  type=str, default=".",
                   help="Directory to save replay HTML files (default: current dir)")
    p.add_argument("--replay-every",type=int, default=10,
                   help="Save a replay file every N episodes (default: 10)")
    p.add_argument("--no-replay",   action="store_true",
                   help="Disable replay dashboard generation")
    p.add_argument("--ppo",         action="store_true",
                   help="Run PPO fine-tuning via Unsloth after curriculum (Colab only)")
    return p.parse_args()


# ── Replay helper ─────────────────────────────────────────────────────────────

def maybe_save_replay(
    env: DataPipelineEnv,
    episode: int,
    task_id: str,
    score: float,
    replay_dir: str,
    replay_every: int,
    no_replay: bool,
) -> None:
    """Save a replay HTML file if this episode meets the criteria."""
    if no_replay:
        return
    if not env.history:
        return

    save = (
        episode % replay_every == 0   # periodic checkpoint
        or score >= 0.95               # high-score episode — always capture
        or episode == 0                # always save first episode (shows baseline)
    )
    if not save:
        return

    os.makedirs(replay_dir, exist_ok=True)
    out_path = os.path.join(replay_dir, f"replay_ep{episode}.html")

    try:
        generate_replay_html(
            episode_log = env.history,
            episode_num = episode,
            task_id     = task_id,
            final_score = score,
            output_path = out_path,
        )
        print(f"  [replay] Saved -> {out_path}")
    except Exception as exc:
        print(f"  [replay] WARNING: could not save replay: {exc}", file=sys.stderr)


# ── Single episode runner ─────────────────────────────────────────────────────

def run_episode(
    task_id:    str,
    seed:       int,
    noise:      float,
    episode:    int,
) -> tuple[float, int, DataPipelineEnv]:
    """
    Run one full episode against the live HF Space environment.

    Returns
    -------
    score : float   — final submitted score (or 0.0 on failure)
    steps : int     — number of steps taken
    env   : DataPipelineEnv  — populated .history for replay
    """
    env = DataPipelineEnv(task_id=task_id, seed=seed)

    try:
        obs = env.reset()
        print(f"  [ep {episode:>4}] task={task_id.replace('task_',''):<30} noise={noise:.3f}")

        score, steps = run_agent_episode(
            env        = env,
            task_id    = task_id,
            noise      = noise,
            episode    = episode,
            base_url   = ENV_BASE_URL,
            model_name = MODEL_NAME,
            hf_token   = HF_TOKEN,
        )
        return score, steps, env

    except httpx.HTTPStatusError as exc:
        print(f"  [ep {episode}] HTTP error {exc.response.status_code}: {exc}", file=sys.stderr)
        return 0.0, 0, env
    except Exception as exc:
        print(f"  [ep {episode}] Error: {exc}", file=sys.stderr)
        return 0.0, 0, env


# ── Curriculum logic ──────────────────────────────────────────────────────────

def should_advance(recent_scores: list[float], window: int, threshold: float) -> bool:
    """Return True if the last `window` scores all meet `threshold`."""
    if len(recent_scores) < window:
        return False
    return all(s >= threshold for s in recent_scores[-window:])


# ── PPO / Unsloth fine-tuning snippet ─────────────────────────────────────────

def run_ppo_finetuning(training_results: list[dict]) -> None:
    """
    Minimal Unsloth + TRL GRPO/PPO fine-tuning stub.
    Run this in Google Colab with the provided compute credits.

    Install:
        pip install unsloth trl accelerate
    """
    print("\n[ppo] Starting PPO fine-tuning with Unsloth …")

    try:
        from unsloth import FastLanguageModel
        from trl import GRPOConfig, GRPOTrainer
    except ImportError:
        print("[ppo] Unsloth/TRL not installed. Run in Colab with: pip install unsloth trl")
        return

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name     = "unsloth/Qwen2.5-7B-Instruct",
        max_seq_length = 2048,
        load_in_4bit   = True,
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r              = 16,
        target_modules = ["q_proj", "v_proj"],
        lora_alpha     = 16,
        lora_dropout   = 0,
        use_gradient_checkpointing = "unsloth",
    )

    # Build a minimal reward function from training_results
    best_task = max(training_results, key=lambda r: r["score"])["task"]
    print(f"[ppo] Fine-tuning on task: {best_task}")

    config = GRPOConfig(
        output_dir          = "./ppo_checkpoints",
        num_train_epochs    = 1,
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        learning_rate       = 2e-5,
        logging_steps       = 10,
        save_steps          = 50,
    )

    print("[ppo] GRPOConfig ready. Attach dataset + reward_fn to GRPOTrainer to proceed.")
    print("[ppo] See: https://huggingface.co/docs/trl/grpo_trainer")


# ── Main training loop ────────────────────────────────────────────────────────

def train(args: argparse.Namespace) -> None:
    print("=" * 60)
    print("  OpenEnv Data Pipeline Debugger — Training")
    print(f"  Episodes : {args.steps}")
    print(f"  Curriculum: {args.curriculum}")
    print(f"  Replay dir: {args.replay_dir if not args.no_replay else 'disabled'}")
    print("=" * 60)

    # ── Setup ──────────────────────────────────────────────────────────────
    curriculum_mgr = CurriculumManager() if args.curriculum else None
    skill_profile  = AgentSkillProfile()

    current_task_idx = 0
    current_task     = TASK_ORDER[current_task_idx] if args.curriculum else args.task

    noise           = args.noise_start
    training_results: list[dict] = []
    recent_scores:    list[float] = []

    t0 = time.time()

    # ── Episode loop ────────────────────────────────────────────────────────
    for ep in range(args.steps):
        seed = args.seed + ep   # vary seed each episode so agent doesn't memorise

        score, steps, env = run_episode(
            task_id = current_task,
            seed    = seed,
            noise   = noise,
            episode = ep,
        )

        print(f"           score={score:.4f}  steps={steps}")

        # Record result
        training_results.append({
            "episode": ep,
            "score":   score,
            "task":    current_task,
            "steps":   steps,
            "noise":   round(noise, 4),
        })

        # ── NEW: Replay Dashboard ──────────────────────────────────────────
        maybe_save_replay(
            env        = env,
            episode    = ep,
            task_id    = current_task,
            score      = score,
            replay_dir = args.replay_dir,
            replay_every = args.replay_every,
            no_replay  = args.no_replay,
        )

        # ── Noise decay ───────────────────────────────────────────────────
        noise = max(args.noise_end, noise * NOISE_DECAY)

        # ── Curriculum advancement ─────────────────────────────────────────
        if args.curriculum:
            recent_scores.append(score)
            if len(recent_scores) > ADVANCE_WINDOW * 2:
                recent_scores.pop(0)

            if should_advance(recent_scores, ADVANCE_WINDOW, ADVANCE_THRESHOLD):
                if current_task_idx < len(TASK_ORDER) - 1:
                    current_task_idx += 1
                    current_task      = TASK_ORDER[current_task_idx]
                    recent_scores     = []   # reset window for new task
                    print(f"\n  [curriculum] *** Advancing to: {current_task} ***\n")

                    # Update skill profile
                    skill_profile.record_advancement(
                        from_task = TASK_ORDER[current_task_idx - 1],
                        to_task   = current_task,
                        episode   = ep,
                    )
                else:
                    print(f"\n  [curriculum] Expert task mastered at episode {ep}!\n")

            # Also let CurriculumManager weigh in
            if curriculum_mgr is not None:
                suggested = curriculum_mgr.suggest_task(skill_profile)
                if suggested and suggested != current_task:
                    current_task = suggested
                    print(f"  [curriculum] Manager override -> {current_task}")

        # ── Progress summary every 25 episodes ────────────────────────────
        if (ep + 1) % 25 == 0:
            recent = training_results[-25:]
            avg    = sum(r["score"] for r in recent) / len(recent)
            best   = max(r["score"] for r in training_results)
            elapsed = time.time() - t0
            print(f"\n  -- Episode {ep+1}/{args.steps} | "
                  f"avg(last 25)={avg:.4f} | best={best:.4f} | "
                  f"task={current_task.replace('task_','')} | "
                  f"elapsed={elapsed:.0f}s --\n")

    # ── Post-training ────────────────────────────────────────────────────────
    elapsed = time.time() - t0
    best_result = max(training_results, key=lambda r: r["score"])
    final_avg   = sum(r["score"] for r in training_results[-20:]) / min(20, len(training_results))

    print("\n" + "=" * 60)
    print("  Training complete")
    print(f"  Total episodes : {len(training_results)}")
    print(f"  Best score     : {best_result['score']:.4f}  (ep {best_result['episode']})")
    print(f"  Final avg(20)  : {final_avg:.4f}")
    print(f"  Elapsed        : {elapsed:.1f}s")
    print("=" * 60)

    # Generate reward curve chart (original, unchanged)
    chart_path = generate_reward_chart(
        training_results = training_results,
        output_path      = "training_results.html",
    )
    print(f"\n  Reward chart   -> {chart_path}")

    # Save final episode replay if not already saved
    if not args.no_replay:
        last_ep  = len(training_results) - 1
        last_res = training_results[-1]
        # Rebuild env for final episode to get history
        _, _, final_env = run_episode(
            task_id = last_res["task"],
            seed    = args.seed + last_ep,
            noise   = args.noise_end,
            episode = last_ep,
        )
        if final_env.history:
            final_replay = os.path.join(args.replay_dir, "replay_final.html")
            generate_replay_html(
                episode_log = final_env.history,
                episode_num = last_ep,
                task_id     = last_res["task"],
                final_score = last_res["score"],
                output_path = final_replay,
            )
            print(f"  Final replay   -> {final_replay}")

    # ── Optional PPO fine-tuning ──────────────────────────────────────────
    if args.ppo:
        run_ppo_finetuning(training_results)

    # Output enhanced training report
    from analytics import generate_training_report
    report_path = os.path.join(args.replay_dir, "training_report.html")
    generate_training_report(training_results, output_path=report_path)

    print("\nDone. Open training_report.html and any replay_ep*.html in your browser.")

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = parse_args()
    train(args)