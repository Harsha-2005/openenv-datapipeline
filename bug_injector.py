"""
bug_injector.py — OpenEnv Data Pipeline Debugger
Implements dynamic and reproducible data quality fault injection.
Used by the curriculum to organically scale task difficulty without hardcoding data.
"""

from __future__ import annotations
import random
from typing import List, Dict, Any

class DynamicBugInjector:
    """
    Injects deterministic bugs into an array of dict (rows).
    Supports:
        - null_injection (drops values)
        - duplicate_injection (repeats rows)
        - schema_drift (casts types to strings/bad formats)
        - outlier_injection (adds extreme values)
    """

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def inject_nulls(self, data: List[Dict[str, Any]], column: str, rate: float = 0.1) -> List[Dict[str, Any]]:
        """Sets random values in the column to None."""
        if not data or not data[0].get(column):
            return data
        
        for row in data:
            if self.rng.random() < rate:
                row[column] = None
        return data

    def inject_duplicates(self, data: List[Dict[str, Any]], rate: float = 0.05) -> List[Dict[str, Any]]:
        """Duplicates existing rows and appends them to the dataset."""
        if not data:
            return data
            
        num_dups = int(len(data) * rate)
        if num_dups == 0:
            return data
            
        dups = self.rng.choices(data, k=num_dups)
        # Deep copy the duplicated rows so modifications don't link
        dups = [dict(d) for d in dups]
        data.extend(dups)
        self.rng.shuffle(data)
        return data

    def inject_schema_drift(self, data: List[Dict[str, Any]], column: str, rate: float = 0.2) -> List[Dict[str, Any]]:
        """Converts values to wrong types (e.g., float to string with text)."""
        if not data:
            return data
            
        for row in data:
            if self.rng.random() < rate and row.get(column) is not None:
                val = row[column]
                if isinstance(val, (int, float)):
                    # Corrupt numeric to bad string
                    row[column] = f"invalid_{val}"
        return data

    def inject_outliers(self, data: List[Dict[str, Any]], column: str, multiplier: float = 100.0, rate: float = 0.05) -> List[Dict[str, Any]]:
        """Multiplies numeric values by an extreme amount."""
        if not data:
            return data
            
        for row in data:
            if self.rng.random() < rate and row.get(column) is not None:
                try:
                    val = float(row[column])
                    row[column] = val * multiplier
                except (ValueError, TypeError):
                    pass
        return data

    def apply_preset(self, data: List[Dict[str, Any]], severity: str = "medium") -> List[Dict[str, Any]]:
        """Applies a collection of bugs based on severity profile."""
        if not data:
            return data
            
        cols = list(data[0].keys())
        num_col = [c for c in cols if all(isinstance(r.get(c), (int, float)) for r in data if r.get(c) is not None)]
        str_col = [c for c in cols if c not in num_col]

        rates = {
            "easy":   {"null": 0.05, "dup": 0.02, "drift": 0.0},
            "medium": {"null": 0.15, "dup": 0.08, "drift": 0.1},
            "hard":   {"null": 0.25, "dup": 0.15, "drift": 0.2, "outlier": 0.1},
        }.get(severity, {"null": 0.1, "dup": 0.05})

        # Inject nulls
        if str_col:
            self.inject_nulls(data, self.rng.choice(str_col), rates["null"])
            
        # Inject duplicates
        self.inject_duplicates(data, rates["dup"])
        
        # Inject drift and outliers
        if num_col and "drift" in rates and rates["drift"] > 0:
            self.inject_schema_drift(data, self.rng.choice(num_col), rates["drift"])
            
        if num_col and "outlier" in rates and rates["outlier"] > 0:
            self.inject_outliers(data, self.rng.choice(num_col), rate=rates["outlier"])

        return data
