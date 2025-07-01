# ------------------------------
# File: utils/helpers.py
# ------------------------------
from typing import Any, Dict


def safe_nested_increment(d: Dict[str, Any], *keys: str, v: int = 1):
    """
    Safely increment a nested dictionary by arbitrary depth using keys.
    Usage:
        safe_nested_increment(results, k1, k2, k3, v=1)
        --> results[k1][k2][k3] += 1
    """
    current = d
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    last_key = keys[-1]
    current[last_key] = current.get(last_key, 0) + v


def flatten_nested_dict(d: Dict[str, Any], prefix: str = "") -> Dict[str, int]:
    """
    Flattens a nested dictionary to a flat dict with joined keys.
    {"a": {"b": {"c": 1}}} -> {"a.b.c": 1}
    """
    flat = {}
    for k, v in d.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            flat.update(flatten_nested_dict(v, prefix=full_key))
        else:
            flat[full_key] = v
    return flat
