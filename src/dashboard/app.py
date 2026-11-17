"""dashboard/app.py - Sprint 1 dashboard.

Depends only on evaluation/base.py (EvaluationResult). It reads results/*.json, where each file is
one EvaluationResult.to_dict(), and renders whatever metrics and curves it finds. It never trains,
scores or evaluates anything, and it names no specific evaluator.

The sidebar lists the eight questions of Hillstrom's challenge. A result file belongs to a question
when its name starts with the question key and an underscore (q1_effect_estimates.json -> Q1).
Each question has its own layout: add a function to RENDERERS; questions without one use render_default.

Naming conventions it understands (so any evaluator can use them):
    a metric or curve called  X  with companions  X_ci_low  and  X_ci_high
        -> metrics are shown in an interval table; curves are drawn as a line with a shaded band.
    metrics called  table.row.column  (exactly two dots)
        -> one table per `table`, one row per `row`; a column X with companions X_ci_low / X_ci_high
           gets an extra "X CI" column.
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

# results/ inside the repo; falls back to the folder above the repo if that is where it lives
RESULTS_DIR = ROOT / "results" if (ROOT / "results").is_dir() else ROOT.parent / "results"
CI_LOW, CI_HIGH = "_ci_low", "_ci_high"

# Hillstrom's eight questions. Result files are matched to a question by the key prefix.
QUESTIONS = {
    "q1": "Q1. Which campaign performed best?",
    "q2": "Q2. Incremental sales per customer",
    "q3": "Q3. The best 10,000 customers to email",
    "q4": "Q4. The 10,000 customers to suppress",
    "q5": "Q5. Performance across customer segments",
    "q6": "Q6. Performance across metrics",
    "q7": "Q7. Anomalies and odd findings",
    "q8": "Q8. Who gets the Men's and who gets the Women's version",
}

st.set_page_config(page_title="Who should we email?", layout="wide")


# ---- helpers ---------------------------------------------------------------------
def folder_signature(results_dir=RESULTS_DIR) -> tuple:
    """Changes whenever a result file is added, removed or modified. Not cached, so a new file shows
    up on the next rerun; the cache on load_results below is keyed on it and never goes stale."""
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


def table_row(cols: dict) -> dict:
    """cols = {column: value}. A column X with X_ci_low / X_ci_high gets an extra 'X CI' column."""
    row = {}
    for c, v in cols.items():
        if c.endswith((CI_LOW, CI_HIGH)) and c.rsplit("_ci_", 1)[0] in cols:
            continue
        row[c] = fmt(v)
        if c + CI_LOW in cols and c + CI_HIGH in cols:
            row[c + " CI"] = f"[{fmt(cols[c + CI_LOW])}, {fmt(cols[c + CI_HIGH])}]"
    return row


# ---- building blocks for layouts ------------------------------------------------------
def render_tables(metrics: dict):
    """Metrics named 'table.row.column' become one table per `table`, one row per `row`."""
    tables = {}
    for k, v in metrics.items():
        t, r, c = k.split(".")
        tables.setdefault(t, {}).setdefault(r, {})[c] = v
    for t, rows in tables.items():
        st.markdown(f"**{t}**")
        st.dataframe(pd.DataFrame([{"comparison": r, **table_row(cols)} for r, cols in rows.items()]),
                     hide_index=True)


def render_metrics(metrics: dict):
    """Plain metrics as cards (four per row); metrics with CI companions in an interval table."""
    main_m, ci_m = split_ci(metrics)
    plain = [k for k in main_m if k not in ci_m]
    if plain:
        st.markdown("**Metrics**")
        for i in range(0, len(plain), 4):
            for col, key in zip(st.columns(4), plain[i:i + 4]):
                col.metric(key, fmt(metrics[key]))
    if ci_m:
        st.markdown("**Estimates with intervals**")
        rows = [{"metric": k, "estimate": sig(metrics[k]), "ci_low": sig(metrics[lo]), "ci_high": sig(metrics[hi])}
                for k, (lo, hi) in ci_m.items()]
        st.dataframe(pd.DataFrame(rows), hide_index=True)
        st.caption("Intervals describe uncertainty in each estimate. Whether a ranking beats random targeting is a "
                   "different question: compare the curve with a random-targeting reference, not with zero. "
                   "If an evaluator reports several intervals, treat them as pointwise.")


def render_curves(curves: dict):
    """Curves sharing the same x values go on one chart."""
    main_c, ci_c = split_ci(curves)
    groups = {}
    for n in main_c:
        groups.setdefault(tuple(curves[n]["x"]), []).append(n)
    for names in groups.values():
        st.markdown("**" + "  /  ".join(names) + "**")
        st.altair_chart(curve_chart(curves, names, {n: ci_c[n] for n in names if n in ci_c}))


def render_compare(results: dict):
    """Overlay one named curve from several results."""
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


# ---- layouts: one function per question ----------------------------------------------
def render_default(res: dict):
    """Tables for dotted metric names, cards and interval table for the rest, then curves."""
    dotted = {k: v for k, v in res["metrics"].items() if k.count(".") == 2}
    flat = {k: v for k, v in res["metrics"].items() if k not in dotted}
    if dotted:
        render_tables(dotted)
    render_metrics(flat)
    if not res["metrics"]:
        st.write("This result has no metrics.")
    render_curves(res["curves"])


RENDERERS = {}  # e.g. RENDERERS["q3"] = render_q3, added when that question's layout is decided


# ---- page ----------------------------------------------------------------------------
st.title("Who should we email?")
st.caption("Finding the customers an email actually persuades, not those who would buy anyway.")

results, errors = load_results(folder_signature())
for fname, msg in errors.items():
    st.warning(f"Could not read `{fname}`: {msg}")

choice = st.sidebar.selectbox("Question", list(QUESTIONS), format_func=QUESTIONS.get)
files = [n for n in results if n.startswith(choice + "_")]

st.subheader(QUESTIONS[choice])
if not files:
    st.info("No result for this question yet. Save its EvaluationResult as JSON in the results/ folder "
            f"with a file name starting `{choice}_`.")
else:
    name = files[0] if len(files) == 1 else st.sidebar.selectbox("Result", files)
    res = results[name]
    st.caption(f"{res['evaluator']}  ·  {name}")
    if res["notes"]:
        st.caption(res["notes"])
    RENDERERS.get(choice, render_default)(res)

if len(results) > 1:
    render_compare(results)