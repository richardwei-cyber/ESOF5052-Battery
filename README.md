# Battery Remaining Useful Life Prediction — Stage 2

Wei Yin · ESOF5052

## Research Objectives

1. Test whether Random Forest and XGBoost reduce remaining useful life (RUL) prediction error relative to Linear Regression on unseen batteries.
2. Examine whether recent capacity trends improve generalization beyond cycle index and current state of health (SOH).

Stage 2 focuses on data selection, multi-source integration, cleaning, labels, and feature design. The report considers at least ten peer-reviewed battery studies. The main improvement target is lower unweighted mean cell-level MAE, assessed alongside RMSE, runtime, and life-overestimation failures under matched experimental conditions.

## Data Sources and Selection

| Source | Scope and rationale | Status |
|---|---|---|
| [NASA](https://catalog.data.gov/dataset/li-ion-battery-aging-datasets) | B0005, B0006, B0007, B0018; nominal 2 Ah. Repeated capacity, voltage, current, and temperature records support the original research question. | Implemented |
| [CALCE](https://calce.umd.edu/data) | CS2_35 and CS2_36; nominal 1.1 Ah. Adds independent aging trajectories and supports cross-source capacity harmonization and cleaning. | Implemented |
| [Severson](https://doi.org/10.1038/s41560-019-0356-8) | Fast-charge LFP/graphite cells broaden chemistry and charging-policy coverage. | Candidate extension |
| [Oxford](https://ora.ox.ac.uk/objects/uuid:03ba4b01-cfed-46d3-9b1a-7d4a7bdf6fac) | Eight Kokam cells; nominal 740 mAh. Adds periodic diagnostics and a different observation frequency. | Candidate extension |

Eligible records are combined into one dataset after checking capacity definitions, ratings, operating conditions, and age indices. Source and battery identities are preserved. NASA and CALCE are currently integrated; Severson and Oxford have not yet been processed.

## Main Methodological Decisions

- **Cleaning:** Remove duplicate, conflicting, invalid-capacity, and incomplete-discharge records. Retain valid capacity recovery, preserve raw files, and leave unavailable essential capacities and labels missing.
- **SOH:** Measured discharge capacity divided by documented rated capacity.
- **Shared 80% endpoint:** The first valid observation with SOH ≤ 0.80 defines a common relative capacity-loss target across different Ah ratings. Severson et al. provide a research precedent. This earlier endpoint can also be observed in some records ending before 70%; it does not remove chemistry or operating-condition differences.
- **Original NASA 70% endpoint:** Retain the proposal's 1.4 Ah definition as a separate target and experiment. Compare 70% and 80% on the same cells where both endpoints are observed.
- **RUL:** Endpoint index minus current index, assigned only before the endpoint. Cells without an observed crossing remain right-censored with missing RUL.
- **Features:** The implemented minimum is age index and current SOH. Planned historical features include the past-five-observation mean, change, and slope. Curve and diagnostic features depend on compatible measurements.
- **Leakage prevention:** Use only information available at prediction time. Keep each battery within one split and fit learned preprocessing on training folds only.

The current age unit is **observed discharge attempts**. CALCE history between workbooks requires reconciliation before interpreting labels as physical-cycle RUL. Five observations do not necessarily represent five cycles.

## Current Results

| Item | Count |
|---|---:|
| Discharge candidates | 2,541 |
| Removed records | 55: 50 duplicates and 5 incomplete discharges |
| Retained observations | 2,486 from six cells |
| Pre-endpoint RUL80 labels | 1,124 from six cells |
| Pre-endpoint NASA RUL70 labels | 328 from three cells |

B0007 remains right-censored at 70% because its minimum observed SOH is approximately 0.70023. Label counts precede exclusions for insufficient historical windows.

## Code and Execution

The current code loads NASA and CALCE records, cleans and combines them, constructs separate endpoint labels, and plots SOH. Model training belongs to later stages.

```bash
python -m pip install -r requirements.txt
python download_data.py
python main.py
```

Main outputs:

- `cleaned_data.csv`: cleaned observations with separate `RUL80` and `RUL70_NASA` columns and statuses.
- `cleaning_summary.csv`, `removed_rows.csv`: cleaning counts and excluded records.
- `eol_summary.csv`, `target_audit.csv`: endpoints and target coverage.
- `soh.png`: SOH curves and endpoint thresholds.

## Planned Evaluation

- Compare all three models on identical cells, rows, and splits, with an ablation of minimal versus historical features.
- Use nested leave-one-cell-out validation and inner-validation MAE for model selection. Seek at least four eligible cells per experiment. With fewer than four, omit tuning; with at least two, evaluate fixed configurations using leave-one-cell-out validation.
- Report MAE, RMSE, R², per-cell and per-source scores, unweighted cell means, fold ranges, and runtime.
- Select and reproduce one compatible published baseline before considering the optional LSTM. Published scores from different tasks provide context; matched experiments determine improvement.

## Timeline

| Checkpoint | Goal |
|---|---|
| Week 2 | Proposal, initial literature review, and shared project folder |
| Week 5 · 25% | Data loading, capacity plots, cohort/endpoint checks, and expanded introduction and review of at least ten peer-reviewed papers |
| Week 8 · 50% | Cleaning, EDA, historical features, cell-disjoint splits, and Linear Regression baseline |
| Week 10 · 75% | Random Forest, XGBoost, tuning, feature ablation, and outer evaluation |
| Week 12 · 100% | Error/runtime analysis, reproducibility, documentation, final report, and presentation |
