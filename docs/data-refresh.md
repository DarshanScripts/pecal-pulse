# Historical data preparation

The app reads prepared offline snapshots. Data imports and training are separate from API requests. Keep source exports, manifests, generated analytics, workflow and chat databases in ignored local directories.

For an authorized offline SQL Server export, verify the SQLite SHA256 against its provenance manifest. Keep both under `data/runtime/source/`, then run from the application root:

```bash
uv run python -m analysis.export_sqlite_data data/runtime/source/PeCalHackathon2026/perschmann.sqlite --complete-through 2026-08 --history-start 2024-01
```

The importer opens SQLite read-only, writes `analysis/customers/` inputs and refuses to overwrite an existing extract. Preserve earlier exports. The alternative read-only SQL exporters are `analysis/export_customer_data.py` and `analysis/export_instrument_data.py`; these require authorized SQL/network access and local credentials.

Choose a new immutable snapshot ID and the actual extraction timestamp from the source manifest. Exclude partial months from the historical cutoff. Run:

```bash
uv run python -m backend.app.capabilities.data.build_snapshot --snapshot-id YOUR_NEW_ID --extracted-at YOUR_ACTUAL_UTC_TIMESTAMP
uv run python -m analysis.build_runtime_snapshot --snapshot-id YOUR_NEW_ID
uv run python -m analysis.challenge2_ml.run --snapshot-id YOUR_NEW_ID --output data/runtime/analytics-v3
PECAL_ANALYTICS_ROOT=data/runtime/analytics-v3 uv run python -m analysis.build_opportunities --snapshot-id YOUR_NEW_ID
uv run python -m analysis.build_retention --snapshot-id YOUR_NEW_ID --analytics-root data/runtime/analytics-v3
uv run python -m analysis.evaluate_volume --snapshot-id YOUR_NEW_ID --analytics-root data/runtime/analytics-v3
uv run python -m analysis.build_insights --snapshot-id YOUR_NEW_ID --analytics-root data/runtime/analytics-v3
```

After successful publication, select `PECAL_SNAPSHOT=YOUR_NEW_ID` and `PECAL_ANALYTICS_ROOT=data/runtime/analytics-v3` in ignored `.env`; restart the backend. Keep the compact JSON and indexed requirements SQLite together. The API rejects raw snapshots above 100 MB. Preserve older analytics directories for rollback.

The locally inspected `historical-full-20260831-v2` compact manifest records extraction at `2026-10-07T12:49:52+00:00`, history reference `2026-08-31` and complete month `2026-08`. Inspect the selected manifest rather than assuming that a dated handover describes the active runtime. The instrument master is a current extract, not a reconstruction at the historical forecast origin.

Missing individual dates remain unknown unless supported by interval/history evidence. Activity probability describes any observed calibration in the next three complete months; volume is a three-month calibration total. No monthly customer prediction or uncertainty interval is supplied. These exports are not live feeds or native SQL Server backups.
