# Who Should We Email? Finding the Customers an Email Actually Persuades

> **Can we identify the customers who will buy because of an email, rather than those who would buy anyway—and can we do so when historical campaign data is biased?**

---

## 1. The short version

A company wants to send a marketing email, but can only email some of its customers. The obvious approach is to email the people most likely to buy. That is wasteful, because many of those people would have bought anyway.

What the company really wants to know is: **who buys *because* we emailed them?** Those customers are the ones worth emailing. This project builds and tests a way to find them, using a real email experiment run by a retailer.

The project also tackles a second, harder problem. Companies rarely have clean experimental data. Past emails were usually sent to customers picked for some reason, such as being frequent shoppers, and that makes the data misleading. We test whether a standard statistical fix, called **propensity score matching**, can repair the damage.

## 2. The problem

Imagine two customers who both buy after receiving an email:

- **Ana** was going to buy that week no matter what. The email changed nothing.
- **Ben** only bought because the email reminded him.

Both look like "email successes", but only Ben was worth emailing. A tool that predicts *who will buy* cannot tell them apart. What we need is a tool that predicts **how much the email changes each person's chance of buying**. This is called **uplift**.

Customers fall into four types:

| Type | What happens | Worth emailing? |
|---|---|---|
| **Persuadables** | Buy if emailed, don't if not | **Yes, the target** |
| **Sure things** | Buy either way | Not needed |
| **Lost causes** | Don't buy either way | Not useful |
| **Sleeping dogs** | The email puts them off | **No, it backfires** |

We can never see which type a person is, because each customer either gets the email or doesn't. We can't watch the same person both ways. So uplift tools work from **groups**: they compare what happened to similar customers who were emailed with what happened to those who weren't.

### Why biased data is a problem

Comparing emailed and non-emailed customers only works if the two groups are alike apart from the email. The cleanest way to get alike groups is to decide by coin flip who is emailed. That is a **randomized experiment**.

Real campaigns usually don't work that way. If a company emails mostly its loyal customers, then emailed customers buy more because they are loyal, not because of the email. The tool mistakes loyalty for persuasion. This mix-up is called **confounding**.

## 3. What this project does

We use a real randomized experiment (the **MineThatData** email test) as a gold-standard benchmark, then break it on purpose and see what happens.

1. **Randomized (the benchmark).** Train the tools on the clean experimental data and see how well they find the persuadable customers.
2. **Biased.** Deliberately remove some emailed customers, using rules that also relate to buying habits. This imitates a company that chose who to email. Train the same tools on this biased data.
3. **Biased + matching.** Apply propensity score matching to the biased data, which pairs each emailed customer with a similar non-emailed one, and train the tools again.
4. **Fair-size check.** Matching throws data away. To avoid blaming matching for what is really just "less data", we also train on a clean randomized dataset of the same smaller size.

Because we know what the clean experiment says, we can measure **how much the bias hurts** and **how much matching wins back**.

The question we answer for each campaign (the Men's-products email and the Women's-products email):

1. Do uplift tools find the right customers better than the usual "who is likely to buy" approach?
2. Do standard prediction tools used in combination (**meta-learners**) do as well as specialist uplift methods?
3. How much worse does the ranking get when the data is biased?
4. How much of that loss does matching recover?

## 4. The data

A real test by an online retailer in 2008, shared publicly by Kevin Hillstrom.

- **64,000 past customers**, split at random: about 21,300 got an email about **men's** products, about 21,400 got one about **women's** products, and about 21,300 got no email.
- Everyone was tracked for **two weeks**. We look at whether they **bought** (our main measure) and whether they **visited the website** (a second measure).
- We know a few things about each customer beforehand: how recently they bought, how much they spent in the past year, whether they bought men's or women's items, whether they are new, where they live (urban, suburban or rural) and which channel they buy through.
- We do **not** model how much customers spend. A tiny number of big spenders account for most of the extra spending, which makes spending too unstable to model.

What the published results of this test show (Radcliffe, 2008):

| | Customers who bought | Extra buyers per 1,000 emailed |
|---|---|---|
| No email | about 1 in 175 (0.57%) | - |
| Men's email | about 1 in 80 (1.25%) | about 7 |
| Women's email | about 1 in 114 (0.88%) | about 3 |

## 5. Why this is hard

Very few people buy. In the no-email group, only about **121 customers** bought anything. Our tests will split the data into slices, and each test slice will hold only about a dozen buyers among the non-emailed and 20-30 among the emailed. With so few buyers:

- A tool that knows nothing can look slightly good **by luck alone**.
- One test slice cannot reliably tell a good tool from a mediocre one. For a group with average buying rates, a single slice has an uncertainty of about **±1.0 percentage point** around the true extra-purchase rate, compared with an average effect of 0.68 for the Men's email. Combining all the slices shrinks this to about ±0.33.
- Published earlier work found the overall effect of the Men's email swinging from 0.26 to 1.01 percentage points across random tenths of the data.

So this project treats **uncertainty as part of the answer**. Every score will be shown with a margin of error, and we will report "can't tell these two apart" when that is the honest answer. These numbers come from the published rates and will be recomputed from the real data in Sprint 2.

## 6. What counts as success

We decide what success means **before** seeing any results, so we can't move the goalposts. The exact thresholds will be set in Sprint 2 and locked with a dated tag in Git (`criteria-v1`) before any final scoring.

We will have succeeded in answering the questions if we can show, with margins of error:

1. **Standard tools are competitive.** The best meta-learner does at least as well as the best specialist method, by more than luck would explain.
2. **Matching makes the groups alike.** After matching, emailed and non-emailed customers look similar on every characteristic we have.
3. **We can measure the damage and the repair.** First we check that the bias really did make the tools worse. If it didn't, we report that and make no claims about matching. If it did, we measure what share of the lost ability matching recovers.
4. **Targeting by persuasion beats targeting by purchase likelihood.** When only the top 30% of customers can be emailed, choosing them by uplift wins more extra purchases than choosing the most likely buyers.

A "win" always means the advantage is **larger than random luck would produce**, judged on the same customers for both methods. A disappointing result is still a valid result.

## 7. Glossary

| Term | Meaning |
|---|---|
| **Uplift** | How much an email changes a customer's chance of buying. |
| **Randomized experiment** | Who gets the email is decided by chance, so the two groups are comparable. |
| **Control group** | The customers who got no email, used as the comparison. |
| **Confounding** | Emailed and non-emailed customers differ for reasons other than the email, which distorts the comparison. |
| **Propensity score** | The chance a customer was emailed, given what we know about them. |
| **Propensity score matching (PSM)** | Pairing each emailed customer with a similar non-emailed one, so the comparison is fairer. |
| **Balance check (SMD)** | A score for how similar two groups are on a characteristic. Under 0.1 means "well balanced". |
| **Meta-learner** | A recipe for estimating uplift using ordinary prediction models, with no special software. |
| **Uplift random forest / causal forest** | Specialist tree-based methods built to estimate uplift directly. |
| **Response model** | The "usual" approach: predicts who will buy after being emailed, not whether the email caused it. |
| **Qini score** | A score for how good a ranking is. Rank customers from most to least persuadable and email from the top down, then track extra purchases created. A good ranking climbs above the straight line you'd get by emailing at random. The Qini score is the area between the two. |
| **Noise floor** | The score a ranking with no real skill reaches by luck. A tool has to beat it. |
| **Cross-validation** | Repeatedly hiding part of the data, training on the rest and testing on the hidden part. |
| **Bootstrap** | Re-sampling the data many times to see how much a result would wobble. |
| **Positivity (overlap)** | Every kind of customer must have some chance of being emailed and some of not, otherwise there is nothing to compare. |

## 8. Technical details

<details>
<summary><strong>Scenarios and confounding mechanism</strong></summary>

| Scenario | Training data | Test data |
|---|---|---|
| **A** Randomized | Full randomized training folds | Randomized held-out fold |
| **A′** Size-matched | Random subsample of A, same size as C | Same |
| **B** Confounded | Confounded training folds, no adjustment | Same |
| **C** Confounded + PSM | Confounded training folds after matching | Same |

Emailed customers are retained with probability

```math
\pi(x) = \operatorname{clip}\!\big(\sigma(\gamma_0 + \gamma^\top z(x)),\ 0.1,\ 0.9\big)
```

where $z(x)$ are standardized variables chosen because they predict purchase. Control customers are all retained. Bounded probabilities preserve overlap. $\gamma$ is calibrated so the unadjusted treated-versus-control difference is biased by a prespecified amount in the training data, using no test outcomes. Final specification: `docs/confounding.md` (Sprint 2). The approach follows Hill (2011) and Ruf and Handrich (2026).

</details>

<details>
<summary><strong>Matching, models and baselines</strong></summary>

- **PSM:** propensity scores from a generalized boosted model, one-to-one nearest-neighbor matching. Caliper and replacement settings in `docs/matching.md`. SMDs reported per encoded covariate level and per campaign.
- **Meta-learners:** S, T, X, R with logistic regression, random forest and XGBoost base learners.
- **Tailored trees:** uplift random forest (KL, ED, CHI splits) and a causal forest (library to be confirmed).
- **Baselines:** response model (trained on emailed customers), purchase propensity model (trained on control customers), random targeting.

</details>

<details>
<summary><strong>Evaluation protocol</strong></summary>

- **Splits and leakage:** split first, stratified by arm and outcome. Confounding and matching are applied to training data only. Every scenario is scored on the full randomized held-out fold, never only on removed customers.
- **Tuning:** nested cross-validation. In B and C the inner loop uses only confounded or matched data. Hyperopt TPE, trial budget set after a timing benchmark (target 50), scored by Qini (uplift models) or AUC (propensity models).
- **Qini:** with customers sorted by score, $\text{Qini}(\phi) = n^{T}_{1}(\phi)/N_T - n^{C}_{1}(\phi)/N_C$. $Q$ is the area between the curve and the random line.
- **Targeting metric:** uplift within the top $k$% ($k = 10, \dots, 100$), headline $k = 30$.
- **Primary inference:** pooled out-of-fold predictions, paired bootstrap over customers (at least 1,000 resamples), repeated cross-validation across seeds for stability.
- **Secondary inference:** pairwise Wilcoxon signed-rank tests across folds with Holm correction, treated cautiously because folds are not independent.
- **Noise floor:** permutation null at the actual fold sizes.

</details>

<details>
<summary><strong>Formal success criteria</strong></summary>

Thresholds ($\delta_i$, $\rho$) are set in Sprint 2 from the noise floor and recorded in `docs/criteria.md` at tag `criteria-v1` before any outer-fold test scoring.

| # | Criterion |
|---|---|
| C1 | On A, the best meta-learner (chosen by inner-loop CV) exceeds the best uplift random forest: $\Delta Q \ge \delta_1$, paired-bootstrap lower bound $> 0$. |
| C2 | After matching, every encoded covariate has $|\text{SMD}| < 0.1$ in the matched training set of every outer fold. |
| C3 | Precondition: $Q_A - Q_B$ exceeds the noise floor. If it holds, then for the model selected on A: $Q_C / Q_A \ge \rho$ and $Q_C - Q_B \ge \delta_3$ with lower bound $> 0$. Otherwise report that confounding did not degrade ranking. |
| C4 | On A, top-30% uplift for uplift-ranked customers exceeds response-ranked by $\ge \delta_4$ pp, paired-bootstrap lower bound $> 0$. Reported for B and C as well. |

</details>

## 9. Results

Results will be shown separately for the Men's and Women's emails.

| Method | A: Randomized | A′: Fair-size check | B: Biased | C: Biased + matching |
|---|---:|---:|---:|---:|
| Standard-tool methods (meta-learners) | - | - | - | - |
| Specialist tree methods | - | - | - | - |
| "Who will buy?" ranking | - | - | - | - |
| Random choice (luck level) | - | - | - | - |

Score: Qini, higher is better, with margins of error. A balance table (before and after matching) and a chart of extra purchases created by emailing the top 10%, 20%, ... of customers will be added.

## 10. Limits

- **Few buyers.** Small differences between methods may be impossible to separate from luck.
- **The bias is simulated.** Real company targeting rules are messier, and results may depend on the rule we chose.
- **Matching only sees what we measure.** It cannot fix distortions caused by factors missing from the data, which we do not test here.
- **Only seven customer characteristics.** Other factors may matter.
- **Individual effects can't be seen.** We judge rankings through group-level measures.
- **Purchases, not profit.** Email costs and margins are not modeled.
- **One retailer, one two-week window, 2008.** Results may not carry over to other settings.
- **Matching discards data**, which costs statistical power. The fair-size check quantifies this.
- **Compute.** Specialist tree methods are slow at this data size, so their tuning budget may be reduced and documented.

## 11. How this relates to earlier work

- **Radcliffe (2008)** analyzed the same data with commercial software and also modeled visits and spending. We use open-source tools, focus on purchases and add the biased-data scenarios. The results are not directly comparable.
- **Ruf and Handrich (2026)** combined matching with standard prediction tools on *simulated* data. Our outcomes are real and come from a randomized experiment, so we can check matching against the truth. They did not compare tools trained with and without matching, and we do.

## 12. Repository and workflow

```text
data/        Raw data (not tracked in Git) and derived biased datasets
src/         Bias, matching, models, evaluation
notebooks/   Exploratory analysis
docs/        Design notes and prespecified success criteria
outputs/     Result files (inputs to the dashboard)
dashboard/   Streamlit app (reads outputs/ only)
tests/       Automated tests
```

Work follows **CRISP-DM** phases organized in **Agile** sprints, tracked on the GitHub project board. Every sprint ships a dashboard update.

| Sprint | Focus |
|---|---|
| 1 | Define the problem, success criteria and dashboard design |
| 2 | Explore the data, design the bias, set the noise floor, lock the criteria |
| 3 | Models on randomized data |
| 4 | Models on biased data, with and without matching |
| 5 | Evaluate and write up |
| 6 | Final dashboard and release |

Reproduction instructions will be added when the modeling pipeline lands (Sprint 3).

## References

- Austin, P. C. (2011). An introduction to propensity score methods for reducing the effects of confounding in observational studies. *Multivariate Behavioral Research*, 46(3), 399-424.
- Hill, J. L. (2011). Bayesian nonparametric modeling for causal inference. *Journal of Computational and Graphical Statistics*, 20(1), 217-240.
- Hillstrom, K. (2008). The MineThatData E-Mail Analytics and Data Mining Challenge. http://minethatdata.blogspot.com/2008/03/minethatdata-e-mail-analytics-and-data.html
- Künzel, S. R., Sekhon, J. S., Bickel, P. J., & Yu, B. (2019). Meta-learners for estimating heterogeneous treatment effects using machine learning. *PNAS*, 116(10), 4156-4165.
- Radcliffe, N. J. (2007). Using control groups to target on predicted lift. *Direct Marketing Analytics Journal*, 14-21.
- Radcliffe, N. J. (2008). *Hillstrom's MineThatData Email Analytics Challenge: An Approach Using Uplift Modelling.* Stochastic Solutions.
- Rosenbaum, P. R., & Rubin, D. B. (1983). The central role of the propensity score in observational studies for causal effects. *Biometrika*, 70(1), 41-55.
- Ruf, F., & Handrich, M. (2026). Using meta-learners and propensity score matching to optimize customer retention. *International Journal of Market Research*, 68(3), 423-439.
- Rzepakowski, P., & Jaroszewicz, S. (2012). Decision trees for uplift modeling with single and multiple treatments. *Knowledge and Information Systems*, 32(2), 303-327.
- Wager, S., & Athey, S. (2018). Estimation and inference of heterogeneous treatment effects using random forests. *JASA*, 113(523), 1228-1242.
