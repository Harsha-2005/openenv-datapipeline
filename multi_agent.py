"""
multi_agent.py — Multi-Agent Pipeline Debugging Environment
Theme 1: Multi-Agent Interactions (cooperation)
Theme 3.1 Sub-theme: Scaler AI Labs Multi-App RL for Enterprise Workflows

Implements a cooperative multi-agent setup where:
  - Agent INSPECTOR: analyzes the pipeline, identifies issues, reports findings
  - Agent FIXER:     receives findings, applies fixes in the correct order
  - Agent VALIDATOR: checks fixes, runs validation, decides when to submit

The agents communicate through a shared message bus.
This tests: coordination, role specialization, sequential handoffs.
"""

from __future__ import annotations
import json
import os
import time
import urllib.request
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# ── Agent roles ───────────────────────────────────────────────────────────────

class AgentRole(str, Enum):
    INSPECTOR  = "inspector"   # finds bugs, reports to FIXER
    FIXER      = "fixer"       # applies fixes based on INSPECTOR report
    VALIDATOR  = "validator"   # validates fixes, decides when to submit


# ── Message bus ──────────────────────────────────────────────────────────────

@dataclass
class Message:
    sender:    AgentRole
    receiver:  AgentRole
    content:   Dict[str, Any]
    timestamp: float = field(default_factory=time.time)

class MessageBus:
    """Shared communication channel for all agents."""
    def __init__(self):
        self._inbox: Dict[AgentRole, List[Message]] = {
            role: [] for role in AgentRole
        }

    def send(self, sender: AgentRole, receiver: AgentRole,
             content: Dict[str, Any]):
        msg = Message(sender=sender, receiver=receiver, content=content)
        self._inbox[receiver].append(msg)

    def receive(self, role: AgentRole) -> List[Message]:
        msgs = self._inbox[role].copy()
        self._inbox[role].clear()
        return msgs

    def broadcast(self, sender: AgentRole, content: Dict[str, Any]):
        for role in AgentRole:
            if role != sender:
                self.send(sender, role, content)


# ── Environment client ────────────────────────────────────────────────────────

ENV_BASE_URL = os.environ.get("ENV_BASE_URL", "http://localhost:7860")

def _env_req(method: str, path: str, body: Optional[Dict] = None) -> Dict:
    url  = ENV_BASE_URL + path
    data = json.dumps(body).encode() if body is not None else None
    req  = urllib.request.Request(
        url, data=data, method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


# ── Specialist agents ─────────────────────────────────────────────────────────

class InspectorAgent:
    """
    Role: Analyze the pipeline state and produce a structured diagnosis.
    Does NOT apply any fixes — only reports.
    Sends findings to FIXER.
    """
    def __init__(self, bus: MessageBus):
        self.bus  = bus
        self.role = AgentRole.INSPECTOR

    def run(self, observation: Dict) -> Dict:
        """Inspect pipeline and send diagnosis to FIXER."""
        schema_info = observation.get("schema_info", [])
        error_log   = observation.get("error_log", [])
        metrics     = observation.get("metrics", {})

        # Find type mismatches
        type_issues = []
        for sf in schema_info:
            name   = sf.get("name","")   if isinstance(sf,dict) else getattr(sf,"name","")
            exp    = sf.get("expected_type","") if isinstance(sf,dict) else getattr(sf,"expected_type","")
            actual = sf.get("actual_type","")   if isinstance(sf,dict) else getattr(sf,"actual_type","")
            if exp and actual and exp != actual:
                type_issues.append({"column": name, "expected": exp, "actual": actual})

        # Parse error log for issue types
        errors_str = " ".join(error_log).lower()
        diagnosis  = {
            "type_issues":        type_issues,
            "has_duplicates":     "duplicate" in errors_str,
            "has_nulls":          "null" in errors_str,
            "has_stage_error":    "stage order" in errors_str or "wrong" in errors_str,
            "has_neg_values":     "negative" in errors_str,
            "has_rule_violations":(
                "discount" in errors_str or "fraud" in errors_str or
                "currency" in errors_str or "country" in errors_str
            ),
            "metrics":            metrics,
            "hint":               observation.get("hint", ""),
            "task_id":            observation.get("task_id", ""),
        }

        # Send diagnosis to FIXER
        self.bus.send(AgentRole.INSPECTOR, AgentRole.FIXER, {
            "type":      "diagnosis",
            "diagnosis": diagnosis,
        })

        print(f"  [INSPECTOR] Found {len(type_issues)} type issues, "
              f"duplicates={diagnosis['has_duplicates']}, "
              f"nulls={diagnosis['has_nulls']}, "
              f"stage_error={diagnosis['has_stage_error']}")

        return {"action_type": "inspect"}  # inspector's own action


class FixerAgent:
    """
    Role: Receive diagnosis from INSPECTOR and apply fixes in correct order.
    Reports completed fixes to VALIDATOR.
    """
    def __init__(self, bus: MessageBus):
        self.bus          = bus
        self.role         = AgentRole.FIXER
        self.fix_queue:   List[Dict] = []
        self.fixes_done:  List[str]  = []

    def _build_fix_queue(self, diagnosis: Dict) -> List[Dict]:
        """Convert diagnosis into ordered fix actions."""
        queue = []
        task_id = diagnosis.get("task_id", "")

        # Priority 1: Stage order (must be first)
        if diagnosis["has_stage_error"]:
            queue.append({
                "action_type": "reorder_stages",
                "parameters":  {"stages": ["ingest","validate","transform","enrich","load"]},
            })

        # Priority 2: Type casts
        for issue in diagnosis["type_issues"]:
            queue.append({
                "action_type": "cast_column",
                "column":      issue["column"],
                "value":       issue["expected"],
            })

        # Priority 3: Duplicates
        if diagnosis["has_duplicates"]:
            queue.append({"action_type": "drop_duplicates"})

        # Priority 4: Business rules
        if diagnosis["has_rule_violations"]:
            errors = " ".join(str(diagnosis.get("metrics",""))).lower()
            for rule in ["discount_lte_1","fraud_score_lte_1","currency_3char","country_2char"]:
                queue.append({"action_type": "apply_business_rule", "value": rule})

        # Priority 5: Nulls
        if diagnosis["has_nulls"]:
            null_fills = {
                "task_easy_schema_fix":            [("age","0"),("revenue","0.0")],
                "task_medium_data_quality":         [("quantity","1"),("unit_price","0.0"),
                                                    ("region","UNKNOWN"),("order_date","2024-01-01")],
                "task_hard_pipeline_orchestration": [("merchant","UNKNOWN"),
                                                    ("fraud_score","0.0"),("category","UNKNOWN")],
            }
            for col, val in null_fills.get(task_id, []):
                queue.append({"action_type": "fill_nulls", "column": col, "value": val})

        # Priority 6: Negative values
        if diagnosis["has_neg_values"]:
            queue.append({"action_type": "filter_outliers",
                          "column": "amount", "value": "0,999999"})

        return queue

    def run(self) -> Optional[Dict]:
        """Check mailbox and return next fix action."""
        messages = self.bus.receive(AgentRole.FIXER)

        # Process any new diagnoses
        for msg in messages:
            if msg.content.get("type") == "diagnosis":
                diagnosis   = msg.content["diagnosis"]
                self.fix_queue = self._build_fix_queue(diagnosis)
                print(f"  [FIXER] Received diagnosis. "
                      f"Fix queue: {len(self.fix_queue)} actions planned.")

        # Execute next fix from queue
        if self.fix_queue:
            action = self.fix_queue.pop(0)
            self.fixes_done.append(action["action_type"])
            print(f"  [FIXER] Applying: {action['action_type']} "
                  f"{action.get('column','') or action.get('value','')}")

            # Notify VALIDATOR of progress
            if not self.fix_queue:
                self.bus.send(AgentRole.FIXER, AgentRole.VALIDATOR, {
                    "type":       "fixes_complete",
                    "fixes_done": self.fixes_done,
                })
                print(f"  [FIXER] All fixes applied. Notifying VALIDATOR.")

            return action
        return None


class ValidatorAgent:
    """
    Role: Check current metrics after fixes and decide when to submit.
    Sends re-inspect requests to INSPECTOR if quality is insufficient.
    """
    def __init__(self, bus: MessageBus, score_threshold: float = 0.75):
        self.bus             = bus
        self.role            = AgentRole.VALIDATOR
        self.score_threshold = score_threshold
        self.fixes_received  = False
        self.validated       = False

    def run(self, observation: Dict) -> Optional[Dict]:
        """Check mailbox and decide next action."""
        messages = self.bus.receive(AgentRole.VALIDATOR)

        for msg in messages:
            if msg.content.get("type") == "fixes_complete":
                self.fixes_received = True
                print(f"  [VALIDATOR] Received completion signal. "
                      f"Running validation.")

        if self.fixes_received and not self.validated:
            metrics     = observation.get("metrics", {})
            completeness = metrics.get("completeness", 0)
            validity     = metrics.get("validity", 0)
            accuracy     = metrics.get("accuracy", 0)
            avg_quality  = (completeness + validity + accuracy) / 3

            print(f"  [VALIDATOR] Quality check: "
                  f"completeness={completeness:.3f}, "
                  f"validity={validity:.3f}, "
                  f"accuracy={accuracy:.3f}, "
                  f"avg={avg_quality:.3f}")

            if avg_quality >= self.score_threshold:
                self.validated = True
                print(f"  [VALIDATOR] Quality PASSED (>={self.score_threshold}). Submitting!")
                return {"action_type": "submit"}
            else:
                # Quality insufficient — ask inspector to re-check
                self.fixes_received = False
                self.bus.send(AgentRole.VALIDATOR, AgentRole.INSPECTOR, {
                    "type":    "recheck_needed",
                    "reason":  f"avg_quality={avg_quality:.3f} below threshold",
                    "metrics": metrics,
                })
                print(f"  [VALIDATOR] Quality insufficient. Requesting re-inspection.")
                return {"action_type": "validate"}

        return None


# ── Multi-agent orchestrator ──────────────────────────────────────────────────

class MultiAgentOrchestrator:
    """
    Coordinates INSPECTOR → FIXER → VALIDATOR pipeline.

    Execution order each step:
      1. INSPECTOR checks state, sends diagnosis to FIXER
      2. FIXER applies one fix from its queue
      3. VALIDATOR checks if done, submits if quality is good
    """

    def __init__(self, score_threshold: float = 0.75):
        self.bus       = MessageBus()
        self.inspector = InspectorAgent(self.bus)
        self.fixer     = FixerAgent(self.bus)
        self.validator = ValidatorAgent(self.bus, score_threshold)
        self.step_log: List[Dict] = []

    def run_episode(self, task_id: str, seed: int = 42,
                    verbose: bool = True) -> Dict:
        """Run a full multi-agent episode."""

        obs          = _env_req("POST", "/reset", {"task_id": task_id, "seed": seed})
        done         = False
        step_count   = 0
        total_reward = 0.0
        max_steps    = obs.get("max_steps", 40)
        info         = {}

        if verbose:
            print(f"\n{'='*60}")
            print(f"Multi-Agent Episode: {task_id}")
            print(f"{'='*60}")

        # Inspector always goes first
        inspect_action = self.inspector.run(obs)
        result = _env_req("POST", "/step", {"action_type": "inspect"})
        obs    = result.get("observation", obs)
        step_count += 1

        while not done and step_count < max_steps:
            action = None

            # Try VALIDATOR first (it has submit authority)
            action = self.validator.run(obs)

            # If VALIDATOR has nothing, try FIXER
            if action is None:
                action = self.fixer.run()

            # If FIXER queue is empty and no new diagnosis, re-inspect
            if action is None:
                if verbose:
                    print(f"  [ORCHESTRATOR] Step {step_count}: Re-inspecting...")
                inspect_action = self.inspector.run(obs)
                action = {"action_type": "inspect"}

            if verbose:
                print(f"  [ORCHESTRATOR] Step {step_count}: "
                      f"Executing {action.get('action_type')}")

            try:
                result = _env_req("POST", "/step", action)
                obs    = result.get("observation", obs)
                done   = result.get("done", False)
                info   = result.get("info", {})
                rw     = result.get("reward", {})
                sr     = rw.get("value", 0.0)
                total_reward = rw.get("cumulative", total_reward + sr)
                step_count  += 1

                self.step_log.append({
                    "step":   step_count,
                    "action": action,
                    "reward": sr,
                    "done":   done,
                })
            except Exception as e:
                if verbose:
                    print(f"  [ERROR] Step failed: {e}")
                break

        final_score = info.get("final_score", 0.5)
        bugs_fixed  = info.get("bugs_fixed", {})
        n_fixed     = sum(1 for v in bugs_fixed.values() if v) if bugs_fixed else 0

        if verbose:
            print(f"\n  Final score: {final_score:.4f}")
            print(f"  Total steps: {step_count}")
            print(f"  Bugs fixed:  {n_fixed}/{len(bugs_fixed) if bugs_fixed else '?'}")
            print(f"  Total reward: {total_reward:.4f}")

        return {
            "task_id":     task_id,
            "final_score": final_score,
            "total_steps": step_count,
            "total_reward":total_reward,
            "bugs_fixed":  n_fixed,
            "success":     final_score >= 0.7,
        }


# ── Demo ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Multi-Agent Pipeline Debugger Demo")
    print("Roles: INSPECTOR → FIXER → VALIDATOR")
    print()

    orchestrator = MultiAgentOrchestrator(score_threshold=0.75)

    tasks = [
        "task_easy_schema_fix",
        "task_medium_data_quality",
        "task_hard_pipeline_orchestration",
    ]

    results = []
    for task in tasks:
        try:
            result = orchestrator.run_episode(task, seed=42, verbose=True)
            results.append(result)
        except Exception as e:
            print(f"[ERROR] {task}: {e}")
            results.append({"task_id": task, "final_score": 0.0, "success": False})

    print("\n" + "="*60)
    print("MULTI-AGENT SUMMARY")
    print("="*60)
    for r in results:
        status = "✅" if r.get("success") else "❌"
        print(f"  {status} {r['task_id']:45s} score={r.get('final_score',0):.4f}")

    avg = sum(r.get("final_score",0) for r in results) / len(results)
    print(f"\n  Average score: {avg:.4f}")
