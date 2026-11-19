"""evaluation/q1_effect_estimates.py

Question 1 of Hillstrom's challenge: which campaign performed best, the Men's or the Women's email?

Estimates the effect of each email on visit rate, conversion rate and spend per customer, as
treatment-minus-reference differences, and saves them as one EvaluationResult for the dashboard.
This is not an Evaluator subclass: that contract takes (scores, y, t) with a binary y, and Q1 has
no scores and a non-binary outcome (spend). It builds an EvaluationResult directly.

Contract
--------
Input  : the Hillstrom CSV (64,000 customers). `segment` is the randomised arm ("Mens E-Mail",
         "Womens E-Mail" or "No E-Mail"); `visit`, `conversion` and `spend` are the outcomes.
Output : results/q1_effect_estimates.json (EvaluationResult.to_dict()). The file name must start
         with "q1_" so that the dashboard shows it under Q1.

Comparisons (treatment vs reference): mens_vs_control, womens_vs_control, mens_vs_womens.
Metrics are named  <outcome>.<comparison>.<stat>  (exactly two dots, which the dashboard turns into
one table per outcome):
    treatment, control        mean of the outcome in each arm ("control" is the reference arm)
    diff (+ _ci_low/_high)    treatment minus reference, with its 95% CI
    rel_diff_pct (+ CI)       relative difference, in percentage points, with its 95% CI
    p_value                   two-sided Welch t-test
Units: visit and conversion are proportions, spend is dollars per customer.
Also saved: n_mens, n_womens, n_control and srm_p_value_equal_thirds (sample-ratio check against
an equal three-way split), and, for the dashboard's reporting sections:
    primary.<outcome>        1 for the primary outcome, 0 for the others
    bonferroni_alpha         0.05 divided by the three comparisons made for each measure
    balance.<row>.<stat>     baseline table, one row per pre-email characteristic (a 0/1 row for each level
                             of a category). control / womens / mens = group mean (a share, for 0/1 rows);
                             sd_control / sd_womens / sd_mens = group standard deviation (continuous rows
                             only); smd_womens / smd_mens = standardized difference vs the no-email group.
                             No significance tests: with random allocation any baseline difference is chance
                             (CONSORT 2010, item 15).

Method: Welch t-test and normal-approximation CIs; the relative CI uses the delta method. Spend is
about 99% zeros with a heavy right tail, so read its intervals as approximate. Multiplicity: Bonferroni,
with three comparisons per measure (alpha = 0.05 / 3). The primary outcome is spend per customer, the
measure closest to campaign profitability (Radcliffe, 2008, section 3).

Run from the repo root:  python -m evaluation.q1_effect_estimates
"""

import json

import numpy as np
import pandas as pd
import argparse
from scipy import stats

from evaluation.base import EvaluationResult

PATH = "hillstrom_raw.csv"                      # the Hillstrom CSV; change to its location
OUT_FILE = "results/q1_effect_estimates.json"   # must start with "q1_"

PRIMARY_OUTCOME = "spend"                       # the other two outcomes are secondary
BASELINE_CONTINUOUS = ["recency", "history"]
BASELINE_BINARY = ["mens", "womens", "newbie"]
BASELINE_CATEGORICAL = ["zip_code", "channel"]  # one 0/1 row per level

ARM = {"mens": "Mens E-Mail", "womens": "Womens E-Mail", "control": "No E-Mail"}
OUTCOMES = ["visit", "conversion", "spend"]
COMPARISONS = [("mens", "control"), ("womens", "control"), ("mens", "womens")]  # (treatment, reference)
BONFERRONI_ALPHA = 0.05 / len(COMPARISONS)      # three comparisons per measure
Z = stats.norm.ppf(0.975)                       # 95% two-sided


def compare(t: pd.Series, r: pd.Series) -> dict:
    """Treatment (t) vs reference (r): arm means, difference, relative difference, CIs and p-value."""
    n1, n0 = len(t), len(r)
    m1, m0 = t.mean(), r.mean()
    v1, v0 = t.var(ddof=1) / n1, r.var(ddof=1) / n0          # variances of the two means
    diff, se = m1 - m0, np.sqrt(v1 + v0)
    p = stats.ttest_ind(t, r, equal_var=False).pvalue        # Welch
    rel = (m1 / m0 - 1) * 100                                # delta method, in percentage points
    se_rel = np.sqrt(v1 / m0**2 + m1**2 * v0 / m0**4) * 100
    return {"treatment": m1, "control": m0,
            "diff": diff, "diff_ci_low": diff - Z * se, "diff_ci_high": diff + Z * se,
            "rel_diff_pct": rel, "rel_diff_pct_ci_low": rel - Z * se_rel,
            "rel_diff_pct_ci_high": rel + Z * se_rel, "p_value": p}


def balance_metrics(d: pd.DataFrame) -> dict:
    """Baseline table: each pre-email characteristic by arm, plus the standardized difference of each
    email arm vs the no-email arm. A category becomes one 0/1 row per level."""
    rows = {v: d[v] for v in BASELINE_CONTINUOUS + BASELINE_BINARY}
    for v in BASELINE_CATEGORICAL:
        for level in sorted(d[v].unique()):
            rows[f"{v}_{level}"] = (d[v] == level).astype(int)

    out = {}
    for name, x in rows.items():
        by_arm = {k: x[d.segment == ARM[k]] for k in ARM}
        for k, s in by_arm.items():
            out[f"balance.{name}.{k}"] = s.mean()
            if name in BASELINE_CONTINUOUS:
                out[f"balance.{name}.sd_{k}"] = s.std()
        for k in ("womens", "mens"):
            pooled = np.sqrt((by_arm[k].var() + by_arm["control"].var()) / 2)
            out[f"balance.{name}.smd_{k}"] = (by_arm[k].mean() - by_arm["control"].mean()) / pooled
    return out


def main(path: str = PATH) -> None:
    d = pd.read_csv(path)

    metrics = {}
    for outcome in OUTCOMES:
        for a, b in COMPARISONS:
            est = compare(d.loc[d.segment == ARM[a], outcome], d.loc[d.segment == ARM[b], outcome])
            for stat, v in est.items():
                metrics[f"{outcome}.{a}_vs_{b}.{stat}"] = v   # EvaluationResult cleans numpy types and NaN

    obs = d.segment.value_counts().reindex(list(ARM.values()))
    for k, v in zip(ARM, obs):
        metrics[f"n_{k}"] = v
    metrics["srm_p_value_equal_thirds"] = stats.chisquare(obs).pvalue

    for outcome in OUTCOMES:
        metrics[f"primary.{outcome}"] = int(outcome == PRIMARY_OUTCOME)
    metrics["bonferroni_alpha"] = BONFERRONI_ALPHA
    metrics.update(balance_metrics(d))

    result = EvaluationResult(
        evaluator="Q1EffectEstimates",
        metrics=metrics,
        curves={},
        notes="Welch t-test; 95% CIs (normal approximation); relative difference and its CI by the delta "
              "method, in percentage points. Differences are treatment minus reference; for "
              "'mens_vs_womens' the reference is the Women's arm. Primary outcome: spend per customer "
              "(closest to campaign profitability); visit and purchase rates are secondary. Multiplicity: "
              "Bonferroni, three comparisons per measure (alpha = 0.05 / 3).")

    with open(OUT_FILE, "w") as f:
        json.dump(result.to_dict(), f, indent=2)
    print("wrote", OUT_FILE, "with", len(result.metrics), "metrics")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Q1 effect estimates for the Hillstrom data.")
    parser.add_argument("path", nargs="?", default=PATH,
                        help=f"path to the Hillstrom CSV (default: {PATH})")
    main(parser.parse_args().path)