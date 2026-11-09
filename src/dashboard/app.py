"""dashboard/app.py - Sprint 1 dashboard.

Depends only on evaluation/base.py (EvaluationResult). It reads results/*.json, where each file is
one EvaluationResult.to_dict(), and renders whatever metrics and curves it finds. It never trains,
scores or evaluates anything, and it names no specific evaluator.

Naming convention it understands (so any evaluator can use it):
    a metric or curve called  X  with companions  X_ci_low  and  X_ci_high
    -> metrics are shown in an interval table; curves are drawn as a line with a shaded band.
"""
import json
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # repo root, so `evaluation` can be imported
from evaluation.base import EvaluationResult  # noqa: E402

RESULTS_DIR = ROOT.parent / "results"
CI_LOW, CI_HIGH = "_ci_low", "_ci_high"

st.set_page_config(page_title="Who should we email?", layout="wide")


# ---- helpers ---------------------------------------------------------------------
@st.cache_data(ttl=300)
def folder_signature(results_dir=RESULTS_DIR) -> tuple:
    """Changes whenever a result file is added, removed or modified, so the cache below never goes stale."""
    return tuple((p.name, p.stat().st_mtime_ns) for p in sorted(Path(results_dir).glob("*.json")))


@st.cache_data
def load_results(signature: tuple, results_dir: str = str(RESULTS_DIR)):
    """Return ({file name: EvaluationResult as dict}, {file name: error message})."""
    ok, bad = {}, {}
    for path in sorted(Path(results_dir).glob("*.json")):
        try:
            ok[path.stem] = EvaluationResult.from_dict(json.loads(path.read_text())).to_dict()
        except Exception as e:  # noqa: BLE001 - one bad file must not take the page down
            bad[path.name] = str(e)
    return ok, bad


def split_ci(named: dict):
    """Split names into (main names, {name: (low_name, high_name)} for those with CI companions).
    The *_ci_low / *_ci_high entries themselves are not in the main list."""
    def is_ci_part(k):
        return any(k.endswith(s) and k[: -len(s)] in named for s in (CI_LOW, CI_HIGH))

    main = [k for k in named if not is_ci_part(k)]
    bands = {k: (k + CI_LOW, k + CI_HIGH) for k in main if k + CI_LOW in named and k + CI_HIGH in named}
    return main, bands


def num(values) -> pd.Series:
    return pd.to_numeric(pd.Series(values), errors="coerce")  # None -> NaN, so gaps are drawn as gaps


def fmt(v) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, int):
        return f"{v:,}"
    if isinstance(v, float):
        return f"{v:.4g}"
    return str(v)


def sig(v):
    return None if v is None else float(f"{v:.4g}")


X_ENC = alt.X("x:Q", title="Share of customers targeted", axis=alt.Axis(format="%"))


def curve_chart(curves: dict, names: list, bands: dict):
    """Lines for `names` (name -> {"x","y"}); a shaded band behind each name that has one in `bands`."""
    color = alt.Color("curve:N", title=None)
    layers = []
    for n in names:
        if n in bands:
            lo, hi = bands[n]
            b = pd.DataFrame({"x": num(curves[lo]["x"]), "curve": n,
                              "lo": num(curves[lo]["y"]), "hi": num(curves[hi]["y"])})
            layers.append(alt.Chart(b).mark_area(opacity=0.2).encode(
                x=X_ENC, y=alt.Y("lo:Q", title="Value"), y2="hi:Q", color=color))
    long = pd.concat([pd.DataFrame({"x": num(curves[n]["x"]), "curve": n, "y": num(curves[n]["y"])})
                      for n in names], ignore_index=True)
    layers.append(alt.Chart(long).mark_line(point=True).encode(
        x=X_ENC, y=alt.Y("y:Q", title="Value"), color=color))
    return alt.layer(*layers).properties(height=340)


# ---- page ----------------------------------------------------------------------------
st.title("Who should we email?")
st.caption("Finding the customers an email actually persuades, not those who would buy anyway.")

results, errors = load_results(folder_signature())
for fname, msg in errors.items():
    st.warning(f"Could not read `{fname}`: {msg}")
if not results:
    st.info("No result files found yet. Save an EvaluationResult as JSON in the results/ folder and push it.")
    st.stop()

name = st.sidebar.selectbox("Result", list(results))
res = results[name]

st.subheader(f"{res['evaluator']}  ·  {name}")
if res["notes"]:
    st.caption(res["notes"])

# ---- metrics ---------------------------------------------------------------------------
metrics = res["metrics"]
main_m, ci_m = split_ci(metrics)
plain = [k for k in main_m if k not in ci_m]

if plain:
    st.markdown("**Metrics**")
    for i in range(0, len(plain), 4):
        for col, key in zip(st.columns(4), plain[i:i + 4]):
            col.metric(key, fmt(metrics[key]))

if ci_m:
    st.markdown("**Estimates with intervals**")
    rows = []
    for k, (lo, hi) in ci_m.items():
        est, l, h = metrics[k], metrics[lo], metrics[hi]
        rows.append({"metric": k, "estimate": sig(est), "ci_low": sig(l), "ci_high": sig(h)})
    st.dataframe(pd.DataFrame(rows), hide_index=True)
    st.caption("Intervals describe uncertainty in each estimate. Whether a ranking beats random targeting is a "
               "different question: compare the curve with a random-targeting reference, not with zero. "
               "If an evaluator reports several intervals, treat them as pointwise.")

if not metrics:
    st.write("This result has no metrics.")

# ---- curves: curves sharing the same x values go on one chart ----------------------------
curves = res["curves"]
main_c, ci_c = split_ci(curves)
groups = {}
for n in main_c:
    groups.setdefault(tuple(curves[n]["x"]), []).append(n)
for names in groups.values():
    st.markdown("**" + "  /  ".join(names) + "**")
    st.altair_chart(curve_chart(curves, names, {n: ci_c[n] for n in names if n in ci_c}))

# ---- compare results ---------------------------------------------------------------------
if len(results) > 1:
    st.subheader("Compare results")
    curve_names = sorted({c for r in results.values() for c in split_ci(r["curves"])[0]})
    if curve_names:
        pick = st.selectbox("Curve", curve_names)
        have = [n for n, r in results.items() if pick in r["curves"]]
        chosen = st.multiselect("Results", have, default=have)
        if chosen:
            frames = [pd.DataFrame({"x": num(results[n]["curves"][pick]["x"]), "result": n,
                                    "y": num(results[n]["curves"][pick]["y"])}) for n in chosen]
            st.altair_chart(alt.Chart(pd.concat(frames, ignore_index=True)).mark_line(point=True).encode(
                x=X_ENC, y=alt.Y("y:Q", title="Value"), color=alt.Color("result:N", title=None)
            ).properties(height=340))