"""Shared input and cohort validation (no external services)."""
from copy import deepcopy
import math
from numbers import Real


def number(value, name, minimum=0, maximum=None, positive=False):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    if value < minimum or (positive and value <= 0) or (maximum is not None and value > maximum):
        raise ValueError(f"{name} is outside its valid range")
    return float(value)


def year(value, name="year"):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


def cohorts(values, name="cohorts", json_keys=False):
    if not isinstance(values, dict):
        raise ValueError(f"{name} must be a year-to-capacity mapping")
    out = {}
    for key, value in values.items():
        if json_keys and isinstance(key, str) and key.isdigit():
            key = int(key)
        out[year(key, name)] = number(value, name)
    return out


def weights(values, name):
    if not isinstance(values, (list, dict)) or not values:
        raise ValueError(f"{name} must be a nonempty distribution")
    seq = values.values() if isinstance(values, dict) else values
    if not math.isclose(sum(number(v, name, maximum=1) for v in seq), 1, rel_tol=0, abs_tol=1e-9):
        raise ValueError(f"{name} must sum to one")
    return values


class Params:
    """Isolated parameter snapshot with provenance and explicit numeric access."""
    def __init__(self, blob):
        self._blob = deepcopy(blob)
        self._accessed = set()
        for path, node in self.entries():
            if node.get("kind") not in {"observed", "derived", "calibrated", "assumption"}:
                raise ValueError(f"{path}: missing or unsupported evidence kind")
            if any(key not in node for key in ("source", "date", "url")):
                raise ValueError(f"{path}: missing provenance fields")

    def entries(self):
        def walk(node, prefix=""):
            if not isinstance(node, dict):
                return
            if "value" in node:
                yield prefix, node
                return
            for key, value in node.items():
                if not key.startswith("_"):
                    yield from walk(value, f"{prefix}.{key}" if prefix else key)
        return list(walk(self._blob))

    def _node(self, path):
        node = self._blob
        for part in path.split("."):
            node = node[part]
        return node

    def get(self, path):
        self._accessed.add(path)
        node = self._node(path)
        formula = node.get("formula")
        if formula:
            values = [self.get(p) for p in formula["inputs"]]
            if formula["operation"] == "product":
                return math.prod(values)
            if formula["operation"] == "mean":
                return sum(values)/len(values)
            raise ValueError(f"Unsupported derived formula: {path}")
        return deepcopy(node["value"])

    def numeric(self, path, **kwargs):
        return number(self.get(path), path, **kwargs)

    def cite(self, path):
        node = self._node(path)
        return f"{node.get('source')} ({node.get('date')})"

    def kind(self, path):
        return self._node(path)["kind"]

    def assumptions(self):
        return [path for path, node in self.entries() if node["kind"] in {"assumption", "calibrated"}]

    def registry(self):
        accessed = set(self._accessed)
        result = [{"parameter": path, **node, "value": self.get(path),
                   "read_by_this_run": path in accessed} for path, node in self.entries()]
        self._accessed = accessed
        return result


def service_cohorts(signed, lag_weights, origin, end):
    """Full allocation ledger, including pre-window and beyond-horizon tails."""
    signed = cohorts(signed)
    if not isinstance(lag_weights,list):
        raise ValueError("Service lag weights must be a list indexed by lag year")
    weights(lag_weights, "service lag weights")
    return [dict(booking_year=y, requested_service_year=y+lag,
                 signed_gw=gw, allocation_weight=w, requested_gw=gw*w,
                 window="before" if y+lag < origin else "after" if y+lag >= end else "within")
            for y, gw in sorted(signed.items()) for lag, w in enumerate(lag_weights) if w]
