# %% Cell 1: Import libraries

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, cross_val_score, KFold

from meta_learners import SLearner


# %% Cell 2: Load data
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
X = df[["recency", "history", "mens", "womens", "newbie"]].copy()
dummies = pd.get_dummies(df[["zip_code", "channel"]], drop_first=True).astype(int)
X = pd.concat([X, dummies], axis=1)

Slearner_rf = SLearner(base_learner=RandomForestClassifier(n_estimators=100, random_state=42))
Slearner_rf._fit(X, t, df["conversion"].to_numpy())
Slearner_rf_scores = Slearner_rf._predict_uplift(X)

# %% Cell 5: Analyze uplift scores
print("========== ARRAY OVERVIEW ==========")
print(f"Shape: {Slearner_rf_scores.shape}")
print(f"Size: {Slearner_rf_scores.size:,}")
print(f"Data type: {Slearner_rf_scores.dtype}")

print("\n========== STATISTICS ==========")
print("Minimum:", np.min(Slearner_rf_scores))
print("Maximum:", np.max(Slearner_rf_scores))
print("Mean:", np.mean(Slearner_rf_scores))
print("Median:", np.median(Slearner_rf_scores))
print("Standard deviation:", np.std(Slearner_rf_scores))
print("25th percentile:", np.percentile(Slearner_rf_scores, 25))
print("75th percentile:", np.percentile(Slearner_rf_scores, 75))

print("\n========== VALUE DISTRIBUTION ==========")
total = Slearner_rf_scores.size
zeros = np.count_nonzero(Slearner_rf_scores == 0)
nonzeros = np.count_nonzero(Slearner_rf_scores)
print("Total elements:", total)
print("Zeros:", zeros)
print("Nonzeros:", nonzeros)
print("Percentage zeros:", zeros / total * 100)

print("\n========== MOST FREQUENT VALUES ==========")
values, counts = np.unique(Slearner_rf_scores, return_counts=True)
indices = np.argsort(counts)[::-1][:10]

for i in indices:
    print(f"{values[i]}: {counts[i]:,}")

# %% Cell 6: Visualize data

plt.hist(data, bins=30)
plt.show()