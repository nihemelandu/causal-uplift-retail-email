# %% Cell 1: Import libraries

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json

from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, cross_val_score, KFold

from meta_learners import SLearner
from evaluation.metrics import QiniEvaluator


# %% Cell 2: Load data
print("__file__:", __file__)
fname = "Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv"
dfname = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / fname

data = pd.read_csv(dfname)

print(f"Loaded {len(data)} rows from {dfname}")
print (data.head())

# %% Cell 3: Explore data
data.segment.value_counts()

# %% Cell 4: Build models

df = data[data.segment.isin(["Mens E-Mail", "No E-Mail"])].reset_index(drop=True)
t = (df.segment == "Mens E-Mail").astype(int).to_numpy()
y = df["conversion"].to_numpy()
X = df[["recency", "history", "mens", "womens", "newbie"]].copy()
dummies = pd.get_dummies(df[["zip_code", "channel"]], drop_first=True).astype(int)
X = pd.concat([X, dummies], axis=1)

# 80/20 split; all three arrays are split together so rows stay aligned
X_train, X_test, t_train, t_test, y_train, y_test = train_test_split(
    X, t, y, test_size=0.2, stratify=t, random_state=42
)

# Sanity check: the treatment probability p should be close to 0.5
print("p (all):  ", t.mean())
print("p (train):", t_train.mean())
print("p (test): ", t_test.mean())

Slearner_rf = SLearner(base_learner=RandomForestClassifier(n_estimators=100, random_state=42))
Slearner_rf.fit(X_train, t_train, y_train)

scores_train = Slearner_rf.predict_uplift(X_train)
scores_test = Slearner_rf.predict_uplift(X_test)

# %% Cell 5: Analyze uplift scores
print("========== ARRAY OVERVIEW ==========")
print(f"Shape: {scores_test.shape}")
print(f"Size: {scores_test.size:,}")
print(f"Data type: {scores_test.dtype}")

print("\n========== STATISTICS ==========")
print("Minimum:", np.min(scores_test))
print("Maximum:", np.max(scores_test))
print("Mean:", np.mean(scores_test))
print("Median:", np.median(scores_test))
print("Standard deviation:", np.std(scores_test))
print("25th percentile:", np.percentile(scores_test, 25))
print("75th percentile:", np.percentile(scores_test, 75))

print("\n========== VALUE DISTRIBUTION ==========")
total = scores_test.size
zeros = np.count_nonzero(scores_test == 0)
nonzeros = np.count_nonzero(scores_test)
print("Total elements:", total)
print("Zeros:", zeros)
print("Nonzeros:", nonzeros)
print("Percentage zeros:", zeros / total * 100)

print("\n========== MOST FREQUENT VALUES ==========")
values, counts = np.unique(scores_test, return_counts=True)
indices = np.argsort(values)[::-1][:10]

for i in indices:
    print(f"{values[i]}: {counts[i]:,}")

# %% Cell 6: Evaluate and Visualize performance

qini_ev = QiniEvaluator()
res_test = qini_ev.evaluate(scores_test, y_test, t_test)
res_train = qini_ev.evaluate(scores_train, y_train, t_train)

results_dir = Path(__file__).resolve().parent.parent.parent / "results"   # adjust to your repo root
results_dir.mkdir(exist_ok=True)
for label, res in [("test", res_test), ("train", res_train)]:
    path = results_dir / f"s_learner_rf__{label}__QiniEvaluator.json"
    path.write_text(json.dumps(res.to_dict(), indent=2, allow_nan=False))
    print("saved", path)

# %% Cell 7: plot Qini curve    

def plot_qini(res, label, ax):
    c = res.curves
    x = [0.0] + c["qini"]["x"]
    y = [0.0] + c["qini"]["y"]            # the curve starts at the origin
    lo = [0.0] + c["qini_ci_low"]["y"]
    hi = [0.0] + c["qini_ci_high"]["y"]
    ax.plot(x, y, marker="o", label=label)
    ax.fill_between(x, lo, hi, alpha=0.2)

fig, ax = plt.subplots()           # creates the figure and the axis
plot_qini(res_test, "test", ax)    # draws the test curve on that axis
plot_qini(res_train, "train", ax)  # draws the train curve on the same axis

ax.set_xlabel("Share of population treated (ranked by predicted uplift)")
ax.set_ylabel("Qini value (incremental gain)")
ax.legend()
plt.show()

# %%
