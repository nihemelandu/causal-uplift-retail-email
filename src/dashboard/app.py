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


# ---- Q1 layout -------------------------------------------------------------------
Q1_GROUPS = ["No email", "Women's email", "Men's email"]
Q1_COLORS = ["#9e9e9e", "#e377c2", "#1f77b4"]   # grey baseline, one colour per campaign
Q1_MEASURES = {                                  # outcome -> (title, axis format, label format)
    "visit": ("Visit rate", "%", ".1%"),
    "conversion": ("Purchase rate", "%", ".2%"),
    "spend": ("Spend per customer", "$.2f", "$.2f"),
}
Q1_COMPARISONS = {
    "mens_vs_control": "Men's email vs. no email",
    "womens_vs_control": "Women's email vs. no email",
    "mens_vs_womens": "Men's email vs. Women's email",
}


def q1_group_means(m: dict, outcome: str) -> list:
    """Group means in Q1_GROUPS order: no email, Women's, Men's."""
    return [m[f"{outcome}.mens_vs_control.control"],
            m[f"{outcome}.womens_vs_control.treatment"],
            m[f"{outcome}.mens_vs_control.treatment"]]


def q1_measure_chart(df: pd.DataFrame, column: str, title: str, axis_fmt: str, label_fmt: str,
                     show_legend: bool = False):
    legend = alt.Legend(title=None, orient="top", symbolType="square") if show_legend else None
    base = alt.Chart(df).encode(
        x=alt.X("group:N", sort=Q1_GROUPS, title=None, axis=alt.Axis(labels=False, ticks=False)),
        y=alt.Y(f"{column}:Q", title=None, scale=alt.Scale(domain=[0, df[column].max() * 1.15]),
                axis=alt.Axis(format=axis_fmt)),
        color=alt.Color("group:N", scale=alt.Scale(domain=Q1_GROUPS, range=Q1_COLORS), legend=legend),
    )
    bars = base.mark_bar()
    labels = base.mark_text(dy=-8, fontWeight="bold", color="black").encode(
        text=alt.Text(f"{column}:Q", format=label_fmt))
    return (bars + labels).properties(title=title, width=190, height=280)


def q1_uplift_table(m: dict) -> pd.DataFrame:
    """One row per measure and comparison: uplift, 95% interval, p-value, in the units a reader thinks in."""
    rows = []
    for outcome, (name, _, _) in Q1_MEASURES.items():
        if outcome == "spend":
            f = lambda v: f"{'+' if v >= 0 else '-'}${abs(v):.2f}"
        else:
            f = lambda v: f"{v * 100:+.2f} pp"
        for key, label in Q1_COMPARISONS.items():
            p = m[f"{outcome}.{key}.p_value"]
            rows.append({"Measure": name, "Comparison": label,
                         "Uplift": f(m[f"{outcome}.{key}.diff"]),
                         "95% confidence interval": f"[{f(m[f'{outcome}.{key}.diff_ci_low'])}, "
                                                    f"{f(m[f'{outcome}.{key}.diff_ci_high'])}]",
                         "p-value": "<0.001" if p < 0.001 else f"{p:.3f}"})
    return pd.DataFrame(rows).set_index(["Measure", "Comparison"])


Q1_BALANCE_ROWS = {   # row key -> (label, kind): "mean" rows show mean (SD); "share" rows show a percentage
    "recency": ("Months since last purchase, mean (SD)", "mean"),
    "history": ("Spend in the past year, $, mean (SD)", "mean"),
    "mens": ("Bought men's merchandise in the past year", "share"),
    "womens": ("Bought women's merchandise in the past year", "share"),
    "newbie": ("New customer in the past twelve months", "share"),
    "zip_code_Rural": ("Zip code: rural", "share"),
    "zip_code_Surburban": ("Zip code: suburban", "share"),
    "zip_code_Urban": ("Zip code: urban", "share"),
    "channel_Multichannel": ("Channel: multichannel", "share"),
    "channel_Phone": ("Channel: phone", "share"),
    "channel_Web": ("Channel: web", "share"),
}


def q1_relative_table(m: dict) -> pd.DataFrame:
    """Relative uplift (uplift divided by the comparison group's average) with its 95% interval."""
    rows = []
    for outcome, (name, _, _) in Q1_MEASURES.items():
        for key, label in Q1_COMPARISONS.items():
            k = f"{outcome}.{key}.rel_diff_pct"
            rows.append({"Measure": name, "Comparison": label,
                         "Relative uplift": f"{m[k]:+.1f}%",
                         "95% confidence interval": f"[{m[k + '_ci_low']:+.1f}%, {m[k + '_ci_high']:+.1f}%]"})
    return pd.DataFrame(rows).set_index(["Measure", "Comparison"])


def q1_analysis_notes(m: dict) -> list:
    """Lines stating the primary outcome and how multiplicity was handled."""
    lines = []
    primary = [name.lower() for k, (name, _, _) in Q1_MEASURES.items() if m.get(f"primary.{k}") == 1]
    if primary:
        others = [name.lower() for k, (name, _, _) in Q1_MEASURES.items() if m.get(f"primary.{k}") != 1]
        lines.append(f"**Primary outcome:** {primary[0]}, the measure closest to campaign profitability. "
                     f"{' and '.join(others).capitalize()} are secondary.")
    if "bonferroni_alpha" in m:
        alpha = m["bonferroni_alpha"]
        tests = [(name, label, m[f"{k}.{c}.p_value"]) for k, (name, _, _) in Q1_MEASURES.items()
                 for c, label in Q1_COMPARISONS.items()]
        failed = [(n, lab, p) for n, lab, p in tests if p >= alpha]
        text = (f"**Multiplicity:** Bonferroni correction. Each measure has three comparisons, so a difference "
                f"counts as significant when p < {alpha:.4f} (0.05 / {round(0.05 / alpha)}). ")
        if failed:
            text += f"{len(tests) - len(failed)} of {len(tests)} comparisons meet this. " + " ".join(
                f"{lab} on {n.lower()} (p = {p:.3f}) does not." for n, lab, p in failed)
        else:
            text += f"All {len(tests)} comparisons meet this."
        lines.append(text)
    return lines


def q1_balance_table(m: dict) -> pd.DataFrame:
    """Baseline table: each pre-email characteristic by group, and the largest standardized difference."""
    rows = []
    for key, (label, kind) in Q1_BALANCE_ROWS.items():
        def cell(arm):
            mean = m[f"balance.{key}.{arm}"]
            return f"{mean:.2f} ({m[f'balance.{key}.sd_{arm}']:.2f})" if kind == "mean" else f"{mean * 100:.1f}%"
        smd = max(abs(m[f"balance.{key}.smd_womens"]), abs(m[f"balance.{key}.smd_mens"]))
        rows.append({"Characteristic": label, "No email": cell("control"), "Women's email": cell("womens"),
                     "Men's email": cell("mens"), "Largest standardized difference": f"{smd:.3f}"})
    return pd.DataFrame(rows).set_index("Characteristic")


def render_q1(res: dict):
    m = res["metrics"]

    # 1. The answer
    winners = {name: ("Men's" if m[f"{k}.mens_vs_womens.diff"] > 0 else "Women's")
               for k, (name, _, _) in Q1_MEASURES.items()}
    if len(set(winners.values())) == 1:
        w = next(iter(winners.values()))
        loser = "Women's" if w == "Men's" else "Men's"
        st.success(f"**{w} email performed best:** it beat the {loser} email on visit rate, "
                   "purchase rate and spend per customer.")
    else:
        st.info("**Mixed result:** " + "; ".join(f"the {w} email led on {n.lower()}" for n, w in winners.items()))

    unclear = [name.lower() for k, (name, _, _) in Q1_MEASURES.items()
               if m[f"{k}.mens_vs_womens.diff_ci_low"] <= 0 <= m[f"{k}.mens_vs_womens.diff_ci_high"]]
    if unclear:
        st.caption("The gap between the two emails on " + " and ".join(unclear) +
                   " could be chance: its confidence interval includes zero.")
    else:
        st.caption("The gap between the two emails is clear on all three measures.")

    # 2. The evidence: one bar chart per measure
    panels = []
    for i, (outcome, (title, axis_fmt, label_fmt)) in enumerate(Q1_MEASURES.items()):
        df = pd.DataFrame({"group": Q1_GROUPS, outcome: q1_group_means(m, outcome)})
        panels.append(q1_measure_chart(df, outcome, title, axis_fmt, label_fmt, show_legend=(i == 0)))
    st.altair_chart(alt.hconcat(*panels))

    # 3. What each email added, and how far to trust it
    st.markdown("**What each email added**")
    st.dataframe(q1_uplift_table(m))
    st.caption("Uplift is the difference between the two groups. Visit and purchase rates are in percentage "
               "points (pp); spend is dollars per customer emailed. Spend is about 99% zeros with a few large "
               "purchases, so treat its intervals and p-values as approximate.")

    # 4. Relative uplift (CONSORT item 17b: absolute and relative effect sizes for binary outcomes)
    st.markdown("**What each email added, relative to the comparison group**")
    st.dataframe(q1_relative_table(m))
    st.caption("Relative uplift is the uplift divided by the comparison group's average.")

    # 5. How the analysis was set up: primary outcome and multiplicity
    for line in q1_analysis_notes(m):
        st.markdown(line)

    # 6. Were the groups alike before the emails? (CONSORT item 15: baseline table, no significance tests)
    if any(k.startswith("balance.") for k in m):
        st.markdown("**Were the groups alike before the emails?**")
        st.dataframe(q1_balance_table(m))
        st.caption("Each cell is the group average (standard deviation) or the share of customers. The "
                   "standardized difference is the gap between an email group and the no-email group divided by "
                   "the pooled standard deviation; below about 0.1 is conventionally treated as balanced. No "
                   "significance tests are shown: with random allocation, any difference at the start is chance "
                   "(CONSORT 2010).")

    # 7. Analyst details
    with st.expander("Technical details"):
        st.write(f"Customers: {m['n_mens']:,} Men's, {m['n_womens']:,} Women's, {m['n_control']:,} no email.")
        st.write(f"Sample-ratio check against an equal three-way split: p = {m['srm_p_value_equal_thirds']:.3f}.")
        st.write(res["notes"])


RENDERERS = {"q1": render_q1}  # add RENDERERS["q3"] = render_q3 etc. as each layout is decided


# ---- page ----------------------------------------------------------------------------
st.title("Who should we email?")
st.caption("Finding the customers an email actually persuades, not those who would buy anyone.")

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
    if res["notes"] and choice not in RENDERERS:  # custom layouts place the notes themselves
        st.caption(res["notes"])
    RENDERERS.get(choice, render_default)(res)