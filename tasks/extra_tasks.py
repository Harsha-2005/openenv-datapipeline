"""
Extra tasks — Very Hard and Expert difficulty.
Task 4: Streaming Pipeline Debug
Task 5: Multi-Source Join Repair
"""

from __future__ import annotations
import copy
import random
from typing import Any, Dict, List
from env.models import SchemaField, PipelineMetrics, PipelineState
from tasks.definitions import _make_schema, _compute_metrics


# ---------------------------------------------------------------------------
# TASK 4 — Very Hard: Streaming Pipeline Debug
# ---------------------------------------------------------------------------

VERYHARD_SCHEMA = _make_schema(
    ("event_id",      "int",   "str",   False),
    ("user_id",       "int",   "str",   False),
    ("event_type",    "str",   "str",   True),
    ("event_ts",      "str",   "str",   False),
    ("session_id",    "str",   "str",   True),
    ("value",         "float", "str",   True),
    ("latency_ms",    "int",   "str",   True),
    ("region",        "str",   "str",   True),
    ("is_test",       "bool",  "str",   True),
    ("processed_ts",  "str",   "str",   True),
)

VERYHARD_TARGET = {
    "completeness": 0.93,
    "uniqueness":   0.97,
    "validity":     0.92,
    "accuracy":     0.93,
}

VERYHARD_RULES = [
    lambda r: r.get("value") is None or (isinstance(r.get("value"), (int,float)) and r["value"] >= 0),
    lambda r: r.get("latency_ms") is None or (isinstance(r.get("latency_ms"), (int,float)) and 0 <= r["latency_ms"] <= 30000),
    lambda r: r.get("event_type") is None or r.get("event_type") in ("click","view","purchase","login","logout","error","UNKNOWN"),
]

VERYHARD_BUGS = {
    "cast_event_id_to_int":      False,
    "cast_user_id_to_int":       False,
    "cast_value_to_float":       False,
    "cast_latency_ms_to_int":    False,
    "drop_duplicates":           False,
    "fill_nulls_event_type":     False,
    "fill_nulls_session_id":     False,
    "fill_nulls_region":         False,
    "filter_negative_value":     False,
    "filter_extreme_latency":    False,
    "fix_invalid_event_type":    False,
    "fix_stage_order":           False,
    "validate_final":            False,
}

VERYHARD_WRONG_STAGES = ["ingest", "enrich", "validate", "transform", "load"]

def _generate_veryhard_data(seed: int = 42) -> List[Dict[str, Any]]:
    rng = random.Random(seed)
    event_types = ["click","view","purchase","login","logout","error"]
    regions     = ["US","EU","APAC","LATAM","MEA"]
    rows = []
    for i in range(150):
        rows.append({
            "event_id":     str(50000 + i),
            "user_id":      str(rng.randint(1, 2000)),
            "event_type":   rng.choice(event_types),
            "event_ts":     f"2024-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}T{rng.randint(0,23):02d}:{rng.randint(0,59):02d}:{rng.randint(0,59):02d}Z",
            "session_id":   f"sess_{rng.randint(10000,99999)}",
            "value":        str(round(rng.uniform(0.0, 500.0), 2)),
            "latency_ms":   str(rng.randint(1, 5000)),
            "region":       rng.choice(regions),
            "is_test":      str(rng.random() < 0.1).lower(),
            "processed_ts": f"2024-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}T{rng.randint(0,23):02d}:{rng.randint(0,59):02d}:{rng.randint(0,59):02d}Z",
        })

    # Bug 1: Duplicates (10 rows)
    for _ in range(10):
        rows.append(copy.deepcopy(rng.choice(rows[:100])))

    # Bug 2: Nulls (~15%)
    null_targets = ["event_type","session_id","region","value","latency_ms"]
    for i in rng.sample(range(150), 22):
        rows[i][rng.choice(null_targets)] = None

    # Bug 3: Invalid event types
    for i in [5, 14, 33, 67, 89]:
        rows[i]["event_type"] = rng.choice(["CLICK","VIEW","UNKNOWN_TYPE","bad_event","null_type"])

    # Bug 4: Negative values
    for i in [8, 21, 45]:
        rows[i]["value"] = str(-abs(float(rows[i]["value"] or "10")))

    # Bug 5: Extreme latency
    for i in [12, 34, 78]:
        rows[i]["latency_ms"] = str(rng.randint(50000, 999999))

    rng.shuffle(rows)
    return rows

def build_veryhard_task(seed: int = 42) -> PipelineState:
    data    = _generate_veryhard_data(seed)
    schema  = copy.deepcopy(VERYHARD_SCHEMA)
    metrics = _compute_metrics(data, schema, VERYHARD_RULES)
    return PipelineState(
        task_id        = "task_veryhard_streaming_pipeline",
        step_count     = 0,
        max_steps      = 50,
        pipeline_stage = "ingest",
        data           = data,
        schema_info    = schema,
        error_log      = [
            "CRITICAL: Stage order WRONG: [ingest,enrich,validate,transform,load]",
            "ERROR: event_id/user_id/value/latency_ms all arrive as strings",
            "ERROR: 10 duplicate events detected",
            "ERROR: 22 null values across event_type/session_id/region",
            "ERROR: 5 invalid event_type values (not in allowed set)",
            "ERROR: 3 negative values violate value>=0 rule",
            "ERROR: 3 extreme latency values >30000ms",
            "SLA BREACH: estimated latency 450ms > 200ms threshold",
        ],
        metrics        = metrics,
        cumulative_reward = 0.0,
        done           = False,
        applied_actions= [],
        bugs_fixed     = copy.deepcopy(VERYHARD_BUGS),
        target_metrics = VERYHARD_TARGET,
        stage_order    = VERYHARD_WRONG_STAGES.copy(),
    )


# ---------------------------------------------------------------------------
# TASK 5 — Expert: Multi-Source Join Repair
# ---------------------------------------------------------------------------

EXPERT_SCHEMA = _make_schema(
    ("customer_id",   "int",   "str",   False),
    ("order_id",      "int",   "str",   False),
    ("product_sku",   "str",   "str",   False),
    ("quantity",      "int",   "str",   True),
    ("unit_price",    "float", "str",   True),
    ("customer_name", "str",   "str",   True),
    ("email",         "str",   "str",   True),
    ("product_name",  "str",   "str",   True),
    ("category",      "str",   "str",   True),
    ("joined_total",  "float", "str",   True),
    ("discount",      "float", "str",   True),
    ("tax_rate",      "float", "str",   True),
)

EXPERT_TARGET = {
    "completeness": 0.94,
    "uniqueness":   0.98,
    "validity":     0.93,
    "accuracy":     0.94,
}

EXPERT_RULES = [
    lambda r: r.get("quantity") is None or (isinstance(r.get("quantity"),(int,float)) and r["quantity"] > 0),
    lambda r: r.get("unit_price") is None or (isinstance(r.get("unit_price"),(int,float)) and r["unit_price"] > 0),
    lambda r: r.get("discount") is None or (isinstance(r.get("discount"),(int,float)) and 0 <= r["discount"] <= 1),
    lambda r: r.get("tax_rate") is None or (isinstance(r.get("tax_rate"),(int,float)) and 0 <= r["tax_rate"] <= 0.5),
]

EXPERT_BUGS = {
    "fix_stage_order":          False,
    "cast_customer_id_to_int":  False,
    "cast_order_id_to_int":     False,
    "cast_quantity_to_int":     False,
    "cast_unit_price_to_float": False,
    "cast_joined_total_float":  False,
    "cast_discount_to_float":   False,
    "cast_tax_rate_to_float":   False,
    "drop_duplicates":          False,
    "fill_nulls_customer_name": False,
    "fill_nulls_product_name":  False,
    "fill_nulls_category":      False,
    "filter_negative_qty":      False,
    "filter_negative_price":    False,
    "fix_discount_rule":        False,
    "fix_tax_rate_rule":        False,
    "validate_final":           False,
}

EXPERT_WRONG_STAGES = ["transform", "ingest", "validate", "load", "enrich"]

def _generate_expert_data(seed: int = 42) -> List[Dict[str, Any]]:
    rng = random.Random(seed)
    categories = ["Electronics","Clothing","Food","Books","Home","Sports"]
    rows = []
    for i in range(200):
        qty   = rng.randint(1, 50)
        price = round(rng.uniform(5.0, 1000.0), 2)
        disc  = round(rng.uniform(0.0, 0.35), 3)
        tax   = round(rng.uniform(0.05, 0.20), 3)
        total = round(qty * price * (1 - disc) * (1 + tax), 2)
        rows.append({
            "customer_id":   str(rng.randint(1000, 9999)),
            "order_id":      str(200000 + i),
            "product_sku":   f"SKU-{rng.randint(1000,9999)}",
            "quantity":      str(qty),
            "unit_price":    str(price),
            "customer_name": f"Customer_{rng.randint(1,500)}",
            "email":         f"user{rng.randint(1,500)}@domain.com",
            "product_name":  f"Product_{rng.randint(1,200)}",
            "category":      rng.choice(categories),
            "joined_total":  str(total),
            "discount":      str(disc),
            "tax_rate":      str(tax),
        })

    # Bug 1: Duplicates (12 rows)
    for _ in range(12):
        rows.append(copy.deepcopy(rng.choice(rows[:150])))

    # Bug 2: Nulls (~12%)
    null_targets = ["customer_name","product_name","category","email"]
    for i in rng.sample(range(200), 24):
        rows[i][rng.choice(null_targets)] = None

    # Bug 3: Negative quantities
    for i in [4, 19, 38, 77]:
        rows[i]["quantity"] = str(-abs(int(rows[i]["quantity"] or "1")))

    # Bug 4: Negative prices
    for i in [9, 27, 55]:
        rows[i]["unit_price"] = str(-abs(float(rows[i]["unit_price"] or "10")))

    # Bug 5: Invalid discounts
    for i in [13, 31, 62, 93]:
        rows[i]["discount"] = str(round(rng.uniform(1.1, 2.5), 3))

    # Bug 6: Invalid tax rates
    for i in [7, 44, 81]:
        rows[i]["tax_rate"] = str(round(rng.uniform(0.6, 1.2), 3))

    rng.shuffle(rows)
    return rows

def build_expert_task(seed: int = 42) -> PipelineState:
    data    = _generate_expert_data(seed)
    schema  = copy.deepcopy(EXPERT_SCHEMA)
    metrics = _compute_metrics(data, schema, EXPERT_RULES)
    return PipelineState(
        task_id        = "task_expert_multi_source_join",
        step_count     = 0,
        max_steps      = 60,
        pipeline_stage = "ingest",
        data           = data,
        schema_info    = schema,
        error_log      = [
            "CRITICAL: Stage order WRONG: [transform,ingest,validate,load,enrich]",
            "ERROR: 8 columns arrive as strings — must cast to correct types",
            "ERROR: 12 duplicate rows detected from multi-source merge",
            "ERROR: 24 null values across customer_name/product_name/category",
            "ERROR: 4 negative quantities violate qty>0 rule",
            "ERROR: 3 negative unit_prices violate price>0 rule",
            "ERROR: 4 discounts > 1.0 violate 0<=discount<=1 rule",
            "ERROR: 3 tax_rates > 0.5 violate 0<=tax_rate<=0.5 rule",
            "SLA BREACH: 620ms > 150ms threshold — 17 bugs remaining",
        ],
        metrics        = metrics,
        cumulative_reward = 0.0,
        done           = False,
        applied_actions= [],
        bugs_fixed     = copy.deepcopy(EXPERT_BUGS),
        target_metrics = EXPERT_TARGET,
        stage_order    = EXPERT_WRONG_STAGES.copy(),
    )


# ---------------------------------------------------------------------------
# Extra task info and builders
# ---------------------------------------------------------------------------

EXTRA_TASK_INFO = [
    {
        "task_id":    "task_veryhard_streaming_pipeline",
        "name":       "Streaming Pipeline Debug",
        "difficulty": "very_hard",
        "description": "Fix a broken streaming event pipeline: wrong stage order, "
                       "13 bugs across type casting, duplicates, nulls, invalid events, "
                       "outliers, and SLA violations.",
        "max_steps":  50,
    },
    {
        "task_id":    "task_expert_multi_source_join",
        "name":       "Multi-Source Join Repair",
        "difficulty": "expert",
        "description": "Repair a multi-source joined dataset: 17 bugs including wrong stage "
                       "order, 8 type mismatches, duplicates, nulls, negative values, and "
                       "business rule violations across quantity/price/discount/tax_rate.",
        "max_steps":  60,
    },
]

EXTRA_TASK_BUILDERS = {
    "task_veryhard_streaming_pipeline": build_veryhard_task,
    "task_expert_multi_source_join":    build_expert_task,
}

EXTRA_RULES = {
    "task_veryhard_streaming_pipeline": VERYHARD_RULES,
    "task_expert_multi_source_join":    EXPERT_RULES,
}
