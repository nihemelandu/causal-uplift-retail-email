"""evaluation/q2_incremental_sales.py

Question 2 of Hillstrom's challenge: how much incremental sales per customer did the Men's version of
the email campaign drive, and how much did the Women's version drive?

Incremental sales per customer is the average spend of an emailed group minus the average spend of the
no-email group; both averages include the customers who spent nothing. The result is saved as one
EvaluationResult for the dashboard. As in Q1, this is not an Evaluator subclass (it has no scores).
The estimate, its Welch interval and p-value come from `compare` in q1_effect_estimates, so Q1 and Q2
cannot disagree.

Contract
--------
Input  : the Hillstrom CSV (64,000 customers); `segment` is the randomised arm, `spend` the outcome.
Output : results/q2_incremental_sales.json (EvaluationResult.to_dict()). The file name must start
         with "q2_" so that the dashboard shows it under Q2.

Metrics, for each campaign (mens, womens) against the no-email group, named spend.<campaign>_vs_control.<stat>:
    treatment, control        average spend per customer, emailed group and no-email group, in dollars
    diff (+ _ci_low/_high)    incremental sales per customer, with its 95% CI
    p_value                   two-sided Welch t-test
    boot_ci_low / _high       95% bootstrap interval for diff (check on the normal-approximation CI)
Also saved: n_mens, n_womens, n_control (customers in each group).

Method: Welch t-test and normal-approximation CI. Spend is about 99% zeros with a heavy right tail, so the
bootstrap interval (2,000 resamples of customers, fixed seed) is saved as a check.

Run from the repo root:  python -m evaluation.q2_incremental_sales [path/to/hillstrom.csv]
"""

import argparse
import json

import numpy as np
import pandas as pd

from evaluation.base import EvaluationResult
from evaluation.q1_effect_estimates import ARM, PATH, compare

OUT_FILE = "results/q2_incremental_sales.json"   # must start with "q2_"
CAMPAIGNS = ["mens", "womens"]                   # each is compared with the no-email group
KEEP = ["treatment", "control", "diff", "diff_ci_low", "diff_ci_high", "p_value"]
BOOTSTRAP_REPS = 2000
SEED = 1


def bootstrap_ci(t: np.ndarray, r: np.ndarray, rng: np.random.Generator) -> tuple:
    """95% bootstrap interval for mean(t) - mean(r), resampling customers within each group."""
    diffs = [rng.choice(t, len(t)).mean() - rng.choice(r, len(r)).mean() for _ in range(BOOTSTRAP_REPS)]
    low, high = np.percentile(diffs, [2.5, 97.5])
    return low, high


def main(path: str = PATH) -> None:
    d = pd.read_csv(path)
    control = d.loc[d.segment == ARM["control"], "spend"]
    rng = np.random.default_rng(SEED)

    metrics = {}
    for campaign in CAMPAIGNS:
        treated = d.loc[d.segment == ARM[campaign], "spend"]
        est = compare(treated, control)
        for stat in KEEP:
            metrics[f"spend.{campaign}_vs_control.{stat}"] = est[stat]
        low, high = bootstrap_ci(treated.to_numpy(), control.to_numpy(), rng)
        metrics[f"spend.{campaign}_vs_control.boot_ci_low"] = low
        metrics[f"spend.{campaign}_vs_control.boot_ci_high"] = high
        metrics[f"n_{campaign}"] = len(treated)
    metrics["n_control"] = len(control)

    result = EvaluationResult(
        evaluator="Q2IncrementalSales",
        metrics=metrics,
        curves={},
        notes="Incremental sales per customer = average spend of the emailed group minus average spend of the "
              "no-email group, both including customers who spent nothing. Welch t-test and 95% "
              "normal-approximation CI; bootstrap CI (2,000 resamples) as a check.")

    with open(OUT_FILE, "w") as f:
        json.dump(result.to_dict(), f, indent=2)
    print("wrote", OUT_FILE, "with", len(result.metrics), "metrics")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Q2 incremental sales per customer for the Hillstrom data.")
    parser.add_argument("path", nargs="?", default=PATH,
                        help=f"path to the Hillstrom CSV (default: {PATH})")
    main(parser.parse_args().path)