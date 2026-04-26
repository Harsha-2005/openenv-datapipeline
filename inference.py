#!/usr/bin/env python3
"""
inference.py — Baseline inference script for OpenEnv Data Pipeline Debugger.

Uses the OpenAI client configured via environment variables:
  API_BASE_URL   — LLM API endpoint
  MODEL_NAME     — model identifier
  HF_TOKEN       — API key
  ENV_BASE_URL   — environment server URL (default: http://localhost:7860)

Stdout emits structured [START]/[STEP]/[END] blocks as required by evaluator.
"""

from __future__ import annotations
import json, os, re, sys, time, traceback
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
<<<<<<< HEAD
=======
# Load .env file (for local runs — on HF Space env vars are set via secrets)
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required — env vars may be set externally

# ---------------------------------------------------------------------------
>>>>>>> 03d62d9 (updated the demo and dashboard file and added the training using the grpo)
# Configuration — read from environment variables
# ---------------------------------------------------------------------------
API_BASE_URL = os.environ.get("API_BASE_URL", "")
MODEL_NAME   = os.environ.get("MODEL_NAME",   "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN     = os.environ.get("HF_TOKEN",     "")
ENV_BASE_URL = os.environ.get("ENV_BASE_URL", "http://localhost:7860").rstrip("/")

TASKS = [
    "task_easy_schema_fix",
    "task_medium_data_quality",
    "task_hard_pipeline_orchestration",
    "task_veryhard_streaming_pipeline",
    "task_expert_multi_source_join",
]
SEED = 42

# ---------------------------------------------------------------------------
# Environment HTTP client
# ---------------------------------------------------------------------------
import urllib.request
import urllib.error

def _env_request(method: str, path: str, body=None) -> Dict:
    url  = ENV_BASE_URL + path
    data = json.dumps(body).encode() if body is not None else None
    req  = urllib.request.Request(
        url, data=data, method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())

def env_reset(task_id: str, seed: int = SEED) -> Dict:
    return _env_request("POST", "/reset", {"task_id": task_id, "seed": seed})

def env_step(action_type: str, column=None, value=None, parameters=None) -> Dict:
    return _env_request("POST", "/step", {
        "action_type": action_type,
        "column":      column,
        "value":       value,
        "parameters":  parameters,
    })

# ---------------------------------------------------------------------------
# LLM client — initialised after config check
# ---------------------------------------------------------------------------
client = None

# ── Few-shot self-improvement memory (Change 2) ──────────────────────────────
# Stores best episode action sequences for injection into system prompt.
# When score >= 0.95, we save the action sequence here.
_fewshot_examples: list[dict] = []   # [{"task_id": ..., "score": ..., "actions": [...]}]
MAX_FEWSHOT_EXAMPLES = 3             # keep top 3 best runs

def record_best_episode(task_id: str, score: float, actions: list[dict]):
    """Save a high-scoring episode's action sequence for few-shot prompting."""
    global _fewshot_examples
    entry = {"task_id": task_id, "score": score, "actions": actions[:20]}  # cap at 20 actions
    _fewshot_examples.append(entry)
    _fewshot_examples.sort(key=lambda x: x["score"], reverse=True)
    _fewshot_examples = _fewshot_examples[:MAX_FEWSHOT_EXAMPLES]
    print(f"  [fewshot] Recorded best episode: task={task_id} score={score:.4f} "
          f"({len(actions)} actions). Memory: {len(_fewshot_examples)} examples.")

def _build_fewshot_block() -> str:
    """Build a few-shot examples block for the system prompt."""
    if not _fewshot_examples:
        return ""
    lines = ["\n\nFEW-SHOT EXAMPLES (high-scoring past runs — follow these patterns):"]
    for i, ex in enumerate(_fewshot_examples):
        actions_str = " → ".join(
            a.get("action_type", "?") + (f"({a.get('column','')})" if a.get('column') else "")
            for a in ex["actions"]
        )
        lines.append(f"  Example {i+1} (task={ex['task_id']}, score={ex['score']:.2f}): {actions_str}")
    return "\n".join(lines)

SYSTEM_PROMPT = """\
You are a data pipeline debugger. Output ONLY a single JSON object — no explanation, \
no markdown, no code fences, no extra text. Raw JSON only.

VALID ACTIONS:
{"action_type":"inspect"}
{"action_type":"cast_column","column":"COLNAME","value":"int"}
{"action_type":"cast_column","column":"COLNAME","value":"float"}
{"action_type":"cast_column","column":"COLNAME","value":"str"}
{"action_type":"drop_duplicates"}
{"action_type":"drop_nulls","column":"COLNAME"}
{"action_type":"fill_nulls","column":"COLNAME","value":"FILL_VALUE"}
{"action_type":"filter_outliers","column":"COLNAME","value":"MIN,MAX"}
{"action_type":"apply_business_rule","value":"discount_lte_1"}
{"action_type":"apply_business_rule","value":"fraud_score_lte_1"}
{"action_type":"apply_business_rule","value":"currency_3char"}
{"action_type":"apply_business_rule","value":"country_2char"}
{"action_type":"reorder_stages","parameters":{"stages":["ingest","validate","transform","enrich","load"]}}
{"action_type":"validate"}
{"action_type":"submit"}

STRATEGY: inspect once, then fix schema (cast_column), drop_duplicates, fill_nulls, \
filter_outliers, apply_business_rule, validate, submit.
Output ONLY the JSON object."""

VALID_ACTIONS = {
    "inspect","cast_column","drop_nulls","fill_nulls","drop_duplicates",
    "filter_outliers","rename_column","reorder_stages","apply_business_rule",
    "validate","submit"
}

def _extract_json(text: str) -> Optional[Dict]:
    if not text:
        return None
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for m in re.findall(r"```(?:json)?\s*([\s\S]*?)```", text):
        try:
            return json.loads(m.strip())
        except json.JSONDecodeError:
            pass
    m = re.search(r'\{[^{}]*\}', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    try:
        start = text.index('{')
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == '{': depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return json.loads(text[start:i+1])
    except (ValueError, json.JSONDecodeError):
        pass
    m = re.search(r'"action_type"\s*:\s*"([^"]+)"', text)
    if m:
        result: Dict[str, Any] = {"action_type": m.group(1)}
        cm = re.search(r'"column"\s*:\s*"([^"]+)"', text)
        vm = re.search(r'"value"\s*:\s*"([^"]+)"', text)
        if cm: result["column"] = cm.group(1)
        if vm: result["value"]  = vm.group(1)
        return result
    return None

def _rule_based_fallback(obs: Dict, inspect_count: int, last_actions: List[str]) -> Dict:
    task_id     = obs.get("task_id", "")
    schema_info = obs.get("schema_info", [])
    error_log   = obs.get("error_log", [])
    errors_str  = " ".join(error_log).lower()
    hint        = obs.get("hint", "")

    # Handle stage reordering for Hard, VeryHard, and Expert tasks
    if task_id in ("task_hard_pipeline_orchestration", "task_veryhard_streaming_pipeline", "task_expert_multi_source_join"):
        already_reordered = "reorder_stages" in last_actions
        if not already_reordered and ("stage order" in errors_str or "wrong" in errors_str or "reorder" in hint.lower()):
            return {"action_type": "reorder_stages",
                    "parameters": {"stages": ["ingest","validate","transform","enrich","load"]}}

    for sf in schema_info:
        name   = sf.get("name","")   if isinstance(sf,dict) else getattr(sf,"name","")
        exp    = sf.get("expected_type","") if isinstance(sf,dict) else getattr(sf,"expected_type","")
        actual = sf.get("actual_type","")   if isinstance(sf,dict) else getattr(sf,"actual_type","")
        if exp and actual and exp != actual and f"cast:{name}" not in last_actions:
            return {"action_type": "cast_column", "column": name, "value": exp}

    if "discount" in errors_str and "rule:discount" not in str(last_actions):
        return {"action_type": "apply_business_rule", "value": "discount_lte_1"}
    if "fraud_score" in errors_str and "rule:fraud" not in str(last_actions):
        return {"action_type": "apply_business_rule", "value": "fraud_score_lte_1"}
    if "currency" in errors_str and "rule:currency" not in str(last_actions):
        return {"action_type": "apply_business_rule", "value": "currency_3char"}
    if "country_code" in errors_str and "rule:country" not in str(last_actions):
        return {"action_type": "apply_business_rule", "value": "country_2char"}

    if "duplicate" in errors_str and "drop_duplicates" not in last_actions:
        return {"action_type": "drop_duplicates"}

    if "negative" in errors_str or "outlier" in errors_str:
        for col, mn, mx in [("quantity","0","9999"),("unit_price","0","99999"),("amount","0","999999"),("value","0","99999"),("latency_ms","0","30000")]:
            if col in errors_str and f"filter:{col}" not in last_actions:
                return {"action_type": "filter_outliers", "column": col, "value": f"{mn},{mx}"}

    NULL_FILLS = {
        "task_easy_schema_fix":              [("age","0"),("revenue","0.0"),("email","unknown@example.com")],
        "task_medium_data_quality":           [("quantity","1"),("unit_price","0.0"),("region","UNKNOWN"),("order_date","2024-01-01")],
        "task_hard_pipeline_orchestration":   [("merchant","UNKNOWN"),("fraud_score","0.0"),("category","UNKNOWN"),("country_code","US"),("currency","USD")],
        "task_veryhard_streaming_pipeline":   [("event_type","UNKNOWN"),("session_id","unknown"),("region","UNKNOWN"),("value","0.0"),("latency_ms","0")],
        "task_expert_multi_source_join":      [("customer_name","UNKNOWN"),("product_name","UNKNOWN"),("category","UNKNOWN"),("email","unknown@example.com")],
    }
    if "null" in errors_str:
        for col, val in NULL_FILLS.get(task_id, []):
            if f"fill:{col}" not in last_actions:
                return {"action_type": "fill_nulls", "column": col, "value": val}

    if "validate" not in last_actions[-3:]:
        return {"action_type": "validate"}
    return {"action_type": "submit"}

def llm_choose_action(obs: Dict, history: List[Dict],
                       inspect_count: int, last_actions: List[str]):
    step = obs.get("step_count", 0)
    schema_lines = []
    for sf in obs.get("schema_info", []):
        name   = sf.get("name","")   if isinstance(sf,dict) else getattr(sf,"name","")
        exp    = sf.get("expected_type","") if isinstance(sf,dict) else getattr(sf,"expected_type","")
        actual = sf.get("actual_type","")   if isinstance(sf,dict) else getattr(sf,"actual_type","")
        match  = "OK" if exp == actual else f"MISMATCH→{exp}"
        schema_lines.append(f"  {name}: {actual} {match}")

    user_msg = (
        f"Step {step}/{obs.get('max_steps')} | Task: {obs.get('task_id')}\n"
        f"Hint: {obs.get('hint','')}\n"
        f"Inspected {inspect_count} time(s). Recent: {last_actions[-5:]}\n"
        f"Schema:\n" + "\n".join(schema_lines) + "\n"
        f"Metrics: {json.dumps(obs.get('metrics',{}))}\n"
        f"Errors: {obs.get('error_log',[])[-3:]}\n"
        f"Output ONLY the JSON action:"
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    # Inject few-shot examples if available (Change 2: Self-improvement)
    fewshot_block = _build_fewshot_block()
    enriched_prompt = SYSTEM_PROMPT + fewshot_block

    messages = [{"role": "system", "content": enriched_prompt}]
    messages += history[-6:]
    messages.append({"role": "user", "content": user_msg})

    raw = ""
    try:
        if client:
            resp = client.chat.completions.create(
                model=MODEL_NAME, messages=messages, max_tokens=200, temperature=0.0)
            # Use temperature=0.5 for training exploration, 0.0 for evaluation
            temp = 0.5 if _fewshot_examples or len(history) > 0 else 0.0
            resp = client.chat.completions.create(
                model=MODEL_NAME, messages=messages, max_tokens=200, temperature=temp)
            raw = resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"[WARNING] LLM call failed: {e}", file=sys.stderr)

    print(f"[DEBUG] LLM raw: {raw[:200]!r}", file=sys.stderr)

    action = _extract_json(raw)
    if action and action.get("action_type") in VALID_ACTIONS:
        print(f"[DEBUG] LLM parsed OK: {action}", file=sys.stderr)
        return action, raw, False

    print("[WARNING] LLM parse failed → rule-based fallback", file=sys.stderr)
    fallback = _rule_based_fallback(obs, inspect_count, last_actions)
    print(f"[DEBUG] Fallback: {fallback}", file=sys.stderr)
    return fallback, raw, True

# ---------------------------------------------------------------------------
# Episode runner — prints [START]/[STEP]/[END] to STDOUT
# ---------------------------------------------------------------------------
def run_task(task_id: str) -> Dict[str, Any]:
    obs           = env_reset(task_id, seed=SEED)
    done          = obs.get("done", False)
    step_count    = 0
    history: List[Dict] = []
    total_reward  = 0.0
    inspect_count = 0
    last_actions: List[str] = []
    info: Dict   = {}
    max_steps     = obs.get("max_steps", 40)

    # ---- [START] block — plain text format as required by evaluator ----
    print(f"[START] task={task_id} seed={SEED} max_steps={max_steps}", flush=True)

    while not done and step_count < max_steps:
        t0 = time.time()

        action_dict, raw, used_fallback = llm_choose_action(
            obs, history, inspect_count, last_actions)

        at     = action_dict.get("action_type", "inspect")
        col    = action_dict.get("column")
        val    = action_dict.get("value")
        params = action_dict.get("parameters")

        if at == "inspect":
            inspect_count += 1

        if at == "cast_column" and col:       last_actions.append(f"cast:{col}")
        elif at == "fill_nulls" and col:      last_actions.append(f"fill:{col}")
        elif at == "filter_outliers" and col: last_actions.append(f"filter:{col}")
        elif at == "apply_business_rule" and val: last_actions.append(f"rule:{val[:10]}")
        else: last_actions.append(at)

        try:
            result = env_step(at, col, val, params)
        except Exception as e:
            print(f"[WARNING] env_step error: {e}", file=sys.stderr)
            result = {
                "observation": obs,
                "reward": {"value": -0.05, "cumulative": total_reward, "components": {}, "explanation": str(e)},
                "done": False, "info": {"error": str(e)},
            }

        new_obs      = result.get("observation", obs)
        reward_info  = result.get("reward", {})
        done         = result.get("done", False)
        info         = result.get("info", {})
        step_reward  = reward_info.get("value", 0.0)
        total_reward = reward_info.get("cumulative", total_reward + step_reward)
        latency_ms   = round((time.time() - t0) * 1000, 1)
        metrics      = new_obs.get("metrics", {})

        # ---- [STEP] block — plain text format ----
        print(
            f"[STEP] task={task_id} step={step_count+1} "
            f"action={at} reward={step_reward:.4f} "
            f"cumulative_reward={total_reward:.4f} done={str(done).lower()} "
            f"completeness={metrics.get('completeness',0):.3f} "
            f"validity={metrics.get('validity',0):.3f} "
            f"accuracy={metrics.get('accuracy',0):.3f}",
            flush=True
        )

        history.append({"role": "assistant", "content": raw or json.dumps(action_dict)})
        history.append({"role": "user", "content": (
            f"Result: {info.get('action_result','')}. Reward: {step_reward:+.4f}. "
            f"Hint: {new_obs.get('hint','')}"
        )})

        obs        = new_obs
        step_count += 1

        # Force submit near step limit
        if max_steps - step_count <= 1 and not done:
            print("[INFO] Forcing submit at step limit", file=sys.stderr)
            try:
                r2   = env_step("submit")
                info = r2.get("info", {})
                rw2  = r2.get("reward", {})
                total_reward = rw2.get("cumulative", total_reward)
                obs  = r2.get("observation", obs)
                print(
                    f"[STEP] task={task_id} step={step_count+1} "
                    f"action=submit reward={rw2.get('value',0):.4f} "
                    f"cumulative_reward={total_reward:.4f} done=true "
                    f"completeness={obs.get('metrics',{}).get('completeness',0):.3f} "
                    f"validity={obs.get('metrics',{}).get('validity',0):.3f} "
                    f"accuracy={obs.get('metrics',{}).get('accuracy',0):.3f}",
                    flush=True
                )
            except Exception:
                pass
            done = True

    final_score = info.get("final_score", _grade_from_obs(obs))
    bugs_fixed  = info.get("bugs_fixed", {})
    n_fixed     = sum(1 for v in bugs_fixed.values() if v) if bugs_fixed else 0

    # ---- [END] block — plain text format ----
    print(
        f"[END] task={task_id} score={final_score:.4f} "
        f"steps={step_count} total_reward={total_reward:.4f} "
        f"bugs_fixed={n_fixed} success={str(final_score >= 0.7).lower()}",
        flush=True
    )

    return {
        "task_id":     task_id,
        "final_score": round(final_score, 4),
        "total_reward": round(total_reward, 4),
        "total_steps": step_count,
        "success":     final_score >= 0.7,
        "bugs_fixed":  bugs_fixed,
    }

def _grade_from_obs(obs: Dict) -> float:
    m = obs.get("metrics", {})
    raw = (m.get("completeness",0) + m.get("uniqueness",0) +
           m.get("validity",0)     + m.get("accuracy",0)) / 4
    # Clip to strictly open interval (0, 1) — 0.0 and 1.0 not allowed
    return round(min(0.999, max(0.001, raw)), 4)

# ---------------------------------------------------------------------------
# run_agent_episode — local episode runner used by train.py
# ---------------------------------------------------------------------------
def _init_training_llm_client(base_url: str, model_name: str, hf_token: str):
    """Lazily initialise an OpenAI-compatible client for training episodes."""
    global client
    if client is not None:
        return client
    if not base_url or not hf_token:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(base_url=base_url, api_key=hf_token)
        print(f"[train-llm] Client initialised: {model_name}", file=sys.stderr)
        return client
    except Exception as e:
        print(f"[train-llm] Client init failed: {e}", file=sys.stderr)
        return None


def run_agent_episode(
    env,
    task_id: str,
    noise: float = 0.0,
    episode: int = 0,
    base_url: str = "",
    model_name: str = "",
    hf_token: str = "",
) -> tuple:
    """
    Run one episode using a local DataPipelineEnv instance.
    Used by train.py for curriculum training.

    **Change 1**: Now calls llm_choose_action() at temperature=0.5 instead of
    random noise, falling back to rule-based when LLM is unavailable.

    **Change 2**: Records high-scoring episodes (score >= 0.95) as few-shot
    examples for self-improvement.

    Parameters
    ----------
    env : DataPipelineEnv  — already reset()'d environment
    task_id : str          — current task identifier
    noise : float          — exploration noise (0=greedy, 1=random)
    episode : int          — episode number for logging
    base_url, model_name, hf_token — LLM config (unused in fallback mode)
    base_url, model_name, hf_token — LLM config for llm_choose_action()

    Returns
    -------
    (score: float, steps: int)
    """
    import random as _rng
    from env.models import Action, ActionType

    # ── Change 1: Try to initialise LLM client for training ──
    _init_training_llm_client(base_url, model_name, hf_token)
    llm_available = client is not None

    obs_obj = env.reset()
    obs = obs_obj.model_dump() if hasattr(obs_obj, "model_dump") else obs_obj
    done = obs.get("done", False)
    max_steps = obs.get("max_steps", 40)
    step_count = 0
    inspect_count = 0
    last_actions: List[str] = []
    score = 0.0

    while not done and step_count < max_steps:
        # With probability `noise`, pick a random action; otherwise use rule-based
        if _rng.random() < noise:
    history: List[Dict] = []
    episode_actions: list[dict] = []   # for few-shot recording
    score = 0.0

    while not done and step_count < max_steps:
        # ── Change 1: Use LLM instead of random noise ──
        if llm_available and _rng.random() >= noise:
            # Call the real LLM with temperature=0.5 for exploration
            action_dict, raw, used_fallback = llm_choose_action(
                obs, history, inspect_count, last_actions)
        elif _rng.random() < noise and noise > 0.3:
            # High noise → small random exploration for diversity
            action_dict = _rng.choice([
                {"action_type": "inspect"},
                {"action_type": "drop_duplicates"},
                {"action_type": "validate"},
            ])
        else:
            action_dict = _rule_based_fallback(obs, inspect_count, last_actions)
            raw = json.dumps(action_dict)
            used_fallback = True
        else:
            # No LLM available or low noise → deterministic rule-based
            action_dict = _rule_based_fallback(obs, inspect_count, last_actions)
            raw = json.dumps(action_dict)
            used_fallback = True

        at = action_dict.get("action_type", "inspect")
        col = action_dict.get("column")
        val = action_dict.get("value")
        params = action_dict.get("parameters")

        if at == "inspect":
            inspect_count += 1

        # Track actions for repeat detection
        if at == "cast_column" and col:         last_actions.append(f"cast:{col}")
        elif at == "fill_nulls" and col:        last_actions.append(f"fill:{col}")
        elif at == "filter_outliers" and col:   last_actions.append(f"filter:{col}")
        elif at == "apply_business_rule" and val: last_actions.append(f"rule:{val[:10]}")
        else:                                    last_actions.append(at)

        # Record for few-shot memory
        episode_actions.append(action_dict)

        # Build conversation history for LLM context
        history.append({"role": "assistant", "content": raw if 'raw' in dir() else json.dumps(action_dict)})

        # Build Action object for local env
        try:
            action = Action(
                action_type=ActionType(at),
                column=col,
                value=val,
                parameters=params,
            )
            obs_obj = env.step(action)
            obs = obs_obj.model_dump() if hasattr(obs_obj, "model_dump") else obs_obj
            done = obs.get("done", False)
            step_count += 1
        except Exception as e:
            print(f"  [ep {episode}] step error: {e}", file=sys.stderr)
            step_count += 1

            # Add env response to history for LLM context
            history.append({"role": "user", "content": (
                f"Result: {obs.get('hint','')}. "
                f"Metrics: {json.dumps(obs.get('metrics',{}))}"
            )})
        except Exception as e:
            print(f"  [ep {episode}] step error: {e}", file=sys.stderr)
            step_count += 1
            history.append({"role": "user", "content": f"Error: {e}"})
            continue

        # Force submit near step limit
        if max_steps - step_count <= 1 and not done:
            try:
                submit_action = Action(action_type=ActionType.SUBMIT)
                obs_obj = env.step(submit_action)
                obs = obs_obj.model_dump() if hasattr(obs_obj, "model_dump") else obs_obj
                done = True
                step_count += 1
            except Exception:
                done = True

    # Extract final score from the last history entry
    if env.history:
        last_rec = env.history[-1]
        score = last_rec.cumulative_reward if hasattr(last_rec, "cumulative_reward") else 0.0
    else:
        score = _grade_from_obs(obs)

    # ── Change 2: Record best episodes for few-shot self-improvement ──
    if score >= 0.95 and episode_actions:
        record_best_episode(task_id, score, episode_actions)

    return score, step_count


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    global client

    # Initialise LLM client (works even if creds are missing — fallback handles it)
    try:
        if API_BASE_URL and HF_TOKEN:
            from openai import OpenAI
            client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
            print(f"[INFO] LLM client ready: {MODEL_NAME}", file=sys.stderr)
        else:
            print("[WARNING] API_BASE_URL or HF_TOKEN not set — using rule-based fallback only",
                  file=sys.stderr)
    except Exception as e:
        print(f"[WARNING] LLM client init failed: {e}", file=sys.stderr)

    print(f"[INFO] ENV_BASE_URL: {ENV_BASE_URL}", file=sys.stderr)

    # Check environment server is up
    try:
        _env_request("GET", "/health")
        print("[INFO] Environment server: OK", file=sys.stderr)
    except Exception as e:
        print(f"[ERROR] Env server unreachable at {ENV_BASE_URL}: {e}", file=sys.stderr)
        # Still try to run — evaluator controls ENV_BASE_URL
        # Don't sys.exit — let it attempt and fail gracefully per task

    # Run all 3 tasks
    all_results = []
    for task_id in TASKS:
        print(f"[INFO] Starting task: {task_id}", file=sys.stderr)
        try:
            result = run_task(task_id)
            all_results.append(result)
        except Exception as e:
            print(f"[ERROR] Task {task_id} failed: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            # Still emit [START] and [END] so evaluator can parse something
            print(f"[START] task={task_id} seed={SEED} max_steps=40", flush=True)
            print(f"[END] task={task_id} score=0.0 steps=0 total_reward=0.0 bugs_fixed=0 success=false",
                  flush=True)
            all_results.append({"task_id": task_id, "final_score": 0.0,
                                 "success": False, "total_steps": 0})

    # Final summary
    scores = [r.get("final_score", 0.0) for r in all_results]
    avg    = round(sum(scores) / len(scores), 4) if scores else 0.0

    print(f"[SUMMARY] model={MODEL_NAME} tasks={len(all_results)} avg_score={avg:.4f} "
          f"scores={','.join(f'{s:.4f}' for s in scores)}", flush=True)

    print(f"[INFO] Done. Average score: {avg}", file=sys.stderr)


if __name__ == "__main__":
    main()
