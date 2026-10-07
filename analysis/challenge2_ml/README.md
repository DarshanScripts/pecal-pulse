# Member 2 analytics handoff

Branch: `feat/ml-analytics`. This module consumes Member 1's normalized snapshot contract from `plan.md` §4A. `synthetic_fixture.py` generates a **synthetic only** proposed contract fixture pending Member 1's schema freeze. It contains 30 fictional customer IDs and 36 complete months. No source extracts or credentials are committed.

## Build and load

Run from the repository root after `uv sync`:

```bash
uv run python -m analysis.challenge2_ml.synthetic_fixture
uv run python -m analysis.challenge2_ml.run data/mock/analytics_normalized.json
uv run python -m unittest backend.tests.test_analytics -v
```

For a real approved normalized snapshot, pass its JSON path instead. The top-level keys are `manifest`, `profiles`, and `monthly_history`; rows use `SnapshotManifest`, `CustomerProfile`, and `MonthlyHistoryRow` fields in `plan.md`. Publication creates `data/runtime/analytics/<snapshot_id>/{manifest,predictions,segments,sectors,model_report}.json` only after validation. Existing snapshots are immutable; use a new snapshot ID for a refresh. `data/runtime/` is ignored by Git.

Member 1's composition layer can call:

```python
from backend.app.capabilities.analytics.service import load_outputs, get_prediction, get_sectors

outputs = load_outputs(snapshot_id)
prediction = get_prediction(customer_id, snapshot_id)  # dict or None
sectors = get_sectors(snapshot_id)
```

The service rejects snapshot and reference-date mismatches. A missing artifact raises a file error so API composition can report analytics as unavailable. It does not generate predictions during a request.

## Methods and limits

- Features include recency, cadence/gap variability, active-month fraction, recent/prior volume, observed tenure, monthly group breadth, and seasonality. They use only history at or before each cutoff.
- Segment count 3–6 is selected using silhouette; seed agreement and cluster sizes are reported. Sparse accounts stay unassigned.
- Activity is **any observed calibration at this provider in the next three full months**. Logistic and boosted classifiers, with optional isotonic calibration, compete with prevalence and recency baselines. Validation Brier selects the method. Test ROC AUC, average precision, Brier and reliability bins are descriptive holdout results.
- Three-month calibration-event volume includes zero outcomes. Previous-three-month, prior-12-month divided by four, same-quarter-last-year, and boosted Poisson forecasts compete on validation MAE. The chosen method is tested without refit. No monthly customer values or prediction intervals are asserted.
- Inactivity is a deterministic review signal using recency/cadence and recent volume deficit, separate from activity probability. It is not a churn label.
- Sector forecasts select between last-month and trailing-three-month mean using the first half of past-only walk-forward errors and report the second half as holdout. Correlation uses Pearson coefficients of `log1p(calibration_events)` month-to-month changes, with at least 24 aligned changes and nonconstant series. Small industries are warned; membership is the fixed snapshot cohort.
- The historical `analysis/train_customer_models.py` saved report used an August 2026 cutoff, logistic/isotonic activity model and previous-12-month divided by four volume baseline. Its historical export is absent from this clone. Its original calibration and validation label windows overlap, so the new pipeline uses disjoint stage boundaries; historical metrics must be regenerated from Member 1's approved snapshot and may differ.

Eligibility requires two active months, at least twelve observed tenure months and an active month in the last twelve. The twelve-month floor prevents seasonal and annual-average baselines from interpreting periods before tenure as zero. Unsupported activity and volume values are `null`, with a support reason. Inactivity requires longer repeated history. Monthly group breadth is a proxy, not the number of distinct categories in the whole portfolio. The sector cohort and history coverage assume Member 1's manifest certifies a complete global month grid; any uncovered source period must be excluded upstream.

## Representative synthetic response

From `synthetic-analytics-v1` (reference `2026-12-31`; target `2027-01` through `2027-03`):

```json
{
  "customer_id": "synthetic-customer-00",
  "snapshot_id": "synthetic-analytics-v1",
  "segment_id": "segment-4",
  "activity": {"target": "any_calibration_next_3_months", "probability": 0.999998,
    "window_start": "2027-01", "window_end": "2027-03", "support": {"status": "supported"}},
  "calibration_volume": {"metric": "calibration_events", "horizon_months": 3,
    "expected_total": 4.0, "monthly": null, "lower": null, "upper": null,
    "method": "same_3_months_last_year"},
  "inactivity": {"flagged": false, "recency_to_cadence": 0.5}
}
```

This excerpt omits fields for brevity; [example_prediction.json](example_prediction.json) contains the full `plan.md` §4B shape. Synthetic holdout scores are artificially strong because the fixture repeats simple periodic patterns and must not be presented as historical performance.

## Integration still needed

Member 1 should confirm field names, the complete-month grid and snapshot loader, then wire `load_outputs` into API composition. Member 3 can consume `CustomerPrediction` from the published output or composition service. Regenerate and inspect the model report on the same approved snapshot ID as Member 1 before historical mode is enabled.
