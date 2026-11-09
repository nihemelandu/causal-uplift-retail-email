"""evaluation/base.py

Template for every evaluator (Qini, top-P ATE, later: profit curve, balance checks, ...).

Contract
--------
An evaluator receives ONLY (scores, y, t):
    scores : uplift score per customer, higher = more persuadable
    y      : observed binary outcome
    t      : observed treatment flag (1 = emailed, 0 = control)
It returns an EvaluationResult, a JSON-safe bundle of scalar metrics and curves. That bundle is
also the unit the dashboard reads, so an evaluator never needs to know how the scores were made
(meta-learner, causal forest, propensity baseline, ...).
"""

import numpy as np
import math

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

def _clean(v):
    """Make a value JSON-safe: NaN/inf -> None, numpy types -> plain Python."""
    if isinstance(v, (float, np.floating)):
        v = float(v)
        return v if math.isfinite(v) else None
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, (list, tuple, np.ndarray)):
        return [_clean(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _clean(x) for k, x in v.items()}
    return v

@dataclass
class EvaluationResult:
    evaluator: str                                                   # e.g. "QiniEvaluator"
    metrics: dict = field(default_factory=dict)                      # name -> float | None
    curves: dict = field(default_factory=dict)                       # name -> {"x": [...], "y": [...]}
    notes: str = ""

    def __post_init__(self):
        self.metrics = _clean(self.metrics)
        self.curves = _clean(self.curves)
        for name, c in self.curves.items():
            if set(c) != {"x", "y"} or len(c["x"]) != len(c["y"]):
                raise ValueError(f"Curve '{name}' must have equal-length 'x' and 'y' lists.")

    def to_dict(self) -> dict:
        return {"evaluator": self.evaluator, "metrics": self.metrics,
                "curves": self.curves, "notes": self.notes}

    @classmethod
    def from_dict(cls, d: dict) -> "EvaluationResult":
        missing = {"evaluator", "metrics", "curves"} - set(d)
        if missing:
            raise ValueError(f"EvaluationResult is missing keys: {sorted(missing)}")
        return cls(d["evaluator"], d["metrics"], d["curves"], d.get("notes", ""))


class Evaluator(ABC):
    @property
    def name(self) -> str:
        return type(self).__name__

    # ---- subclasses implement this ---------------------------------------
    @abstractmethod
    def _evaluate(self, scores: np.ndarray, y: np.ndarray, t: np.ndarray) -> EvaluationResult:
        """Compute metrics on validated arrays and return an EvaluationResult."""

    # ---- public API (do not override) ------------------------------------
    def evaluate(self, scores, y, t) -> EvaluationResult:
        scores, y, t = self._validate(scores, y, t)
        result = self._evaluate(scores, y, t)
        if not isinstance(result, EvaluationResult):
            raise TypeError(f"{self.name}._evaluate must return an EvaluationResult.")
        return result

    @staticmethod
    def _validate(scores, y, t):
        scores = np.asarray(scores, dtype=float).ravel()
        y = np.asarray(y).astype(int).ravel()
        t = np.asarray(t).astype(int).ravel()
        if not (len(scores) == len(y) == len(t)):
            raise ValueError(f"Length mismatch: scores={len(scores)}, y={len(y)}, t={len(t)}.")
        if not np.isfinite(scores).all():
            raise ValueError("Scores contain NaN or infinite values.")
        if not set(np.unique(y)) <= {0, 1} or not set(np.unique(t)) <= {0, 1}:
            raise ValueError("y and t must be binary (0/1).")
        if t.min() == t.max():
            raise ValueError("Both treated and control customers are required.")
        return scores, y, t

    def __repr__(self) -> str:
        return f"{self.name}()"