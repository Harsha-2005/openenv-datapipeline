"""
Task definitions for the Data Pipeline Debugger environment.
Each task has:
  - A data generator that produces a broken pipeline state
  - Target metrics the agent must reach
  - Bug registry tracking what needs fixing
"""

from __future__ import annotations
import random
import copy
from typing import Any, Dict, List, Tuple

from env.models import SchemaField, PipelineMetrics, PipelineState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_schema(*fields: Tuple[str, str, str, bool]) -> List[SchemaField]:
    """fields: (name, expected_type, actual_type, nullable)"""
    return [SchemaField(name=n, expected_type=e, actual_type=a, nullable=b)
            for n, e, a, b in fields]


def _compute_metrics(data: List[Dict], schema: List[SchemaField],
                     rules: List[callable] = None) -> PipelineMetrics:
    if not data:
        return PipelineMetrics()
    total = len(data)
    cols  = [s.name for s in schema]

    # completeness: fraction of non-null values across all cells
    non_null = sum(1 for row in data for c in cols if row.get(c) is not None and row.get(c) != "")
    completeness = non_null / (total * len(cols)) if cols else 0.0

    # uniqueness: unique rows / total rows
    seen = set()
    unique = 0
    for row in data:
        key = tuple(sorted(row.items()))
        if key not in seen:
            seen.add(key)
            unique += 1
    uniqueness = unique / total

    # accuracy: fraction of rows where every column matches expected type
    def _matches(val, typ):
        if val is None or val == "":
            return True  # null is typed later
        try:
            if typ == "int":   int(val); return True
            if typ == "float": float(val); return True
            if typ == "str":   return isinstance(val, str)
            if typ == "bool":  return str(val).lower() in ("true","false","0","1")
            return True
        except (ValueError, TypeError):
            return False

    correct = sum(
        1 for row in data
        if all(_matches(row.get(s.name), s.expected_type) for s in schema)
    )
    accuracy = correct / total

    # validity via business rules
    if rules:
        valid = sum(1 for row in data if all(r(row) for r in rules))
        validity = valid / total
    else:
        validity = accuracy

    return PipelineMetrics(
        completeness=round(completeness, 4),
        uniqueness=round(uniqueness, 4),
        validity=round(validity, 4),
        accuracy=round(accuracy, 4),
        sla_latency_ms=round(random.uniform(10, 50), 2),
    )


# ---------------------------------------------------------------------------
# TASK 1 — Easy: Schema Mismatch Fix
# ---------------------------------------------------------------------------

EASY_SCHEMA = _make_schema(
    ("customer_id",  "int",   "str",   False),
    ("age",          "int",   "str",   True),
    ("revenue",      "float", "str",   True),
    ("is_active",    "bool",  "str",   True),
    ("email",        "str",   "str",   False),
)

EASY_TARGET = {
    "completeness": 0.85,
    "accuracy":     0.90,
    "validity":     0.85,
}

def _generate_easy_data(seed: int = 42) -> List[Dict[str, Any]]:
    rng = random.Random(seed)
    rows = []
    for i in range(30):
        rows.append({
            "customer_id": str(rng.randint(1000, 9999)),      # should be int
            "age":         str(rng.randint(18, 80)) if rng.random() > 0.1 else None,
            "revenue":     str(round(rng.uniform(10.0, 9999.0), 2)),
            "is_active":   rng.choice(["True","False","true","false","1","0"]),
            "email":       f"user{i}@example.com" if rng.random() > 0.05 else None,
        })
    # introduce a few obviously bad values
    rows[2]["age"]     = "not_a_number"
    rows[7]["revenue"] = "N/A"
    rows[12]["customer_id"] = "ID-MISSING"
    return rows

EASY_BUGS = {
    "cast_customer_id_to_int": False,
    "cast_age_to_int":         False,
    "cast_revenue_to_float":   False,
    "handle_bad_age":          False,
    "handle_bad_revenue":      False,
}

def build_easy_task(seed: int = 42) -> PipelineState:
    data   = _generate_easy_data(seed)
    schema = copy.deepcopy(EASY_SCHEMA)
    metrics = _compute_metrics(data, schema)
    return PipelineState(
        task_id        = "task_easy_schema_fix",
        step_count     = 0,
        max_steps      = 10,
        pipeline_stage = "validate",
        data           = data,
        schema_info    = schema,
        error_log      = [
            "ERROR: column 'customer_id' expected int, got str on 30/30 rows",
            "ERROR: column 'age' expected int, got str on 29/30 rows",
            "ERROR: column 'revenue' expected float, got str on 30/30 rows",
            "WARNING: 2 null emails found",
        ],
        metrics        = metrics,
        cumulative_reward = 0.0,
        done           = False,
        applied_actions= [],
        bugs_fixed     = copy.deepcopy(EASY_BUGS),
        target_metrics = EASY_TARGET,
        stage_order    = ["ingest","validate","transform","enrich","load"],
    )


# ---------------------------------------------------------------------------
# TASK 2 — Medium: Data Quality Remediation
# ---------------------------------------------------------------------------

MEDIUM_SCHEMA = _make_schema(
    ("order_id",    "int",   "int",   False),
    ("product_id",  "int",   "int",   False),
    ("quantity",    "int",   "int",   True),
    ("unit_price",  "float", "float", True),
    ("discount",    "float", "float", True),
    ("region",      "str",   "str",   True),
    ("order_date",  "str",   "str",   True),
    ("total",       "float", "float", True),
)

MEDIUM_TARGET = {
    "completeness": 0.90,
    "uniqueness":   0.95,
    "validity":     0.88,
    "accuracy":     0.90,
}

MEDIUM_RULES = [
    lambda r: r.get("quantity") is None or (isinstance(r.get("quantity"), (int,float)) and r["quantity"] > 0),
    lambda r: r.get("unit_price") is None or (isinstance(r.get("unit_price"), (int,float)) and r["unit_price"] >= 0),
    lambda r: r.get("discount") is None or (isinstance(r.get("discount"), (int,float)) and 0 <= r["discount"] <= 1),
]

def _generate_medium_data(seed: int = 42) -> List[Dict[str, Any]]:
    rng = random.Random(seed)
    regions = ["NORTH","SOUTH","EAST","WEST","CENTRAL"]
    rows = []
    for i in range(60):
        qty   = rng.randint(1, 100)
        price = round(rng.uniform(5.0, 500.0), 2)
        disc  = round(rng.uniform(0, 0.4), 2)
        rows.append({
            "order_id":   1000 + i,
            "product_id": rng.randint(100, 199),
            "quantity":   qty,
            "unit_price": price,
            "discount":   disc,
            "region":     rng.choice(regions),
            "order_date": f"2024-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
            "total":      round(qty * price * (1 - disc), 2),
        })

    # Bug 1: nulls sprinkled (~15% of rows)
    for i in rng.sample(range(60), 9):
        col = rng.choice(["quantity","unit_price","region","order_date"])
        rows[i][col] = None

    # Bug 2: duplicates (add 5 exact duplicates)
    for _ in range(5):
        rows.append(copy.deepcopy(rng.choice(rows[:40])))

    # Bug 3: outliers in quantity (impossible values)
    rows[3]["quantity"]   = -5
    rows[11]["quantity"]  = 99999
    rows[22]["discount"]  = 1.5    # > 1.0, invalid
    rows[35]["unit_price"] = -20.0 # negative price

    # Bug 4: wrong total on 8 rows
    for i in rng.sample(range(40), 8):
        rows[i]["total"] = round(rows[i]["total"] * rng.uniform(0.5, 1.8), 2)

    rng.shuffle(rows)
    return rows

MEDIUM_BUGS = {
    "drop_duplicates":        False,
    "fill_or_drop_nulls":     False,
    "filter_negative_qty":    False,
    "filter_outlier_qty":     False,
    "fix_invalid_discount":   False,
    "fix_negative_price":     False,
}

def build_medium_task(seed: int = 42) -> PipelineState:
    data    = _generate_medium_data(seed)
    schema  = copy.deepcopy(MEDIUM_SCHEMA)
    metrics = _compute_metrics(data, schema, MEDIUM_RULES)
    return PipelineState(
        task_id        = "task_medium_data_quality",
        step_count     = 0,
        max_steps      = 20,
        pipeline_stage = "transform",
        data           = data,
        schema_info    = schema,
        error_log      = [
            f"WARNING: {65} total rows, {5} apparent duplicates detected",
            "WARNING: 9 null values across quantity/unit_price/region/order_date",
            "ERROR: quantity=-5 violates business rule qty>0",
            "ERROR: discount=1.5 violates rule 0<=discount<=1",
            "ERROR: unit_price=-20.0 violates rule price>=0",
            "WARNING: 8 rows have inconsistent 'total' vs quantity*price*(1-discount)",
        ],
        metrics        = metrics,
        cumulative_reward = 0.0,
        done           = False,
        applied_actions= [],
        bugs_fixed     = copy.deepcopy(MEDIUM_BUGS),
        target_metrics = MEDIUM_TARGET,
        stage_order    = ["ingest","validate","transform","enrich","load"],
    )


# ---------------------------------------------------------------------------
# TASK 3 — Hard: Full Pipeline Orchestration Debug
# ---------------------------------------------------------------------------

HARD_SCHEMA = _make_schema(
    ("txn_id",       "int",   "str",   False),
    ("user_id",      "int",   "str",   False),
    ("amount",       "float", "str",   False),
    ("currency",     "str",   "str",   True),
    ("merchant",     "str",   "str",   True),
    ("category",     "str",   "str",   True),
    ("timestamp",    "str",   "str",   False),
    ("fraud_score",  "float", "str",   True),
    ("country_code", "str",   "str",   True),
    ("is_flagged",   "bool",  "str",   True),
)

HARD_TARGET = {
    "completeness": 0.92,
    "uniqueness":   0.97,
    "validity":     0.90,
    "accuracy":     0.92,
    "sla_latency_ms_max": 100.0,
}

HARD_RULES = [
    lambda r: r.get("amount") is None or (isinstance(r.get("amount"),(int,float)) and r["amount"] > 0),
    lambda r: r.get("fraud_score") is None or (isinstance(r.get("fraud_score"),(int,float)) and 0<=r["fraud_score"]<=1),
    lambda r: r.get("currency") is None or (isinstance(r.get("currency"),str) and len(r["currency"])==3),
    lambda r: r.get("country_code") is None or (isinstance(r.get("country_code"),str) and len(r["country_code"])==2),
]

HARD_STAGE_ORDER_CORRECT = ["ingest","validate","transform","enrich","load"]

def _generate_hard_data(seed: int = 42) -> List[Dict[str, Any]]:
    rng      = random.Random(seed)
    cats     = ["food","travel","retail","utilities","entertainment","health"]
    merchants= ["Amazon","Walmart","Uber","Netflix","Spotify","BP","CVS","Target"]
    currencies= ["USD","EUR","GBP","JPY","CAD","AUD"]
    countries = ["US","GB","DE","FR","JP","CA","AU","IN"]
    rows = []
    for i in range(100):
        rows.append({
            "txn_id":      str(10000 + i),          # str instead of int
            "user_id":     str(rng.randint(1,500)),  # str instead of int
            "amount":      str(round(rng.uniform(1.0, 5000.0), 2)),  # str
            "currency":    rng.choice(currencies),
            "merchant":    rng.choice(merchants),
            "category":    rng.choice(cats),
            "timestamp":   f"2024-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}T{rng.randint(0,23):02d}:{rng.randint(0,59):02d}:00Z",
            "fraud_score": str(round(rng.uniform(0, 1), 3)),
            "country_code":rng.choice(countries),
            "is_flagged":  str(rng.random() < 0.05).lower(),
        })

    # Bug 1: wrong stage ordering — stages will be scrambled
    # (tracked in stage_order, not in data)

    # Bug 2: nulls (~12% cells)
    null_targets = ["merchant","category","fraud_score","country_code","currency"]
    for i in rng.sample(range(100), 12):
        rows[i][rng.choice(null_targets)] = None

    # Bug 3: duplicates (7 rows)
    for _ in range(7):
        rows.append(copy.deepcopy(rng.choice(rows[:80])))

    # Bug 4: invalid amounts (negative)
    for i in [5, 14, 33]:
        rows[i]["amount"] = str(-abs(float(rows[i]["amount"])))

    # Bug 5: bad fraud_score (>1)
    for i in [8, 20, 45]:
        rows[i]["fraud_score"] = str(round(rng.uniform(1.1, 3.0), 2))

    # Bug 6: currency wrong length
    rows[3]["currency"]    = "USDD"
    rows[17]["currency"]   = "X"
    rows[30]["country_code"]= "USA"  # 3-letter instead of 2

    rng.shuffle(rows)
    return rows

HARD_BUGS = {
    "fix_stage_order":           False,   # stages run out of order → must reorder
    "cast_txn_id_to_int":        False,
    "cast_user_id_to_int":       False,
    "cast_amount_to_float":      False,
    "cast_fraud_score_to_float": False,
    "drop_duplicates":           False,
    "fill_nulls_merchant":       False,
    "fill_nulls_fraud_score":    False,
    "filter_negative_amounts":   False,
    "fix_invalid_fraud_scores":  False,
    "fix_currency_codes":        False,
    "fix_country_codes":         False,
    "validate_final":            False,
}

HARD_WRONG_STAGE_ORDER = ["ingest","transform","validate","load","enrich"]  # scrambled

def build_hard_task(seed: int = 42) -> PipelineState:
    data    = _generate_hard_data(seed)
    schema  = copy.deepcopy(HARD_SCHEMA)
    metrics = _compute_metrics(data, schema, HARD_RULES)
    return PipelineState(
        task_id        = "task_hard_pipeline_orchestration",
        step_count     = 0,
        max_steps      = 40,
        pipeline_stage = "ingest",
        data           = data,
        schema_info    = schema,
        error_log      = [
            "CRITICAL: Pipeline stage order is WRONG: [ingest,transform,validate,load,enrich]",
            "ERROR: 107 rows — 7 suspected duplicates",
            "ERROR: column 'txn_id' expected int, got str on all rows",
            "ERROR: column 'amount' expected float, got str; 3 rows have negative amounts",
            "ERROR: fraud_score=2.3 violates 0<=score<=1 on 3 rows",
            "ERROR: currency 'USDD' invalid (not 3-char ISO code)",
            "ERROR: country_code 'USA' invalid (not 2-char ISO code)",
            "WARNING: 12 null values in merchant/category/fraud_score/country_code",
            "SLA BREACH: Current estimated latency 320ms > 100ms threshold",
        ],
        metrics        = metrics,
        cumulative_reward = 0.0,
        done           = False,
        applied_actions= [],
        bugs_fixed     = copy.deepcopy(HARD_BUGS),
        target_metrics = HARD_TARGET,
        stage_order    = HARD_WRONG_STAGE_ORDER.copy(),
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

TASK_BUILDERS = {
    "task_easy_schema_fix":           build_easy_task,
    "task_medium_data_quality":        build_medium_task,
    "task_hard_pipeline_orchestration":build_hard_task,
}

TASK_INFO = [
    {
        "task_id":    "task_easy_schema_fix",
        "name":       "Schema Mismatch Fix",
        "difficulty": "easy",
        "description":"Identify and cast mis-typed columns so the schema is valid.",
        "max_steps":  10,
    },
    {
        "task_id":    "task_medium_data_quality",
        "name":       "Data Quality Remediation",
        "difficulty": "medium",
        "description":"Remove duplicates, fill nulls, and filter outliers across an order dataset.",
        "max_steps":  20,
    },
    {
        "task_id":    "task_hard_pipeline_orchestration",
        "name":       "Full Pipeline Orchestration Debug",
        "difficulty": "hard",
        "description":"Fix stage ordering, type errors, duplicates, nulls, and constraint violations in a transaction pipeline under SLA.",
        "max_steps":  40,
    },
]

# ---------------------------------------------------------------------------
# Register extra tasks (very_hard + expert) — imported from extra_tasks.py
# ---------------------------------------------------------------------------
try:
    from tasks.extra_tasks import EXTRA_TASK_BUILDERS, EXTRA_TASK_INFO
    TASK_BUILDERS.update(EXTRA_TASK_BUILDERS)
    TASK_INFO.extend(EXTRA_TASK_INFO)
except ImportError:
    pass  # extra tasks are optional — base 3 tasks always available