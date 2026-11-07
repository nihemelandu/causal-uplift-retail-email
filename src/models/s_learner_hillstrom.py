"""S-learner uplift model on the Hillstrom email dataset (Men's email vs. control).

Usage: python s_learner_hillstrom.py [path/to/hillstrom.csv]

S-learner: ONE model is fitted on covariates + treatment flag T.
Uplift(x) = P(y=1 | x, T=1) - P(y=1 | x, T=0).
Evaluation: 10-fold stratified CV, Qini computed per fold and on pooled out-of-fold scores.
No hyperparameter tuning (fixed, conservative settings) - this is a first-pass baseline.
"""
import json
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

SEED = 42
DATA = sys.argv[1] if len(sys.argv) > 1 else "hillstrom.csv"
ARM = "Mens E-Mail"
MODELS = ["S-LR", "S-LR+interactions", "S-XGB"]
N_PERM = 300


def load():
    df = pd.read_csv(DATA)
    df = df[df.segment.isin([ARM, "No E-Mail"])].reset_index(drop=True)
    t = (df.segment == ARM).astype(int).to_numpy()
    X = df[["recency", "history", "mens", "womens", "newbie"]].copy()
    dummies = pd.get_dummies(df[["zip_code", "channel"]], drop_first=True).astype(int)
    return df, pd.concat([X, dummies], axis=1), t


def make_model(name):
    if name == "S-XGB":
        return XGBClassifier(n_estimators=200, max_depth=3, learning_rate=0.05, subsample=0.8,
                             colsample_bytree=0.8, min_child_weight=5, random_state=SEED,
                             n_jobs=2, verbosity=0)
    return make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))


def design(X, t, name):
    A = X.copy()
    A["T"] = t
    if name == "S-LR+interactions":
        for c in X.columns:
            A[f"T_x_{c}"] = X[c].to_numpy() * t
    return A


def s_learner_uplift(name, Xtr, ttr, ytr, Xte):
    m = make_model(name).fit(design(Xtr, ttr, name), ytr)
    ones, zeros = np.ones(len(Xte), int), np.zeros(len(Xte), int)
    return m.predict_proba(design(Xte, ones, name))[:, 1] - m.predict_proba(design(Xte, zeros, name))[:, 1]


def qini_curve(score, y, t):
    """Q(k) = Y_T(k) - Y_C(k) * N_T(k)/N_C(k) over the top-k customers; Q(0)=0."""
    order = np.argsort(-score, kind="stable")
    y, t = y[order], t[order]
    nt, nc = np.cumsum(t), np.cumsum(1 - t)
    yt, yc = np.cumsum(y * t), np.cumsum(y * (1 - t))
    with np.errstate(divide="ignore", invalid="ignore"):
        q = yt - yc * nt / nc
    return pd.Series(np.r_[0.0, q]).interpolate().to_numpy()  # undefined while no control yet


def qini_scores(q):
    """(per-customer scale, endpoint-normalised) area between curve and random line."""
    n = len(q) - 1
    raw = (q - np.linspace(0, q[-1], n + 1)).sum() / (n + 1)
    return raw / n, (raw / abs(q[-1]) if q[-1] != 0 else float("nan"))


def top_p_ate(score, y, t, p):
    idx = np.argsort(-score, kind="stable")[: int(round(p * len(y)))]
    ys, ts = y[idx], t[idx]
    return float(ys[ts == 1].mean() - ys[ts == 0].mean())


def run(outcome, df, X, t):
    y = df[outcome].to_numpy()
    n = len(y)
    rng = np.random.default_rng(SEED)
    skf = StratifiedKFold(10, shuffle=True, random_state=SEED)
    oof = {m: np.zeros(n) for m in MODELS}
    folds = {m: [] for m in MODELS}
    for tr, te in skf.split(X, t * 2 + y):
        for m in MODELS:
            u = s_learner_uplift(m, X.iloc[tr], t[tr], y[tr], X.iloc[te])
            oof[m][te] = u
            q = qini_curve(u, y[te], t[te])
            per_cust, norm = qini_scores(q)
            folds[m].append({"qini_pc": per_cust, "qini_norm": norm, "endpoint_pc": q[-1] / len(te)})
    out = {"n": n, "overall_uplift": float(y[t == 1].mean() - y[t == 0].mean()), "models": {}}
    for m in MODELS:
        q = qini_curve(oof[m], y, t)
        obs, obs_norm = qini_scores(q)
        null = np.array([qini_scores(qini_curve(rng.permutation(oof[m]), y, t))[0] for _ in range(N_PERM)])
        f = pd.DataFrame(folds[m])
        out["models"][m] = {
            "pooled_qini_pc": obs, "pooled_qini_norm": obs_norm,
            "perm_null_mean": float(null.mean()), "perm_null_sd": float(null.std()),
            "perm_p": float((1 + (null >= obs).sum()) / (N_PERM + 1)),
            "fold_median_qini_pc": float(f.qini_pc.median()),
            "fold_qini_pc_min": float(f.qini_pc.min()), "fold_qini_pc_max": float(f.qini_pc.max()),
            "folds_positive": int((f.qini_pc > 0).sum()),
            "fold_median_qini_norm": float(f.qini_norm.median()),
            "fold_qini_norm_min": float(f.qini_norm.min()), "fold_qini_norm_max": float(f.qini_norm.max()),
            "fold_endpoints_neg": int((f.endpoint_pc <= 0).sum()),
            # Q(k)/N_T: endpoint = overall uplift; read as incremental outcomes per 1,000 emailed customers
            "curve_per_1000": [float(q[int(round(p * n))] / t.sum() * 1000) for p in np.linspace(0, 1, 11)],
            "ate_top_p": {f"{int(p * 100)}%": top_p_ate(oof[m], y, t, p) for p in np.linspace(0.1, 1, 10)},
            "score_sd": float(oof[m].std()), "score_min": float(oof[m].min()), "score_max": float(oof[m].max()),
        }
    return out


if __name__ == "__main__":
    df, X, t = load()
    print(f"Men's email vs control: n={len(df)}, treated={t.sum()}, control={(1 - t).sum()}, "
          f"features={list(X.columns)}", flush=True)
    results = {o: run(o, df, X, t) for o in ["conversion", "visit"]}
    print(json.dumps(results, indent=1))
