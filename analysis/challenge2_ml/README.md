# Member 2 analytics handoff

Branch: `feat/ml-analytics`. Member 1's `member-1` branch at `ffd0e31` is merged as a dependency. Analytics imports the shared models from `backend/app/contracts/sales_v2.py` and accepts the typed `data.service.load_snapshot()` result. `synthetic_fixture.py` generates a longer **synthetic only** fixture using the same contracts: 30 fictional IDs, 36 complete months and explicit zeros after observed tenure. No source extracts or credentials are committed.

## Build and load

Run from the repository root after `uv sync`:

```bash
uv run python -m analysis.challenge2_ml.synthetic_fixture
uv run python -m analysis.challenge2_ml.run data/mock/analytics_normalized.json
uv run python -m analysis.challenge2_ml.run --snapshot-id synthetic-v1
uv run python -m unittest backend.tests.test_analytics -v
```

For a real approved normalized snapshot, pass its JSON path or `--snapshot-id <id>` to use Member 1's loader. Canonical top-level keys are `manifest`, `profiles`, `history` and `month_grid`; `portfolio` is accepted too. JSON and Pydantic rows are normalized through Member 1's shared types. Publication creates `data/runtime/analytics/<snapshot_id>/{manifest,predictions,segments,sectors,model_report}.json` only after shared-contract validation. Existing snapshots are immutable; use a new snapshot ID for a refresh. `data/runtime/` is ignored by Git.

Member 1's small `synthetic-v1` fixture has incomplete month coverage and insufficient history. It produces three valid predictions with null probabilities/volumes and an unavailable model report. The longer fixture `synthetic-analytics-v2` exercises training and supported outputs. Neither is historical performance evidence.

Member 1's composition layer can call:

```python
from backend.app.capabilities.analytics.service import load_outputs, get_prediction, get_segments, get_sectors

outputs = load_outputs(snapshot_id)
prediction = get_prediction(customer_id, snapshot_id)  # shared v2.CustomerPrediction or None
segments = get_segments(snapshot_id)  # list[v2.SegmentSummary]
sectors = get_sectors(snapshot_id)
```

The service rejects snapshot/reference mismatches and validates predictions, segments and non-null correlation matrices against the shared models. Immutable files are loaded/validated once; callers receive independent values. Missing artifacts raise a file error so composition can report analytics as unavailable. Training remains offline.

## Methods and limits

- Features include recency, cadence/gap variability, active-month fraction, recent/prior volume, observed tenure, monthly group breadth, and seasonality. They use only history at or before each cutoff.
- Segment count 3–6 is selected using silhouette; seed agreement and cluster sizes are reported. Sparse accounts stay unassigned.
- Activity is **any observed calibration at this provider in the next three full months**. Logistic and boosted classifiers, with optional isotonic calibration, compete with prevalence and recency baselines. Validation Brier selects the method. Test ROC AUC, average precision, Brier and reliability bins are descriptive holdout results.
- Three-month calibration-event volume includes zero outcomes. Previous-three-month, prior-12-month divided by four, same-quarter-last-year, and boosted Poisson forecasts compete on validation MAE. The chosen method is tested without refit. No monthly customer values or prediction intervals are asserted.
- Inactivity is a deterministic review signal using recency/cadence and recent volume deficit, separate from activity probability. It is not a churn label.
- Sector forecasts select between last-month and trailing-three-month mean using the first half of past-only walk-forward errors and report the second half as holdout. Correlation uses Pearson coefficients of `log1p(calibration_events)` month-to-month changes, with at least 24 aligned changes and nonconstant series. Small industries are warned; membership is the fixed snapshot cohort.
- The historical `analysis/train_customer_models.py` saved report used an August 2026 cutoff, logistic/isotonic activity model and previous-12-month divided by four volume baseline. Its historical export is absent from this clone. Its original calibration and validation label windows overlap, so the new pipeline uses disjoint stage boundaries; historical metrics must be regenerated from Member 1's approved snapshot and may differ.

Eligibility requires two active months, at least twelve observed tenure months and an active month in the last twelve. The twelve-month floor prevents seasonal and annual-average baselines from interpreting periods before tenure as zero. Unsupported activity and volume values are `null`, with separate support reasons/readiness. Inactivity requires longer repeated history. Monthly group breadth is a proxy, not the number of distinct categories in the whole portfolio.

`month_grid` certifies covered months. An incomplete grid disables customer training/segmentation and inactivity flags; sector correlation uses only adjacent covered month pairs and forecasts use only the contiguous covered tail. A full-grid export with holes in a customer's history after first observation is rejected rather than silently zero-filled. No known industry yields a null correlation payload.

## Representative synthetic response

[example_prediction.json](example_prediction.json) contains a complete shared `CustomerPrediction` from `synthetic-analytics-v2` with reference `2026-12-31` and target `2027-01` through `2027-03`. Synthetic holdout scores are artificially strong because the fixture repeats simple periodic patterns and must not be presented as historical performance.

## Integration still needed

Member 1's contracts and loader are connected and checked. Their v2 API composition still returns analytics-unavailable placeholders until they wire the service functions above. Member 3 should import the canonical nested `CustomerPrediction` (`activity.probability`, `calibration_volume.expected_total`) or adapt explicitly at its boundary; its provisional flat prediction model differs.

The real customer export is still absent from this machine. Supply the approved normalized snapshot, run the same CLI and inspect the model report on that exact snapshot ID before historical mode is enabled. Source quality flags, input SHA256, seed, runtime versions, stage sizes, coverage and evaluation metrics are recorded.
