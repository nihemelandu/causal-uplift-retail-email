"""models/meta_learners.py

Meta-learners: uplift estimators built from standard ML models.
Each subclass implements _fit / _predict_uplift from models.base.UpliftModel.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import clone

from base import UpliftModel

_T = "__T__"  # name of the treatment column inside the S-learner's design matrix


class SLearner(UpliftModel):
    """Single-model learner (Lo, 2002; named S-learner by Künzel et al., 2019).

    One model is trained on treated AND control customers, with the treatment flag as an
    extra feature. Uplift(x) = P(y=1 | x, T=1) - P(y=1 | x, T=0).

    Parameters
    ----------
    base_learner : sklearn-style classifier with fit() and predict_proba().
        Put any scaling inside a Pipeline, so it is fitted on training data only.
    interactions : bool
        If True, add T x feature terms. Useful for linear base learners, which otherwise
        give every customer the same shift in log-odds from the treatment.
    """

    def __init__(self, base_learner, interactions: bool = False, random_state: int | None = None):
        super().__init__(random_state)
        self.base_learner = base_learner
        self.interactions = interactions

    # ---- design matrix ----------------------------------------------------
    def _design(self, X: pd.DataFrame, t) -> pd.DataFrame:
        t = np.asarray(t)
        A = X.copy()
        A[_T] = t
        if self.interactions:
            for col in X.columns:
                A[f"{_T}_x_{col}"] = X[col].to_numpy() * t
        return A

    # ---- UpliftModel interface -------------------------------------------
    def _fit(self, X: pd.DataFrame, t: np.ndarray, y: np.ndarray) -> None:
        self.model_ = clone(self.base_learner).fit(self._design(X, t), y)

    def _predict_uplift(self, X: pd.DataFrame) -> np.ndarray:
        n = len(X)
        p1 = self.model_.predict_proba(self._design(X, np.ones(n, dtype=int)))[:, 1]
        p0 = self.model_.predict_proba(self._design(X, np.zeros(n, dtype=int)))[:, 1]
        return p1 - p0

    def __repr__(self) -> str:
        return (f"SLearner(base_learner={type(self.base_learner).__name__}, "
                f"interactions={self.interactions})")


    class TLearner(UpliftModel):
        """Two model learners (Künzel et al., 2019).
        - Train one model using customers who received the campaign.
        - Train another model using customers who did not receive the campaign.
        - Predict the purchase probability for each customer using both models.
        - Calculate the difference.
        """
        
        def __init__(self, base_learner, random_state: int | None = None):
            super().__init__(random_state)
            self.base_learner = base_learner

        def _fit(self, X: pd.DataFrame, t: np.ndarray, y: np.ndarray) -> None:
            self.model_treated_ = clone(self.base_learner).fit(X[t == 1], y[t == 1])
            self.model_control_ = clone(self.base_learner).fit(X[t == 0], y[t == 0])

        def _predict_uplift(self, X: pd.DataFrame) -> np.ndarray:
            p1 = self.model_treated_.predict_proba(X)[:, 1]
            p0 = self.model_control_.predict_proba(X)[:, 1]
            return p1 - p0

        def __repr__(self) -> str:
            return f"TLearner(base_learner={type(self.base_learner).__name__})"