"""
extractor.py
------------
Extracts 10 static code metrics from a raw Python code string.
Uses Python's built-in `ast` module and the `radon` library.
"""

import ast
import re
import textwrap
from collections import Counter
from typing import Dict, Any, Tuple

try:
    from radon.complexity import cc_visit
    RADON_AVAILABLE = True
except ImportError:
    RADON_AVAILABLE = False


# ────────────────────────────────────────────────────────────
#  Neutral fallback vector (returned when ast.parse() fails)
# ────────────────────────────────────────────────────────────
NEUTRAL_METRICS: Dict[str, float] = {
    "loc": 0.0,
    "cyclomatic_complexity": 1.0,
    "num_functions": 0.0,
    "avg_function_length": 0.0,
    "max_function_length": 0.0,
    "num_classes": 0.0,
    "duplicate_ratio": 0.0,
    "max_nesting_depth": 0.0,
    "comment_ratio": 0.0,
    "avg_params": 0.0,
}


# ────────────────────────────────────────────────────────────
#  Internal Helpers
# ────────────────────────────────────────────────────────────

def _lines_of_code(code: str) -> int:
    """Total non-empty lines."""
    return len([l for l in code.splitlines() if l.strip()])


def _cyclomatic_complexity(code: str) -> float:
    """Average cyclomatic complexity across all functions. Falls back to 1.0."""
    if not RADON_AVAILABLE:
        return _fallback_complexity(code)
    try:
        results = cc_visit(code)
        if not results:
            return 1.0
        return round(sum(r.complexity for r in results) / len(results), 2)
    except Exception:
        return _fallback_complexity(code)


def _fallback_complexity(code: str) -> float:
    """
    Rough cyclomatic complexity estimate without radon:
    CC ≈ 1 + number of branching keywords.
    """
    keywords = re.findall(
        r'\b(if|elif|else|for|while|except|and|or|case)\b', code
    )
    return max(1.0, round(1 + len(keywords) * 0.5, 2))


def _function_metrics(tree: ast.AST) -> Tuple[int, float, float]:
    """
    Returns: (num_functions, avg_function_length, max_function_length)
    """
    lengths = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = node.lineno
            end   = getattr(node, 'end_lineno', node.lineno)
            lengths.append(end - start + 1)

    num = len(lengths)
    avg = round(sum(lengths) / num, 2) if num else 0.0
    mx  = float(max(lengths)) if lengths else 0.0
    return num, avg, mx


def _num_classes(tree: ast.AST) -> int:
    return sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))


def _duplicate_ratio(code: str) -> float:
    """
    Ratio of duplicate non-blank lines to total non-blank lines.
    A line must appear ≥ 2 times to count as duplicate.
    """
    lines = [l.strip() for l in code.splitlines() if l.strip()]
    if not lines:
        return 0.0
    counts = Counter(lines)
    dup_lines = sum(c for c in counts.values() if c >= 2)
    return round(dup_lines / len(lines), 4)


def _max_nesting_depth(tree: ast.AST) -> int:
    """Walk the AST and compute the maximum nesting depth of control structures."""
    NEST_NODES = (ast.If, ast.For, ast.While, ast.With, ast.Try,
                  ast.AsyncFor, ast.AsyncWith)

    def depth(node: ast.AST, current: int) -> int:
        if isinstance(node, NEST_NODES):
            current += 1
        child_depths = [depth(child, current) for child in ast.iter_child_nodes(node)]
        return max(child_depths) if child_depths else current

    return depth(tree, 0)


def _comment_ratio(code: str) -> float:
    """Ratio of comment lines (starting with #) to total lines."""
    lines = code.splitlines()
    if not lines:
        return 0.0
    comment_lines = sum(1 for l in lines if re.match(r'^\s*#', l))
    return round(comment_lines / len(lines), 4)


def _avg_params(tree: ast.AST) -> float:
    """Average number of parameters (excl. self/cls) across all functions."""
    param_counts = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args.args
            # exclude self/cls conventional names
            filtered = [a for a in args if a.arg not in ('self', 'cls')]
            param_counts.append(len(filtered))
    if not param_counts:
        return 0.0
    return round(sum(param_counts) / len(param_counts), 2)


# ────────────────────────────────────────────────────────────
#  Public API
# ────────────────────────────────────────────────────────────

def extract_metrics(code: str) -> Tuple[Dict[str, float], bool]:
    """
    Extract 10 static code metrics from a Python code string.

    Returns:
        metrics    : dict of 10 numeric metric values
        parse_error: True if ast.parse() failed (non-Python or syntax error)
    """
    code = textwrap.dedent(code).strip()
    
    loc = _lines_of_code(code)
    cc  = _cyclomatic_complexity(code)
    comment_ratio = _comment_ratio(code)
    dup_ratio     = _duplicate_ratio(code)

    parse_error = False
    try:
        tree = ast.parse(code)
    except SyntaxError:
        parse_error = True
        metrics = dict(NEUTRAL_METRICS)
        metrics["loc"]            = float(loc)
        metrics["cyclomatic_complexity"] = cc
        metrics["comment_ratio"]  = comment_ratio
        metrics["duplicate_ratio"] = dup_ratio
        metrics["avg_function_length"] = float(loc)
        metrics["max_function_length"] = float(loc)
        return metrics, parse_error

    num_fn, avg_fn, max_fn = _function_metrics(tree)
    if num_fn == 0:
        avg_fn = float(loc)
        max_fn = float(loc)

    metrics: Dict[str, float] = {
        "loc":                   float(loc),
        "cyclomatic_complexity": cc,
        "num_functions":         float(num_fn),
        "avg_function_length":   avg_fn,
        "max_function_length":   max_fn,
        "num_classes":           float(_num_classes(tree)),
        "duplicate_ratio":       dup_ratio,
        "max_nesting_depth":     float(_max_nesting_depth(tree)),
        "comment_ratio":         comment_ratio,
        "avg_params":            _avg_params(tree),
    }
    return metrics, parse_error
