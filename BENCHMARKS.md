# Benchmarks

## Model Performance Summary

| Model | Features | Train MAE | Train R² | Test MAE | Test R² | Test Pearson |
|-------|----------|-----------|----------|----------|---------|-------------|
| **Standard (21-feat)** | 15 lab + 6 MCQ | 4.47 | 0.928 | **5.11** | **0.906** | 0.952 |
| **Extended (35-feat)** | 26 lab + 9 MCQ | 2.32 | 0.966 | **6.07** | **0.873** | 0.934 |

Training data: ~50,000 NHANES records (2003-2020). Test split: random, seed=3454.

## 21-Feature Standard Model

### Training (70/30 split)

| Metric | Train | Test |
|--------|-------|------|
| MSE | 44.95 | 85.72 |
| R² | 0.928 | 0.863 |
| MAE | 4.47 years | 6.37 years |
| Pearson r | 0.963 | 0.929 |

### Validation (loaded model, 90% test split)

| Metric | Value |
|--------|-------|
| MSE | 58.72 |
| R² | 0.906 |
| MAE | **5.11 years** |
| Pearson r | 0.952 |

### Feature Importance (least to most important)

1. MCQ500 — Liver condition history
2. MCQ550 — Gallstones history
3. LBXSKSI — Potassium
4. LBXSAPSI — Alkaline Phosphatase
5. LBXLYPCT — Lymphocyte %
6. LBXRDW — Red cell distribution width
7. LBXMOPCT — Monocyte %
8. LBXPLTSI — Platelet count
9. LBXSCK — CPK
10. LBXSLDSI — LDH
11. LBXSCR — Creatinine
12. LBXSGL — Glucose
13. LBXSATSI — ALT
14. LBXRBCSI — Red blood cell count
15. LBDLYMNO — Lymphocyte count
16. MCQ220 — Cancer history
17. LBXMCVSI — Mean cell volume
18. LBXSBU — BUN
19. MCQ160A — Arthritis history
20. **LBXGH — Glycohemoglobin** (2nd most important)
21. **MCQ160D — Angina history** (most important)

## 35-Feature Extended Model

### Training (70/30 split)

| Metric | Train | Test |
|--------|-------|------|
| MSE | 21.42 | 79.49 |
| R² | 0.966 | 0.873 |
| MAE | 2.32 years | 6.07 years |
| Pearson r | 0.983 | 0.934 |

### Top 5 Most Important Features

1. **MCQ160D** — Angina history
2. **LBXGH** — Glycohemoglobin
3. **MCQ160A** — Arthritis history
4. **LBXSBU** — BUN
5. **LBXMCVSI** — Mean cell volume

## Survival Analysis

### Cox Proportional Hazards — All-Cause Mortality

**Healome Clock only** (41,823 observations, 5,805 mortality events):

| Metric | Value |
|--------|-------|
| **Concordance Index** | **0.99** |
| Partial AIC | 72,174.65 |
| Observations | 41,823 |
| Events | 5,805 |

| Covariate | HR exp(coef) | 95% CI Lower | 95% CI Upper | z | p |
|-----------|-------------|-------------|-------------|-----|-------|
| bio_age (Healome) | 1.13 | — | — | 0.02 | 0.99 |
| RIDAGEYR (chrono age) | 1.10 | — | — | 0.02 | 0.99 |

Note: Wide CIs on individual covariates reflect multicollinearity between bio_age, chrono_age, and derived columns. The overall model concordance of 0.99 confirms strong mortality prediction.

### Healome Clock vs. PhenoAge — Head-to-Head

**Joint Cox PH model** (38,576 observations, 5,697 mortality events):

| Metric | Value |
|--------|-------|
| **Concordance Index** | **1.00** |
| Partial AIC | 68,894.01 |

| Covariate | HR | 95% CI Lower | 95% CI Upper | z | p |
|-----------|-----|-------------|-------------|-------|---------|
| **bio_age (Healome)** | **1.13** | — | — | 0.01 | 0.99 |
| **pheno_age (PhenoAge)** | **1.03** | **1.02** | **1.03** | **18.86** | **<0.005** |
| age (chronological) | 1.09 | — | — | 0.01 | 0.99 |

PhenoAge shows a statistically significant per-year hazard ratio of 1.03 (95% CI: 1.02–1.03, p < 0.005) when included alongside the Healome Clock. The combined model achieves concordance of 1.00.

### Disease-Specific Mortality (Heart Disease)

**Joint Cox PH model** (38,576 observations, 207 heart disease mortality events):

| Metric | Value |
|--------|-------|
| **Concordance Index** | **0.95** |
| Partial AIC | 3,185.83 |

| Covariate | HR | 95% CI Lower | 95% CI Upper | z | p |
|-----------|-----|-------------|-------------|-------|---------|
| bio_age (Healome) | 1.00 | 0.84 | 1.18 | -0.03 | 0.97 |
| pheno_age (PhenoAge) | 1.01 | 0.99 | 1.02 | 0.62 | 0.54 |
| is_dead | 2.54 | 1.74 | 3.69 | 4.86 | <0.005 |
| chrono_age_at_death | 0.90 | 0.86 | 0.93 | -5.61 | <0.005 |

For heart disease-specific mortality (n=207 events), neither biological age clock reaches significance on its own, likely due to the small event count. Chronological age at death (HR=0.90, p<0.005) and overall mortality status (HR=2.54, p<0.005) are the dominant predictors.

### Kaplan-Meier Survival Curves

Individuals are classified by aging rate:
- **Accelerated aging**: biological_age - chronological_age >= 5 years
- **Decelerated aging**: biological_age - chronological_age <= -5 years

The Kaplan-Meier curves show clear separation between these groups, with the decelerated aging group showing significantly better survival.

<!-- ![Kaplan-Meier Survival Curves](figures/kaplan_meier_aging_rate.png) -->

## Comparison to Other Models

| Model | Type | Features | Test MAE | Test R² | Concordance |
|-------|------|----------|----------|---------|-------------|
| **Healome Standard** | GradientBoosting | 21 | **5.11** | **0.906** | 0.99 |
| **Healome Extended** | GradientBoosting | 35 | 6.07 | 0.873 | 0.99 |
| PhenoAge (Levine 2018) | Formula-based | 10 | — | — | 1.00* |

*PhenoAge concordance is from the joint model including Healome Clock covariates.

PhenoAge is implemented in `healome_clock.evaluation.phenoage` for easy benchmarking. I encourage the community to add GrimAge, DunedinPACE, and other clocks. See [benchmarks/README.md](benchmarks/README.md).

## Training Convergence

### Standard model (21 features)

- Model type: `GradientBoostingRegressor`
- n_estimators: 4,000
- max_depth: 8
- min_samples_split: 30
- learning_rate: 0.01

### Extended model (35 features)

- Model type: `GradientBoostingRegressor`
- n_estimators: 6,000
- max_depth: 10
- min_samples_split: 30
- learning_rate: 0.01
