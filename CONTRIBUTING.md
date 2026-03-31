# Contributing

Contributions that improve the model's accuracy, robustness, interpretability, or documentation are welcome.

## Particularly Valuable Contributions

- **Benchmark comparisons** against other biological age models (PhenoAge, Klemera-Doubal, GrimAge, etc.)
- **Subgroup analyses** on populations not well-represented in NHANES
- **Alternative preprocessing** or imputation strategies (e.g., iterative imputation, normalization)
- **Feature importance analysis** — which biomarkers drive predictions most?
- **Improved visualization** of results
- **Bug reports** and reproducibility issues
- **Documentation** improvements and clarifications

## How to Contribute

1. **Open an issue first** before starting a large PR to discuss the approach
2. Fork the repository and create a feature branch
3. Make your changes with clear commit messages
4. Add or update tests as appropriate
5. Submit a pull request with a description of what you changed and why

## Development Setup

```bash
git clone https://github.com/Healome/openage.git
cd openage
pip install -e ".[dev]"
pytest
```

## Code Style

- [Black](https://github.com/psf/black) for formatting (line length 100)
- [Ruff](https://github.com/astral-sh/ruff) for linting
- Type hints are encouraged but not required
- Docstrings follow NumPy/Google style

## Leaderboard Submissions

This repo maintains a dual-track leaderboard. To submit your model:

1. Train on NHANES data (any cycles)
2. Evaluate using `test_size=0.3, random_state=3454`
3. Generate a submission JSON using `openage.evaluation.leaderboard.create_submission()`
4. Open a PR adding your JSON to `benchmarks/submissions/`

See [benchmarks/README.md](benchmarks/README.md) for the full specification and `notebooks/evaluation.ipynb` for a walkthrough.

## Adding Data Sources

The data loading system is extensible. To add a new data source:

1. Create a loader function that returns a pandas DataFrame with NHANES-compatible column names
2. Register it using `openage.data.registry.register_data_source()`
3. Add documentation and a loader module to `openage/data/`

## Questions?

Open an issue on GitHub or reach out at [nikhil@healome.one](mailto:nikhil@healome.one).
