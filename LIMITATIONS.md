# Limitations

## Known Limitations

- **Training data scope:** Trained on NHANES, a US-representative survey. Performance on non-US populations, clinical subgroups, or individuals outside the NHANES age range has not been externally validated.

- **Label definition:** The model predicts deviation from chronological age. Whether this deviation corresponds to meaningful biological aging, disease risk, or mortality is an active research question, not a settled fact.

- **No organ-specific resolution:** This model estimates an overall biological age. It does not provide organ-level or system-level aging estimates. That is a future research direction.

- **Not a medical device:** This model is released for research and personal exploration. It is not FDA-cleared, CE-marked, or validated for clinical decision-making.

- **Biomarker availability:** Performance depends on having the specific biomarkers the model was trained on. Partial panels may degrade accuracy. See [MODEL_CARD.md](MODEL_CARD.md) for the full biomarker list.

- **Population bias:** NHANES oversamples certain demographic groups by design (Hispanic, non-Hispanic Black, non-Hispanic Asian, older adults, low-income populations). Model performance may vary across subpopulations not well-represented in the effective training distribution.

- **Analytical variance:** While blood biomarkers generally show lower analytical variance than epigenetic markers, some individual biomarkers (e.g., CRP, liver enzymes like GGT/ALT) can fluctuate based on acute illness, fasting status, alcohol intake, or time of day. Users should interpret results in the context of the individual's clinical state at the time of blood draw.

- **No longitudinal calibration:** The model was trained on cross-sectional data. While I have validated against longitudinal data, the training objective is cross-sectional age prediction. Longitudinal trajectory interpretation requires additional validation.

- **Imputation sensitivity:** When biomarker values are missing, the model uses imputation. Predictions from heavily imputed inputs should be interpreted with additional caution.

## Intended Use

- Research and benchmarking against other biological age models
- Personal health exploration (with appropriate context)
- Foundation for further model development and extension
- Educational purposes in computational biology and aging research

## Not Intended For

- Clinical diagnosis or prognosis
- Medical decision-making without professional oversight
- Insurance underwriting, employment decisions, or other consequential decisions about individuals
- Sole basis for health interventions without clinical consultation
