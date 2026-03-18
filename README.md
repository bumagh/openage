# The Healome Aging Clock

**Open-source blood-based biological age estimation from standard clinical biomarkers.**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/healome/healome-aging-clock/blob/main/notebooks/demo.ipynb)

---

## Why This Exists

Many biological age models are difficult to interpret in clinical contexts, hard to benchmark reproducibly, and show high variability on repeated measurements. I built this release to provide a transparent, reproducible baseline using routine blood biomarkers and a public dataset. The methodology, model, and evaluation are fully open so the community can inspect, compare, and improve on this work.

## Design Principles

- **Interpretable** — Built on standard clinical biomarkers (CBC + CMP + medical history) that map to physiological systems physicians already reason about.
- **Reproducible** — Trained entirely on public data ([NHANES](https://www.cdc.gov/nchs/nhanes/index.htm)). Anyone can retrain, validate, and audit.
- **Validated against mortality** — Survival analysis confirms the model's biological age estimates predict mortality (Cox PH concordance = 0.99).
- **Extensible** — Structured for community contributions: new data sources, models, and benchmarks.

## Quick Start

```bash
git clone https://github.com/healome/healome-aging-clock.git
cd healome-aging-clock
pip install -e .
```

Model weights (`.joblib` files) are in `healome_clock/models/weights/` and are included in the repo. If cloning without Git LFS, you may need to download them separately from releases.

### Requirements

| Package | Version |
|---------|---------|
| Python | 3.8+ |
| numpy | >=1.21, <2 |
| pandas | >=1.3 |
| scikit-learn | >=1.0, <1.1 (models trained with 0.24.1) |
| joblib | >=1.0 |
| matplotlib | >=3.4 |

**Optional extras:**
- `pip install -e ".[survival]"` — adds lifelines (for Kaplan-Meier, Cox PH)
- `pip install -e ".[neural]"` — adds PyTorch (experimental model)

```python
from healome_clock import predict_age

result = predict_age({
    "LBXGH": 5.4,       # Glycohemoglobin (HbA1c)
    "LBXSGL": 95,       # Glucose
    "LBXSCR": 0.80,     # Creatinine
    "LBXRBCSI": 4.52,   # Red blood cell count
    "LBXPLTSI": 245,    # Platelet count
    "LBXMCVSI": 93,     # Mean cell volume
    "LBXRDW": 12.8,     # Red cell distribution width
    "LBXLYPCT": 28.5,   # Lymphocyte %
    "LBDLYMNO": 2.1,    # Lymphocyte count
    "LBXMOPCT": 6.2,    # Monocyte %
    "LBXSATSI": 22,     # ALT
    "LBXSAPSI": 68,     # ALP
    "LBXSLDSI": 138,    # LDH
    "LBXSCK": 132,      # CPK
    "LBXSBU": 15,       # BUN
    "LBXSKSI": 4.0,     # Potassium
    "MCQ220": 2,         # Cancer history (2=No)
    "MCQ160D": 2,        # Angina history (2=No)
    "MCQ160A": 2,        # Arthritis history (2=No)
    "MCQ500": 2,         # Liver condition (2=No)
    "MCQ550": 2,         # Gallstones (2=No)
}, chronological_age=45)

print(result.summary())
```

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/healome/healome-aging-clock/blob/main/notebooks/demo.ipynb)

## Two Model Variants

| Variant | Features | Test MAE | Test R² | Pearson r |
|---------|----------|----------|---------|-----------|
| **Standard** | 21 (15 lab + 6 questionnaire) | 5.11 years | 0.906 | 0.952 |
| **Extended** | 35 (expanded lab panel) | 6.07 years | 0.873 | 0.934 |

Both models: GradientBoosting trained on ~50K NHANES records (2003-2020), validated with Cox PH survival analysis (concordance = 0.99).

Models load from `healome_clock/models/weights/` (standard_21feat.joblib, extended_35feat.joblib). These files are included in the repo. Ensure they exist before running inference.

```python
from healome_clock import HealomeClock

# Standard model (15 blood markers + 6 medical history questions)
clock = HealomeClock(variant="standard")

# Extended model (35 features for comprehensive panels)
clock = HealomeClock(variant="extended")
```

## Training Data

Trained on approximately 50,000 records from [NHANES](https://www.cdc.gov/nchs/nhanes/index.htm) survey cycles 2003-2020. See [MODEL_CARD.md](MODEL_CARD.md) and [DATASET_FACTS.md](DATASET_FACTS.md) for details.

## Internal Validation

Validated against a proprietary longitudinal clinical dataset (~1.5M blood-test records). Summary statistics and validation results are in [DATASET_FACTS.md](DATASET_FACTS.md). Raw data cannot be shared for patient privacy reasons.

## Survival Analysis

The model's biological age predictions are validated against mortality outcomes using NHANES linked mortality data:

- **Cox PH Concordance: 0.99** — biological age is a strong predictor of mortality
- **Kaplan-Meier**: Clear separation between accelerated aging (bio_age - chrono_age >= 5 years) and decelerated aging groups

See [BENCHMARKS.md](BENCHMARKS.md) for full results.

## Benchmarking & Leaderboard

This repo maintains a dual-track leaderboard for community benchmarking:

1. **Track 1**: Age prediction accuracy (MAE, R², RMSE)
2. **Track 2**: Mortality prediction (Cox PH concordance, Kaplan-Meier)

See [benchmarks/README.md](benchmarks/README.md) for how to submit your model.

## Repo Structure

```
healome_clock_oss/
├── healome_clock/
│   ├── models/              # Tree-based (primary) + experimental neural net
│   ├── data/                # NHANES + mortality data loaders
│   ├── evaluation/          # Metrics, survival analysis, leaderboard
│   ├── inference.py         # Main prediction API
│   └── visualization.py     # Plotting utilities
├── notebooks/
│   ├── demo.ipynb           # Quick start (2 min)
│   ├── training.ipynb       # Full training pipeline
│   └── evaluation.ipynb     # Benchmarking walkthrough
├── benchmarks/              # Leaderboard submissions
├── data/                    # Sample input data
└── figures/                 # Generated plots
```

## Limitations

Read [LIMITATIONS.md](LIMITATIONS.md) before using. Key points:
- Trained on a US-representative survey; other populations not validated
- Estimates overall biological age; no organ-specific resolution
- Not a medical device; not for clinical decision-making without oversight

## Future Directions

- Extended model using proprietary longitudinal clinical dataset
- Organ-specific biological age estimation
- Methodology paper

Star this repo or follow [@Healome](https://twitter.com/healome) for updates.

## About Healome

Healome is a longevity-focused health technology company building blood-based aging models and tools for longitudinal health tracking. Learn more at [healome.com](https://healome.com).

## Citation

```bibtex
@software{healome_aging_clock,
  author = {Nikhil Yadala},
  title = {The Healome Aging Clock},
  year = {2026},
  url = {https://github.com/healome/healome-aging-clock}
}
```

## Contributing

I believe the field benefits from better benchmarking and open scrutiny. See [CONTRIBUTING.md](CONTRIBUTING.md) for how to get involved.

## License

Apache License 2.0. See [LICENSE](LICENSE).
