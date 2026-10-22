# Uplift Modeling for Email Targeting

> **Can we identify the customers who will buy because of an email, rather than those who would buy anyway—and can we do so when historical campaign data is biased?**

A marketing team has a limited number of customers it can contact. The challenge is not simply to predict who will purchase, but to identify whose purchasing decision can actually be changed by an email. This project investigates whether uplift modeling can identify those customers and whether propensity score matching can recover targeting performance when treatment assignment is no longer randomized.

Using the MineThatData email experiment, I compare uplift models on randomized data, deliberately introduce confounding into treatment assignment, and evaluate whether propensity score matching can mitigate its effects.

## The problem

A retailer cannot email every customer, and contacting someone is not necessarily valuable just because they are likely to buy. Some customers would purchase regardless of receiving an email; others might purchase only if they receive one. A conventional response model tends to prioritize both groups because it predicts who is likely to buy after being contacted, not whether the contact itself changes their behavior.

What the retailer really wants to know is: **how much more likely is each customer to purchase if they receive an email than if they do not?**

This is the idea behind uplift modeling:

```math
\operatorname{uplift}(x)
=
P(Y=1 \mid T=1,x)
-
P(Y=1 \mid T=0,x)
```

Here, \(T=1\) represents receiving an email, \(T=0\) represents receiving no email, and \(Y=1\) represents making a purchase within two weeks.

Uplift modeling distinguishes four conceptual customer groups:

- **Persuadables:** customers more likely to purchase when emailed. These are the primary targeting candidates.
- **Sure things:** customers likely to purchase regardless of the email. Contacting them may generate little incremental value.
- **Lost causes:** customers unlikely to purchase either way. They may be low-priority targets.
- **Sleeping dogs:** customers less likely to purchase when emailed. Contacting them may be counterproductive.

The difficulty is that we cannot directly observe what an individual customer would have done under both conditions. We observe either an emailed customer or a non-emailed customer, never both potential outcomes for the same person. Uplift models therefore estimate incremental effects from differences in outcomes across groups of customers.

This is relatively straightforward in a randomized experiment, where treatment and control groups are comparable on average. In real marketing campaigns, however, customers are often selected for contact based on their characteristics or previous behavior. Emailed and non-emailed customers then differ in ways that also affect purchasing. This is **confounding**, and it can make a model mistake pre-existing differences in purchase behavior for the effect of the email.

This project investigates whether uplift models can still rank customers effectively under such conditions, and whether propensity score matching (PSM) can reduce the damage caused by confounding.

## Why it matters

- **Predicting purchases is not the same as influencing them.** A customer who would buy anyway may be a good prediction but a poor marketing target. Uplift modeling aims to prioritize customers whose behavior can actually be changed.
- **Contact can have negative effects.** Emails consume attention and may involve promotional incentives. Radcliffe (2008), analyzing this dataset, identified segments in which the Women's email appeared to reduce spending. Targeting should therefore account for potential negative effects as well as positive ones.
- **Real-world campaign data is rarely perfectly randomized.** Marketing teams often decide whom to contact using customer attributes, purchase histories, or existing targeting rules. Understanding whether uplift models remain useful under these conditions is essential if they are to be applied beyond controlled experiments.

The central challenge is that a model can perform well on randomized data yet struggle when trained on historical campaigns in which treatment assignment is related to customer characteristics. This project uses a real randomized experiment to investigate that problem under controlled, simulated confounding.

## Approach

**Scenario A, randomized.** The original randomized dataset is used to benchmark the uplift models. Customers were assigned to the Men's email, the Women's email, or a no-email control group. Each email is evaluated as a separate binary treatment problem against the control group.

**Scenario B, confounded.** Treatment assignment is made non-random by selectively removing customers from the emailed group according to customer characteristics that also predict purchasing. The selection rule is based on the approach described in Hill (2011) and Ruf and Handrich (2026). **[Specify the exact selection rule and parameters.]**

Models are trained and evaluated under three conditions:

1. On the original randomized data.
2. On the confounded data without adjustment.
3. On the confounded data after propensity score matching.

The original randomized experiment provides a benchmark for assessing how much ranking performance is lost under confounding and how much, if any, can be recovered through matching.

**Propensity score matching.** Propensity scores are estimated using a generalized boosted model. One-to-one nearest-neighbor matching is used to pair treated and control customers with similar estimated probabilities of receiving the email. Covariate balance is assessed using standardized mean differences (SMDs), with an absolute SMD below 0.1 for every covariate as the prespecified target.

Matching can improve comparability on observed characteristics, but it cannot eliminate bias from unobserved confounders. It may also discard unmatched customers and reduce the effective sample size.

**Uplift models compared.**

- **Meta-learners:** S-, T-, X-, and R-learners, each using logistic regression, random forest, and XGBoost as base learners.
- **Tree-based models:** uplift random forest with KL-divergence, Euclidean-distance (ED), and chi-squared (CHI) split criteria, and a causal forest (**library: XXX**).

**Targeting baselines.**

- **Response model:** trained on emailed customers to estimate purchase propensity among treated customers.
- **Purchase propensity model:** trained on non-emailed customers to estimate purchase propensity without treatment.
- **Random targeting:** provides a reference for selection without a customer-level ranking model.

These baselines help test whether estimating incremental effects offers an advantage over ranking customers by their underlying likelihood of purchasing.

**Outcome.** Purchase (conversion) within two weeks is the primary outcome, and site visit is a secondary outcome. Spend is not modeled because a small number of customers account for most of the incremental spending in this dataset, making spend-based estimates particularly unstable.

**Treatment.** The dataset contains two email treatments and a control group. The Men's email versus control and the Women's email versus control are analyzed as separate binary treatment problems.

## Result

**The key questions are whether uplift modeling improves targeting over response propensity, how much performance is lost under confounding, and whether propensity score matching helps recover it.** Results will be reported separately for the Men's and Women's email comparisons.

- Improvement in incremental purchase response when targeting the top 30% of customers by uplift rather than response propensity: **XXX percentage points**.
- Proportion of randomized-data Qini performance recovered after PSM: **XXX%**, compared with **XXX%** without adjustment.

Success criteria, fixed before model evaluation:

1. On randomized data, the best meta-learner's Qini coefficient exceeds the uplift random forest's by at least XXX.
2. After PSM, every covariate has an absolute SMD below 0.1.
3. On confounded data, the best model after PSM reaches at least XXX% of its randomized-data Qini coefficient and exceeds the unadjusted model by at least XXX.
4. Targeting the top 30% by uplift captures at least XXX percentage points more incremental purchases than targeting the top 30% by response propensity.

These criteria should be interpreted as prespecified evaluation targets, not assumptions about which models will perform best.

### Model comparison

Qini coefficient, summarized over XXX held-out folds. Higher is better.

| Model | A: Randomized | B: Confounded, no adjustment | B: Confounded + PSM |
|---|---:|---:|---:|
| S-learner (XXX) | XXX | XXX | XXX |
| T-learner (XXX) | XXX | XXX | XXX |
| X-learner (XXX) | XXX | XXX | XXX |
| R-learner (XXX) | XXX | XXX | XXX |
| Uplift random forest (KL) | XXX | XXX | XXX |
| Uplift random forest (ED) | XXX | XXX | XXX |
| Uplift random forest (CHI) | XXX | XXX | XXX |
| Causal forest | XXX | XXX | XXX |
| Response model | XXX | XXX | XXX |
| Random targeting | XXX | XXX | XXX |

Results are reported separately for the Men's and Women's emails. **[Insert one table for each email comparison.]**

### Covariate balance

| Covariate | Absolute SMD before PSM | Absolute SMD after PSM |
|---|---:|---:|
| recency | XXX | XXX |
| history | XXX | XXX |
| mens | XXX | XXX |
| womens | XXX | XXX |
| newbie | XXX | XXX |
| zip_code | XXX | XXX |
| channel | XXX | XXX |

The objective is to determine whether matching improves comparability between treated and control customers on observed covariates. The prespecified balance criterion is an absolute SMD below 0.1 for every covariate.

### Targeting effect

**[Insert figure: accumulated incremental purchase rate by targeting percentile.]**

Plot the accumulated incremental purchase rate when targeting the top 10%, 20%, ..., 100% of customers, ranked by uplift model, response model, and purchase propensity model.

The key comparison is how much incremental purchase response each ranking captures at different campaign sizes, particularly when the retailer can contact only a small proportion of customers.

## How we tested it

- **Data:** 64,000 customers from the MineThatData Email Analytics and Data Mining Challenge (Hillstrom, 2008), including a randomized control group.
- **Benchmark:** the original randomized experiment provides the reference for evaluating the effects of simulated confounding. Radcliffe (2008) provides published context for the dataset's observed purchase uplift and its variability.
- **Confounding:** the selection rule is applied to the emailed group, leaving XXX treated and XXX control customers per comparison.
- **Evaluation:** nested cross-validation, with an inner loop for hyperparameter tuning and an outer loop for performance estimation. Models in Scenario B are also evaluated on randomized customers excluded from training, where applicable. **[Confirm the exact split, matching procedure, and leakage-prevention strategy.]**
- **Tuning:** Tree-structured Parzen Estimator search, with 50 trials per model, scored by Qini coefficient for uplift models and AUC for propensity models.
- **Comparison:** pairwise Wilcoxon signed-rank tests across outer folds, with runtime per trial recorded. The dependence between folds should be considered when interpreting statistical significance.
- **Uncertainty:** bootstrap intervals for Qini coefficients. Model differences should be assessed using paired uncertainty estimates where possible, rather than relying solely on overlap between separate confidence intervals.

The evaluation is designed to distinguish three questions: whether models rank customers effectively under randomization, how their performance changes under confounding, and whether matching mitigates that change.

## Limits of these results

- **Very few buyers.** The control group contains approximately 120 purchasers (122 in Radcliffe's analysis). With so few positive outcomes, individual treatment-effect estimates and model rankings may be noisy. Radcliffe reported that overall purchase uplift varied from 0.26 to 1.01 percentage points across 10% samples of the Men's email. Small differences between models may therefore be difficult to distinguish reliably.
- **The confounding is simulated.** The selection rule is a controlled approximation of non-random treatment assignment. Real campaign targeting rules are often more complex, and results may depend on the particular mechanism used to introduce confounding.
- **Only observed covariates can be balanced.** PSM cannot remove bias caused by unobserved confounders. Its effectiveness also depends on sufficient overlap between treated and control customers.
- **Limited feature set.** The available customer attributes may not capture all the factors influencing treatment assignment or purchase behavior. The exact number of covariates used should be confirmed and reported consistently.
- **Evaluation is at the group level, not the individual level.** Individual treatment effects cannot be directly observed. Ranking quality must be evaluated through aggregate metrics such as Qini curves and accumulated incremental response.
- **Purchase, not profit.** Email costs, margins, and incentive costs are not modeled. A higher incremental purchase rate does not necessarily translate into higher profitability.
- **One retailer, one two-week window, 2008 data.** The results may not generalize to other retailers, campaigns, customer populations, or outcome windows.
- **PSM discards data.** Unmatched customers are dropped, potentially reducing statistical power in an already low-signal setting.

## Where this departs from the papers

- **From Radcliffe (2008):** Radcliffe used a proprietary uplift package, bagged trees, and indicator models, and examined visit and spend outcomes. This project uses open-source meta-learners and tree-based uplift models, focuses primarily on purchase probability, and adds a confounded treatment-assignment scenario. The modeling and evaluation differences mean that results should not be compared as if they came from the same pipeline.
- **From Ruf and Handrich (2026):** Their study uses semi-synthetic data, combining real customer characteristics with simulated treatment and outcomes. Here, the observed outcomes come from a real randomized email experiment, and treatment assignment is modified to introduce confounding. The original randomized data therefore provides a reference for evaluating the consequences of that modification. This project also includes a causal forest and uses a different dataset and outcome.

## Data

| Attribute | Detail |
|---|---|
| Source | MineThatData E-Mail Analytics and Data Mining Challenge (Hillstrom, 2008) |
| Download | XXX |
| Customers | 64,000 |
| Men's email | 21,307 |
| Women's email | 21,387 |
| No email (control) | 21,306 |
| Assignment | Randomized |
| Outcome window | Two weeks after the email |
| Outcomes | Visit, conversion (purchase), spend |
| Covariates | recency, history, mens, womens, newbie, zip_code, channel |
| Excluded feature | history_segment, a binned version of history |

The two email treatments are analyzed separately against the control group. The covariate list above contains seven features; confirm whether an eighth feature is included in the actual modeling pipeline.

## Repository

```text
data/        Raw data (not tracked in Git) and derived confounded datasets
src/         Confounding, matching, models, and evaluation
notebooks/   Exploratory analysis
docs/        Design notes and prespecified success criteria
outputs/     Metrics, Qini curves, balance tables, and figures
