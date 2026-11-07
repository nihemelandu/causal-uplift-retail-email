"""models/base.py

Shared interface for every uplift model (meta-learners, causal forest, uplift RF, baselines).

Contract
--------
fit(X, t, y)      : trained on customers from BOTH arms (t = 1 emailed, t = 0 control),
                    with a binary outcome y.
predict_uplift(X) : one score per row, higher = more persuadable.

Evaluation code (Qini, top-P ATE) only ever sees these scores, so it works with any subclass.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
import pandas as pd


class UpliftModel(ABC):
    def __init__(self, random_state: int | None = None):
        self.random_state = random_state
        self.is_fitted_ = False
        self.feature_names_: list[str] | None = None

    # ---- subclasses implement these two ----------------------------------
    @abstractmethod
    def _fit(self, X: pd.DataFrame, t: np.ndarray, y: np.ndarray) -> None:
        """Train on validated data. Store whatever state is needed on self."""

    @abstractmethod
    def _predict_uplift(self, X: pd.DataFrame) -> np.ndarray:
        """Return a 1-D array of uplift scores, one per row of X."""

    # ---- public API (do not override) ------------------------------------
    def fit(self, X, t, y) -> "UpliftModel":
        X, t, y = self._validate_training_data(X, t, y)
        self.feature_names_ = list(X.columns)
        self._fit(X, t, y)
        self.is_fitted_ = True
        return self

    def predict_uplift(self, X) -> np.ndarray:
        if not self.is_fitted_:
            raise RuntimeError(f"{self.name} is not fitted yet. Call fit() first.")
        X = pd.DataFrame(X).reset_index(drop=True)
        missing = set(self.feature_names_) - set(X.columns)
        if missing:
            raise ValueError(f"Missing features at prediction time: {sorted(missing)}")
        X = X[self.feature_names_]  # enforce training column order
        scores = np.asarray(self._predict_uplift(X), dtype=float).ravel()
        if len(scores) != len(X):
            raise ValueError(f"Expected {len(X)} scores, got {len(scores)}.")
        return scores

    def fit_predict_uplift(self, X_train, t_train, y_train, X_test) -> np.ndarray:
        """Convenience for cross-validation loops."""
        return self.fit(X_train, t_train, y_train).predict_uplift(X_test)

    # ---- helpers ---------------------------------------------------------
    @property
    def name(self) -> str:
        return type(self).__name__

    @staticmethod
    def _validate_training_data(X, t, y):
        X = pd.DataFrame(X).reset_index(drop=True)
        t = np.asarray(t).astype(int).ravel()
        y = np.asarray(y).astype(int).ravel()
        if not (len(X) == len(t) == len(y)):
            raise ValueError(f"Length mismatch: X={len(X)}, t={len(t)}, y={len(y)}.")
        if not set(np.unique(t)) <= {0, 1}:
            raise ValueError("Treatment t must be binary (0 = control, 1 = treated).")
        if not set(np.unique(y)) <= {0, 1}:
            raise ValueError("Outcome y must be binary (project scope).")
        if t.min() == t.max():
            raise ValueError("Both treated and control customers are required.")
        return X, t, y

    def __repr__(self) -> str:
        return f"{self.name}(random_state={self.random_state})"