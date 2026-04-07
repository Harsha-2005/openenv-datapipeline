#!/usr/bin/env python3
"""
inference.py — Baseline inference script for OpenEnv Data Pipeline Debugger.

Uses the OpenAI client to run a model against all 3 tasks.
Reads credentials from environment variables:
  API_BASE_URL   — API endpoint for LLM
  MODEL_NAME     — model identifier
  HF_TOKEN       — HuggingFace API key
  ENV_BASE_URL   — environment server (default: http://localhost:7860)

Emits structured stdout logs in [START] / [STEP] / [END] format.
"""

from __future__ import annotations
import json, os, re, sys, time, traceback
from typing import Any, Dict, List, Optional
from openai import OpenAI
# from dotenv import load_dotenv

# load_dotenv()


# ---------------------------------------------------------------------------
# Configuration — all from environment variables
# ---------------------------------------------------------------------------
API_BASE_URL = os.environ.get("API_BASE_URL","https://router.huggingface.co/v1")
MODEL_NAME   = os.environ.get("MODEL_NAME","Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN     = os.environ.get("HF_TOKEN")
ENV_BASE_URL = os.environ.get("ENV_BASE_URL", "http://localhost:7860")
TASKS        = ["task_easy_schema_fix","task_medium_data_quality","task_hard_pipeline_orchestration"]
SEED         = 42

def validate_config():
    missing = [k for k,v in {"API_BASE_URL":API_BASE_URL,"MODEL_NAME":MODEL_NAME,"HF_TOKEN":HF_TOKEN}.items() if not v]
    if missing:
        print(f"[ERROR] Missing env vars: {missing}", file=sys.stderr)
        sys.exit(1)

# ---------------------------------------------------------------------------
# Environment HTTP client
# ---------------------------------------------------------------------------
import urllib.request, urllib.error

def _env_request(method, path, body=None):
    data = json.dumps(body).encode() if body else None
    req  = urllib.request.Request(ENV_BASE_URL+path, data=data, method=method,
                                   headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def env_reset(task_id, seed=SEED):
    return _env_request("POST", "/reset", {"task_id":task_id,"seed":seed})

def env_step(action_type, column=None, value=None, parameters=None):
    return _env_request("POST", "/step",
        {"action_type":action_type,"column":column,"value":value,"parameters":parameters})

# ---------------------------------------------------------------------------
# LLM client (created in main after validation)
# ---------------------------------------------------------------------------
client = None

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

RULES:
1. inspect ONCE only — after that, take fixing actions immediately
2. Hard task: reorder_stages first
3. cast_column for every col where actual_type != expected_type
4. drop_duplicates if duplicates exist
5. fill_nulls / drop_nulls for nulls
6. filter_outliers for negative/extreme values
7. apply_business_rule for constraint violations
8. validate then submit

Output ONLY the JSON object. Nothing else."""

VALID_ACTIONS = {
    "inspect","cast_column","drop_nulls","fill_nulls","drop_duplicates",
    "filter_outliers","rename_column","reorder_stages","apply_business_rule",
    "validate","submit"
}

def _extract_json(text):
    """5-strategy JSON extractor — handles all ways LLMs mess up JSON output."""
    if not text:
        return None
    text = text.strip()
    # 1: Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 2: Strip markdown fences
    for m in re.findall(r"```(?:json)?\s*([\s\S]*?)```", text):
        try:
            return json.loads(m.strip())
        except json.JSONDecodeError:
            pass
    # 3: First { } block
    m = re.search(r'\{[^{}]*\}', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    # 4: Outermost { } with nesting
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
    # 5: Regex for action_type keyword
    m = re.search(r'"action_type"\s*:\s*"([^"]+)"', text)
    if m:
        result = {"action_type": m.group(1)}
        cm = re.search(r'"column"\s*:\s*"([^"]+)"', text)
        vm = re.search(r'"value"\s*:\s*"([^"]+)"', text)
        if cm: result["column"] = cm.group(1)
        if vm: result["value"]  = vm.group(1)
        return result
    return None

def _rule_based_fallback(obs, inspect_count, last_actions):
    """Deterministic fallback when LLM output can't be parsed — always makes progress."""
    task_id     = obs.get("task_id","")
    schema_info = obs.get("schema_info",[])
    error_log   = obs.get("error_log",[])
    errors_str  = " ".join(error_log).lower()
    hint        = obs.get("hint","")

    # Hard task: fix stage order first (only if not already done)
    if task_id == "task_hard_pipeline_orchestration":
        already_reordered = "reorder_stages" in last_actions
        if not already_reordered and ("stage order" in errors_str or "wrong" in errors_str or "reorder" in hint.lower()):
            return {"action_type":"reorder_stages",
                    "parameters":{"stages":["ingest","validate","transform","enrich","load"]}}

    # Cast all mistyped columns
    for sf in schema_info:
        name   = sf.get("name","")   if isinstance(sf,dict) else getattr(sf,"name","")
        exp    = sf.get("expected_type","") if isinstance(sf,dict) else getattr(sf,"expected_type","")
        actual = sf.get("actual_type","")   if isinstance(sf,dict) else getattr(sf,"actual_type","")
        if exp and actual and exp != actual and f"cast:{name}" not in last_actions:
            return {"action_type":"cast_column","column":name,"value":exp}

    # Business rules
    if "discount" in errors_str and "rule:discount" not in str(last_actions):
        return {"action_type":"apply_business_rule","value":"discount_lte_1"}
    if "fraud_score" in errors_str and "rule:fraud" not in str(last_actions):
        return {"action_type":"apply_business_rule","value":"fraud_score_lte_1"}
    if "currency" in errors_str and "rule:currency" not in str(last_actions):
        return {"action_type":"apply_business_rule","value":"currency_3char"}
    if "country_code" in errors_str and "rule:country" not in str(last_actions):
        return {"action_type":"apply_business_rule","value":"country_2char"}

    # Duplicates
    if "duplicate" in errors_str and "drop_duplicates" not in last_actions:
        return {"action_type":"drop_duplicates"}

    # Outliers / negatives
    if "negative" in errors_str or "outlier" in errors_str:
        for col,mn,mx in [("quantity","0","9999"),("unit_price","0","99999"),("amount","0","999999")]:
            key = f"filter:{col}"
            if col in errors_str and key not in last_actions:
                return {"action_type":"filter_outliers","column":col,"value":f"{mn},{mx}"}

    # Nulls
    NULL_FILLS = {
        "task_easy_schema_fix":            [("age","0"),("revenue","0.0"),("email","unknown@example.com")],
        "task_medium_data_quality":         [("quantity","1"),("unit_price","0.0"),("region","UNKNOWN"),("order_date","2024-01-01")],
        "task_hard_pipeline_orchestration": [("merchant","UNKNOWN"),("fraud_score","0.0"),("category","UNKNOWN"),("country_code","US"),("currency","USD")],
    }
    if "null" in errors_str:
        for col,val in NULL_FILLS.get(task_id,[]):
            key = f"fill:{col}"
            if key not in last_actions:
                return {"action_type":"fill_nulls","column":col,"value":val}

    # Validate then submit
    if "validate" not in last_actions[-3:]:
        return {"action_type":"validate"}
    return {"action_type":"submit"}

def llm_choose_action(obs, history, inspect_count, last_actions):
    """Call LLM, parse response with 5-strategy extractor, fall back to rule-based if needed."""
    step = obs.get("step_count",0)

    # Build schema summary string
    schema_lines = []
    for sf in obs.get("schema_info",[]):
        name   = sf.get("name","")   if isinstance(sf,dict) else getattr(sf,"name","")
        exp    = sf.get("expected_type","") if isinstance(sf,dict) else getattr(sf,"expected_type","")
        actual = sf.get("actual_type","")   if isinstance(sf,dict) else getattr(sf,"actual_type","")
        match  = "OK" if exp==actual else f"MISMATCH (should be {exp})"
        schema_lines.append(f"  {name}: {actual} → {match}")

    user_msg = f"""Step {step}/{obs.get('max_steps')} | Task: {obs.get('task_id')}
Hint: {obs.get('hint','')}
Inspected {inspect_count} time(s). Recent actions: {last_actions[-5:]}

Schema types:
{chr(10).join(schema_lines)}

Metrics: completeness={obs.get('metrics',{}).get('completeness',0):.3f}  uniqueness={obs.get('metrics',{}).get('uniqueness',0):.3f}  validity={obs.get('metrics',{}).get('validity',0):.3f}  accuracy={obs.get('metrics',{}).get('accuracy',0):.3f}

Recent errors:
{chr(10).join(obs.get('error_log',[])[-4:])}

Data sample[0]: {json.dumps(obs.get('data_sample',[{}])[0] if obs.get('data_sample') else {})}

Output ONLY the JSON action:"""

    messages = [{"role":"system","content":SYSTEM_PROMPT}] + history[-6:] + [{"role":"user","content":user_msg}]

    raw = ""
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME, messages=messages, max_tokens=200, temperature=0.0)
        raw = resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"[WARNING] LLM call failed: {e}", file=sys.stderr)

    print(f"[DEBUG] LLM raw: {raw[:300]!r}", file=sys.stderr)

    action = _extract_json(raw)
    if action and action.get("action_type") in VALID_ACTIONS:
        print(f"[DEBUG] LLM parsed OK: {action}", file=sys.stderr)
        return action, raw, False

    print(f"[WARNING] LLM parse failed → using rule-based fallback", file=sys.stderr)
    fallback = _rule_based_fallback(obs, inspect_count, last_actions)
    print(f"[DEBUG] Fallback: {fallback}", file=sys.stderr)
    return fallback, raw, True

# ---------------------------------------------------------------------------
# Episode runner
# ---------------------------------------------------------------------------
def run_task(task_id):
    obs           = env_reset(task_id, seed=SEED)
    done          = obs.get("done",False)
    step_count    = 0
    history       = []
    total_reward  = 0.0
    inspect_count = 0
    last_actions  = []   # stores action keys like "cast:customer_id", "fill:age" etc
    info          = {}
    max_steps     = obs.get("max_steps",40)

    print(json.dumps({
        "type":"[START]","task_id":task_id,"seed":SEED,
        "max_steps":max_steps,"initial_metrics":obs.get("metrics"),
    }), flush=True)

    while not done and step_count < max_steps:
        t0 = time.time()

        action_dict, raw, used_fallback = llm_choose_action(obs, history, inspect_count, last_actions)

        at     = action_dict.get("action_type","inspect")
        col    = action_dict.get("column")
        val    = action_dict.get("value")
        params = action_dict.get("parameters")

        if at == "inspect":
            inspect_count += 1

        # Record action with key for fallback dedup tracking
        if at == "cast_column" and col:
            last_actions.append(f"cast:{col}")
        elif at == "fill_nulls" and col:
            last_actions.append(f"fill:{col}")
        elif at == "filter_outliers" and col:
            last_actions.append(f"filter:{col}")
        elif at == "apply_business_rule" and val:
            last_actions.append(f"rule:{val[:10]}")
        else:
            last_actions.append(at)

        try:
            result = env_step(at, col, val, params)
        except Exception as e:
            print(f"[WARNING] env_step error: {e}", file=sys.stderr)
            result = {"observation":obs,"reward":{"value":-0.05,"cumulative":total_reward,
                      "components":{},"explanation":str(e)},"done":False,"info":{"error":str(e)}}

        new_obs     = result.get("observation", obs)
        reward_info = result.get("reward", {})
        done        = result.get("done", False)
        info        = result.get("info", {})
        step_reward  = reward_info.get("value", 0.0)
        total_reward = reward_info.get("cumulative", total_reward+step_reward)
        latency_ms   = round((time.time()-t0)*1000, 1)

        print(json.dumps({
            "type":"[STEP]","task_id":task_id,"step":step_count+1,
            "action":action_dict,"reward":step_reward,
            "cumulative_reward":total_reward,"done":done,
            "metrics":new_obs.get("metrics",{}),"action_result":info.get("action_result",""),
            "latency_ms":latency_ms,"used_fallback":used_fallback,
        }), flush=True)

        history.append({"role":"assistant","content": raw or json.dumps(action_dict)})
        history.append({"role":"user","content":(
            f"Result: {info.get('action_result','')}. Reward: {step_reward:+.4f}. "
            f"Hint: {new_obs.get('hint','')}"
        )})

        obs        = new_obs
        step_count += 1

        # Force submit near step limit
        if max_steps - step_count <= 1 and not done:
            print("[INFO] Forcing submit at step limit", file=sys.stderr)
            try:
                r2 = env_step("submit")
                info = r2.get("info",{})
                rw2  = r2.get("reward",{})
                total_reward = rw2.get("cumulative", total_reward)
                print(json.dumps({
                    "type":"[STEP]","task_id":task_id,"step":step_count+1,
                    "action":{"action_type":"submit"},"reward":rw2.get("value",0),
                    "cumulative_reward":total_reward,"done":True,
                    "metrics":r2.get("observation",obs).get("metrics",{}),"action_result":"forced submit",
                    "latency_ms":0,"used_fallback":True,
                }), flush=True)
                obs = r2.get("observation",obs)
            except Exception:
                pass
            done = True

    final_score = info.get("final_score", grade_from_obs(obs))
    end_log = {
        "type":"[END]","task_id":task_id,"total_steps":step_count,
        "final_score":round(final_score,4),"total_reward":round(total_reward,4),
        "final_metrics":obs.get("metrics",{}),"bugs_fixed":info.get("bugs_fixed",{}),
        "success":final_score >= 0.7,
    }
    print(json.dumps(end_log), flush=True)
    return end_log

def grade_from_obs(obs):
    m = obs.get("metrics",{})
    return round((m.get("completeness",0)+m.get("uniqueness",0)+
                  m.get("validity",0)+m.get("accuracy",0))/4, 4)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    validate_config()
    global client
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

    print(f"[INFO] Model: {MODEL_NAME}", file=sys.stderr)
    print(f"[INFO] Env:   {ENV_BASE_URL}", file=sys.stderr)

    try:
        _env_request("GET","/health")
        print("[INFO] Environment server: OK", file=sys.stderr)
    except Exception as e:
        print(f"[ERROR] Env server unreachable: {e}\nRun: python app.py", file=sys.stderr)
        sys.exit(1)

    all_results = []
    for task_id in TASKS:
        print(f"\n{'='*60}", flush=True)
        print(f"Running task: {task_id}", flush=True)
        print(f"{'='*60}", flush=True)
        try:
            all_results.append(run_task(task_id))
        except Exception as e:
            print(f"[ERROR] {task_id}: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            all_results.append({"task_id":task_id,"final_score":0.0,"success":False,"total_steps":0})

    # Flush any buffered output before printing summary
    sys.stdout.flush()

    print("", flush=True)
    print("="*60, flush=True)
    print("BASELINE SUMMARY", flush=True)
    print("="*60, flush=True)
    scores = []
    for r in all_results:
        sc = r.get("final_score", 0.0)
        scores.append(sc)
        print(json.dumps({
            "task_id":     r.get("task_id"),
            "final_score": sc,
            "success":     r.get("success", sc >= 0.7),
            "total_steps": r.get("total_steps", 0),
        }), flush=True)

    avg = round(sum(scores) / len(scores), 4) if scores else 0.0
    print(json.dumps({
        "type":          "SUMMARY",
        "model":         MODEL_NAME,
        "tasks_run":     len(all_results),
        "average_score": avg,
        "scores":        dict(zip(TASKS, scores)),
    }), flush=True)

if __name__ == "__main__":
    main()