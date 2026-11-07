"""dashboard/app.py - Sprint 1 dashboard.

Depends only on evaluation/base.py (EvaluationResult). It reads results/*.json, where each file is
one EvaluationResult.to_dict(), and renders whatever metrics and curves it finds. It never trains,
scores or evaluates anything, and it names no specific evaluator or metric.
"""
import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # repo root, so `evaluation` can be imported
from evaluation.base import EvaluationResult  # noqa: E402

RESULTS_DIR = ROOT / "results"

st.set_page_config(page_title="Who should we email?", layout="wide")


@st.cache_data(ttl=300)
def load_results(results_dir: str = str(RESULTS_DIR)):
    """Return ({file name: EvaluationResult as dict}, {file name: error message})."""
    ok, bad = {}, {}
    for path in sorted(Path(results_dir).glob("*.json")):
        try:
            ok[path.stem] = EvaluationResult.from_dict(json.loads(path.read_text())).to_dict()
        except Exception as e:  # noqa: BLE001 - one bad file must not take the page down
            bad[path.name] = str(e)
    return ok, bad


def fmt(v) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, int):
        return f"{v:,}"
    if isinstance(v, float):
        return f"{v:.4g}"
    return str(v)


st.title("Who should we email?")
st.caption("Finding the customers an email actually persuades, not those who would buy anyway.")

results, errors = load_results()
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

# ---- metrics: every scalar in the result, no names assumed ---------------------
st.markdown("**Metrics**")
items = list(res["metrics"].items())
if not items:
    st.write("This result has no metrics.")
for i in range(0, len(items), 4):
    for col, (key, value) in zip(st.columns(4), items[i:i + 4]):
        col.metric(key, fmt(value))

# ---- curves: curves that share the same x values are drawn on one chart --------
groups = {}
for cname, c in res["curves"].items():
    groups.setdefault(tuple(c["x"]), {})[cname] = c["y"]
for x, series in groups.items():
    st.markdown("**" + "  /  ".join(series) + "**")
    st.line_chart(pd.DataFrame(series, index=list(x)))

# ---- all results side by side ---------------------------------------------------
st.subheader("All results")
st.dataframe(pd.DataFrame([{"result": n, "evaluator": r["evaluator"], **r["metrics"]}
                           for n, r in results.items()]), hide_index=True)