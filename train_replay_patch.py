"""
train_replay_patch.py
=====================
Shows EXACTLY what to add/change in your existing train.py to enable
the Replay Dashboard.  These are NOT full replacements — find the matching
lines in train.py and apply the three labelled patches.

PATCH 1 — import  (add at the top of train.py, with the other imports)
-----------------------------------------------------------------------
"""
from visualize import generate_replay_html, generate_reward_chart   # PATCH 1 (was: from visualize import generate_reward_chart)


"""
PATCH 2 — inside your episode loop, after env.step() returns done=True
-----------------------------------------------------------------------
Find the block in train.py that looks like:

    if done or step >= task.max_steps:
        training_results.append({"episode": ep, "score": score, "task": task_id})
        break

Replace with:
"""

def _patch_2_example(env, ep, score, task_id, training_results, output_dir="."):
    """
    Drop this block in place of (or right after) your episode-end logic.
    env      = DataPipelineEnvironment instance (has env.history populated)
    ep       = current episode index (int)
    score    = final score float
    task_id  = task string
    """
    import os

    # --- existing line (keep it) ---
    training_results.append({"episode": ep, "score": score, "task": task_id})

    # --- NEW: save replay every 10 episodes, always save the last episode ---
    if ep % 10 == 0 or score >= 0.95:
        replay_path = os.path.join(output_dir, f"replay_ep{ep}.html")
        generate_replay_html(
            episode_log = env.history,          # populated automatically by environment.py
            episode_num = ep,
            task_id     = task_id,
            final_score = score,
            output_path = replay_path,
        )
        print(f"[train] Replay saved → {replay_path}")


"""
PATCH 3 — after training loop ends, call generate_reward_chart as before
-------------------------------------------------------------------------
This is unchanged — just confirming the existing call still works:

    generate_reward_chart(training_results, output_path="training_results.html")

No change needed here.

──────────────────────────────────────────────────────────────
RESULTING FILE LAYOUT after patches
──────────────────────────────────────────────────────────────
After a run with --steps 1000 you will get:

    training_results.html     ← original reward curve (unchanged)
    replay_ep0.html           ← episode 0 replay
    replay_ep10.html          ← episode 10 replay
    ...
    replay_ep100.html         ← episode 100 replay (if ≥100 episodes)
    replay_ep<last>.html      ← final episode replay (always saved if score ≥ 0.95)

Open any replay_ep*.html in a browser — no server needed, fully standalone.
──────────────────────────────────────────────────────────────
"""


"""
QUICK TEST — run this file directly to verify the replay generator works
without touching train.py at all:

    python train_replay_patch.py

It will create  replay_ep_test.html  in the current directory.
"""
if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))

    from visualize import generate_replay_html

    # Synthetic episode log — same shape as StepRecord.to_dict()
    FAKE_EPISODE = [
        {"step":1,  "action":"inspect",            "params":{},                             "reward":0.00,  "cumulative_reward":0.000, "bugs_remaining":13, "description":"Scanned 107 rows, 9 cols. 13 bugs flagged."},
        {"step":2,  "action":"inspect",            "params":{},                             "reward":-0.07, "cumulative_reward":-0.070,"bugs_remaining":13, "description":"Re-scanned (repeat penalty applied)."},
        {"step":3,  "action":"cast_column",        "params":{"column":"order_id","dtype":"int64"},   "reward":0.04,  "cumulative_reward":-0.030,"bugs_remaining":12, "description":"Cast 'order_id' float → int64."},
        {"step":4,  "action":"drop_duplicates",    "params":{},                             "reward":0.06,  "cumulative_reward":0.030, "bugs_remaining":11, "description":"Removed 4 duplicate rows."},
        {"step":5,  "action":"fill_nulls",         "params":{"column":"order_value","value":"median"},"reward":0.06, "cumulative_reward":0.090,"bugs_remaining":10, "description":"Filled 12 nulls in 'order_value' with median 142.5."},
        {"step":6,  "action":"reorder_stages",     "params":{"order":["ingest","cast","validate","export"]},"reward":0.10,"cumulative_reward":0.190,"bugs_remaining":9,"description":"Reordered stages: ingest → cast → validate → export."},
        {"step":7,  "action":"filter_outliers",    "params":{"column":"fraud_score"},       "reward":0.06,  "cumulative_reward":0.250, "bugs_remaining":8, "description":"Filtered 3 outliers in 'fraud_score' > 1.0."},
        {"step":8,  "action":"cast_column",        "params":{"column":"order_value","dtype":"float64"},"reward":0.06,"cumulative_reward":0.310,"bugs_remaining":7,"description":"Cast 'order_value' object → float64."},
        {"step":9,  "action":"fill_nulls",         "params":{"column":"discount_pct","value":0.0},"reward":0.06, "cumulative_reward":0.370,"bugs_remaining":6,"description":"Filled 5 nulls in 'discount_pct' with 0.0."},
        {"step":10, "action":"apply_business_rule","params":{"rule":"discount_lte_1"},      "reward":0.08,  "cumulative_reward":0.450, "bugs_remaining":5, "description":"Applied discount_lte_1: clipped 2 rows."},
        {"step":11, "action":"apply_business_rule","params":{"rule":"currency_3char"},      "reward":0.08,  "cumulative_reward":0.530, "bugs_remaining":4, "description":"Applied currency_3char: renamed 'US' → 'USD'."},
        {"step":12, "action":"rename_column",      "params":{"old_name":"cust_id","new_name":"customer_id"},"reward":0.04,"cumulative_reward":0.570,"bugs_remaining":3,"description":"Renamed 'cust_id' → 'customer_id'."},
        {"step":13, "action":"drop_nulls",         "params":{"column":"customer_id"},       "reward":0.04,  "cumulative_reward":0.610, "bugs_remaining":2, "description":"Dropped 2 rows with null customer_id."},
        {"step":14, "action":"validate",           "params":{},                             "reward":0.00,  "cumulative_reward":0.610, "bugs_remaining":1, "description":"Validation score: 0.940. 1 bug remaining."},
        {"step":15, "action":"apply_business_rule","params":{"rule":"country_2char"},       "reward":0.08,  "cumulative_reward":0.690, "bugs_remaining":0, "description":"Applied country_2char: 'IND' → 'IN'."},
        {"step":16, "action":"validate",           "params":{},                             "reward":0.00,  "cumulative_reward":0.690, "bugs_remaining":0, "description":"All checks passed. 0 bugs. Ready to submit."},
        {"step":17, "action":"submit",             "params":{},                             "reward":0.291, "cumulative_reward":0.981, "bugs_remaining":0, "description":"Submitted. Final score: 0.981."},
    ]

    path = generate_replay_html(
        episode_log = FAKE_EPISODE,
        episode_num = 69,
        task_id     = "task_hard_pipeline_orchestration",
        final_score = 0.981,
        output_path = "replay_ep_test.html",
    )
    print(f"\nTest replay written → {path}")
    print("Open replay_ep_test.html in your browser to verify.")
