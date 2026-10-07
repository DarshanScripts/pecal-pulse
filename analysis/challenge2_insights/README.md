# Member 3 — analysis workspace (`challenge2_insights`)

Owner: Member 3 · Branch: `feat/sales-intelligence`

Fixture-first peer/ranking development while Members 1/2 build the shared
snapshot + predictions. No training here; the only script is a
reproducible worked example over the synthetic fixture.

## Layout

- `fixtures/synthetic_snapshot.json` — 6 accounts, `synth-2026-08-31`.
  Recorded/inferred/stopped/unknown requirements, flagged + unsupported
  predictions, snooze + follow-up workflow. Small on purpose: default peer
  thresholds (20/25%) yield nothing here, proving sparse handling.
- `run_eda.py` — loads the fixture, runs the real `insights` service
  functions (lowered `min_peer_accounts=2` so the small fixture shows a
  discovery), prints ranked queue + one preparation card + EDA aggregates.

## Run

```bash
uv run python analysis/challenge2_insights/run_eda.py
uv run python -m unittest backend.tests.test_insights_services -v
```

## Expected output (abbreviated)

- Queue: `C-AUTO-001` top (recorded upcoming, high timing/quantity),
  `C-AUTO-004` inactivity-review present, stopped-only / fully-suppressed
  accounts absent.
- Preparation card for `C-AUTO-001`: every fact carries evidence refs;
  peer question asks about Torque tools without claiming ownership.
- EDA: `AUTO/G-TORQUE 3/4 = 75%`; opportunity mix + account coverage.

## Validating on the shared historical snapshot

When Member 1 publishes the normalized snapshot + Member 2 the predictions
for the same `snapshot_id`, rerun the same service calls with default
thresholds (20 accounts / 25%) and `SnapshotStats` from Member 1, then
paste the resulting queue top-10 + prevalence table into the handoff.
Do not commit real extracts or model binaries here (see `.gitignore`).
