import numpy as np
import math
from evaluation.base import Evaluator, EvaluationResult

class QiniEvaluator(Evaluator):
    def __init__(self, shares: int = 10, z: float = 1.96):
        self.shares = tuple(np.linspace(1 / shares, 1, num=shares))
        self.z = z

    def _evaluate(self, scores: np.ndarray, y: np.ndarray, t: np.ndarray) -> EvaluationResult:
        order = np.argsort(-scores, kind="stable")      # highest predicted uplift first
        t_s, y_s = t[order], y[order]
        n = len(y)

        xs, qini, lo, hi = [], [], [], []
        metrics = {}
        skipped = []

        for s in self.shares:
            k = int(np.ceil(round(s * n, 9)))           # round() guards against float error, e.g. 0.3 * 10
            tk, yk = t_s[:k], y_s[:k]
            y1, y0 = yk[tk == 1], yk[tk == 0]
            n1, n0 = len(y1), len(y0)
            pct = int(round(s * 100))

            if n1 < 2 or n0 < 2:                        # need both arms (and a variance) in the share
                skipped.append(pct)
                q = l = h = float("nan")
            else:
                ate = y1.mean() - y0.mean()             # ATE-hat for the top share
                q = y1.sum() - (n1 / n0) * y0.sum()     # equals ate * n1
                se = np.sqrt(y1.var(ddof=1) / n1 + y0.var(ddof=1) / n0)
                l, h = (ate - self.z * se) * n1, (ate + self.z * se) * n1

            xs.append(float(s)); qini.append(float(q)); lo.append(float(l)); hi.append(float(h))
            metrics[f"qini_{pct}"] = float(q)
            metrics[f"qini_{pct}_ci_low"] = float(l)
            metrics[f"qini_{pct}_ci_high"] = float(h)

        notes = "Unadjusted Qini curve; CI from asymptotic normality (Appendix A.3)."
        if skipped:
            notes += f" Shares with too few treated/control units were set to NaN: {skipped}."

        return EvaluationResult(
            evaluator=self.name,
            metrics=metrics,
            curves={
                "qini":         {"x": xs, "y": qini},
                "qini_ci_low":  {"x": xs, "y": lo},
                "qini_ci_high": {"x": xs, "y": hi},
            },
            notes=notes,
        )


