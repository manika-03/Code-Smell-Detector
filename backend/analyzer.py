"""
analyzer.py
-----------
Step B: Code smell detection using rule-based thresholds on extracted metrics.
Step C: Severity classification — deterministic rule-based (ML is an optional overlay).
Step D: Recommendation generation.

Thresholds are calibrated against real-world datasets such as the
"Code Smells and Refactoring Dataset 120k" (Kaggle) where:
  - God Class / Large Class: >= 5 methods in a single class
  - Long Method: avg function length > 20 lines  (SHORT snippets still flagged via LOC ratio)
  - High Complexity: cyclomatic complexity >= 4 per function on average
  - Long Parameter List: > 3 params per function on average
  - Duplicate Code: > 5% duplicate non-blank lines
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np


# ────────────────────────────────────────────────────────────
#  Smell Detection — Threshold Table
# ────────────────────────────────────────────────────────────

# Each entry: metric_key → (metric_name, threshold, comparison)
# Comparison: "gt" = greater than, "lt" = less than
SMELL_RULES: List[Dict] = [
    {
        "key":     "long_method",
        "metric":  "avg_function_length",
        "threshold": 20,
        "cmp":     "gt",
        "display": "Long Method",
    },
    {
        "key":     "high_complexity",
        "metric":  "cyclomatic_complexity",
        "threshold": 4,
        "cmp":     "gt",
        "display": "High Complexity",
    },
    {
        "key":     "long_parameter_list",
        "metric":  "avg_params",
        "threshold": 3,
        "cmp":     "gt",
        "display": "Long Parameter List",
    },
    {
        "key":     "duplicate_code",
        "metric":  "duplicate_ratio",
        "threshold": 0.05,
        "cmp":     "gt",
        "display": "Duplicate Code",
    },
    {
        "key":     "deep_nesting",
        "metric":  "max_nesting_depth",
        "threshold": 3,
        "cmp":     "gt",
        "display": "Deep Nesting",
    },
]

# ────────────────────────────────────────────────────────────
#  Recommendations per smell
# ────────────────────────────────────────────────────────────
RECOMMENDATIONS: Dict[str, str] = {
    "Long Method": (
        "Break this function into smaller, single-purpose methods "
        "(target ≤ 20 lines each). Apply the Extract Method refactoring."
    ),
    "Large Class": (
        "This class has too many responsibilities. Apply the Single Responsibility Principle — "
        "split by distinct concerns (e.g. UserManager, ReportService, EmailService)."
    ),
    "God Class": (
        "This class violates the Single Responsibility Principle severely. "
        "It handles unrelated domains (data, reporting, email, DB). "
        "Decompose into focused, cohesive domain-specific classes."
    ),
    "Duplicate Code": (
        "Extract repeated code blocks into shared utility functions. "
        "Apply the DRY (Don't Repeat Yourself) principle."
    ),
    "High Complexity": (
        "Replace deeply nested conditionals with guard clauses or early returns. "
        "Consider the Strategy or Command pattern to reduce branching."
    ),
    "Long Parameter List": (
        "Introduce a Parameter Object or data class to group related arguments. "
        "Use keyword arguments with defaults where possible."
    ),
    "Deep Nesting": (
        "Flatten deeply nested blocks using early returns (guard clauses). "
        "Extract inner blocks into well-named helper functions."
    ),
}

# Feature order expected by the ML model (must match train_model.py)
FEATURE_ORDER = [
    "loc",
    "cyclomatic_complexity",
    "num_functions",
    "avg_function_length",
    "max_function_length",
    "num_classes",
    "duplicate_ratio",
    "max_nesting_depth",
    "comment_ratio",
    "avg_params",
]


# ────────────────────────────────────────────────────────────
#  Step B: Smell Detection
# ────────────────────────────────────────────────────────────

def detect_smells(metrics: Dict[str, float]) -> List[str]:
    """
    Detect code smells from the extracted metrics dict.
    Returns a list of triggered smell display names.
    """
    triggered: List[str] = []

    # ── Standard threshold rules ──
    for rule in SMELL_RULES:
        val = metrics.get(rule["metric"], 0.0)
        if rule["cmp"] == "gt" and val > rule["threshold"]:
            triggered.append(rule["display"])
        elif rule["cmp"] == "lt" and val < rule["threshold"]:
            triggered.append(rule["display"])

    # ── Large Class: a class with >= 5 methods is a Large Class ──
    num_classes   = metrics.get("num_classes", 0)
    num_functions = metrics.get("num_functions", 0)
    loc           = metrics.get("loc", 0)

    if num_classes >= 1 and num_functions > 0:
        avg_methods_per_class = num_functions / num_classes
        # >= 5 methods in a class → Large Class (well-established threshold)
        if avg_methods_per_class >= 5:
            triggered.append("Large Class")

        # God Class: class with many methods spanning unrelated domains.
        # Heuristic: avg >= 7 methods in one class = God Class
        if avg_methods_per_class >= 7:
            triggered.append("God Class")

    # ── Large Module: no classes but huge function count ──
    elif num_classes == 0 and num_functions >= 8:
        triggered.append("Large Class")

    # ── Bloated Script: very high LOC, no structure ──
    if num_functions == 0 and num_classes == 0 and loc > 40:
        triggered.append("Long Method")

    # De-duplicate while preserving order
    seen = set()
    unique: List[str] = []
    for s in triggered:
        if s not in seen:
            seen.add(s)
            unique.append(s)

    return unique


# ────────────────────────────────────────────────────────────
#  Step C: Severity Classification (Deterministic Rule Engine)
# ────────────────────────────────────────────────────────────

# Per-smell severity weight
SMELL_WEIGHT = {
    "God Class":           3,
    "Large Class":         2,
    "High Complexity":     2,
    "Long Method":         2,
    "Deep Nesting":        2,
    "Long Parameter List": 1,
    "Duplicate Code":      1,
}

def _rule_based_severity(
    metrics: Dict[str, float],
    smells:  List[str],
) -> str:
    """
    Deterministic severity scorer.
    Score is the weighted sum of triggered smells + bonus for extreme metric values.
    LOW  →  score 0
    MEDIUM → score 1-3
    HIGH → score >= 4
    """
    # Weighted smell score
    score = sum(SMELL_WEIGHT.get(s, 1) for s in smells)

    cc  = metrics.get("cyclomatic_complexity", 0)
    loc = metrics.get("loc", 0)
    nd  = metrics.get("max_nesting_depth", 0)
    nf  = metrics.get("num_functions", 0)
    nc  = metrics.get("num_classes", 0)

    # Extreme metric bonuses
    if cc  > 10:  score += 3
    elif cc > 6:  score += 2
    elif cc > 4:  score += 1

    if loc > 200: score += 2
    elif loc > 50: score += 1

    if nd  > 4:   score += 2
    elif nd > 2:  score += 1

    # A single class with many methods is inherently HIGH (God Class pattern)
    if nc >= 1 and nf > 0 and (nf / nc) >= 7:
        score += 3
    elif nc >= 1 and nf > 0 and (nf / nc) >= 5:
        score += 2

    if score >= 4:
        return "HIGH"
    elif score >= 1:
        return "MEDIUM"
    return "LOW"


def classify_severity(
    metrics:    Dict[str, float],
    smells:     List[str],
    model=None,
    le=None,
) -> Tuple[str, str]:
    """
    Classify severity as LOW / MEDIUM / HIGH.

    The rule-based engine is always computed. The ML classifier is used as a
    secondary signal, but it cannot override to a LOWER severity than the rule engine.
    This prevents systematic under-classification of real code smells.
    """
    rule_severity = _rule_based_severity(metrics, smells)

    if model is not None and le is not None:
        try:
            import pandas as pd
            feature_df = pd.DataFrame(
                [[metrics.get(f, 0.0) for f in FEATURE_ORDER]],
                columns=FEATURE_ORDER
            )
            pred_encoded = model.predict(feature_df)[0]
            ml_severity  = str(le.inverse_transform([pred_encoded])[0])

            # Severity ordering for comparison
            order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}

            # Take the MAXIMUM of ML and rule-based — never downgrade
            if order.get(ml_severity, 0) >= order.get(rule_severity, 0):
                return ml_severity, "ml_classifier"
            else:
                return rule_severity, "ml_adapted"

        except Exception as e:
            print(f"[WARN] ML prediction failed: {e}")

    return rule_severity, "rule_based"


# ────────────────────────────────────────────────────────────
#  Step D: Recommendation Generation
# ────────────────────────────────────────────────────────────

def get_recommendations(smells: List[str]) -> List[str]:
    """Return recommendation strings for each triggered smell."""
    recs = []
    for smell in smells:
        rec = RECOMMENDATIONS.get(smell)
        if rec:
            recs.append(rec)
    return recs
