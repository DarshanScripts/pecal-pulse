# Member 1 — data / API / workflow

Owner: Member 1, branch `member-1` (plan names it `feat/data-api`).

## Run

```bash
uv sync
uv run python -m unittest discover -s backend/tests -v
```

## Source access (read-only; workflow writes stay in local SQLite)

- Server `tcp:192.168.1.200,1433`, database `PeCalHackathon2026`, account
  `PeCalHackathonParticipant`, driver `ODBC Driver 18 for SQL Server`.
  Reachable from the lab network only. Password is prompted interactively
  and never saved; `.env` files are gitignored.
- Extract scripts (all read-only): `analysis/export_customer_data.py`
  (monthly history, industry, group counts) and
  `analysis/export_instrument_data.py` (instruments, instrument events).
  Outputs land in `analysis/customers/*.json` (gitignored).
- Build a runnable snapshot without SQL access:
  `uv run python -m backend.app.capabilities.data.build_snapshot --help`
  (reads the extracts above, writes `data/runtime/snapshots/<id>.json`).
  Select it with `PECAL_SNAPSHOT=<id>`; default is the synthetic fixture.
- Demo "today" for workflow/snooze logic: `PECAL_TODAY` (default 2026-10-07).

## Extract inputs (what the builder consumes)

- `analysis/export_customer_data.py` — read-only SQL Server extract (lab network,
  password prompted, never saved). Outputs land in `analysis/customers/`
  (gitignored): `monthly_history.json` (2024-01–2026-08, complete months only),
  `industry.json`, `groups.json` (trailing 12 m), `industry_duplicates.json`.
- `analysis/challenge_data_validation.txt` — quality evidence: 140,390 missing
  due dates (23,895 with repeat history, 17,746 with positive interval),
  September 2026 is partial → `complete_through_month = 2026-08`.
- Source customer IDs are full 64-char SHA2-256 hashes. Never truncate them
  without a collision check (`train_customer_models.py` truncates to 10 chars;
  the shared contract uses full IDs).

## Outputs

- `backend/app/contracts/sales_v2.py` — frozen shared Pydantic models (plan §4):
  snapshot rows, Member 2 prediction types, requirements/actions/preparation,
  screen metadata, workflow writes, v2 chat context.
- `backend/app/capabilities/data/service.py` — immutable snapshot loader
  (`load_snapshot`, `get_customer_detail`, `recency_months`); synthetic fixture
  in `data/mock/`, real extracts in `data/runtime/snapshots/` (gitignored).
- `backend/app/capabilities/data/requirements.py` — four-tier due inference
  (recorded / nominal ±1m / repeat-history ≥3 gaps / unknown), rule
  `requirements-v1`. Inference reproduces the fixture tiers exactly.
- `backend/app/capabilities/data/workflow.py` — SQLite owner/checks/
  signal-scoped suppressions/audit + v2 follow-ups (reason links in audit).
- `backend/app/api/v2.py` — bootstrap, customers list/detail, followups,
  contracts, workflow PATCH. Predictions/actions/sectors/model-report return
  explicit unavailable (503 or null) until Members 2/3 merge; v1 routes intact.
- `data/mock/v2_snapshot_synthetic.json` — small valid synthetic snapshot
  (`synthetic-v1`, reference 2026-08-31) covering all requirement tiers:
  recorded / nominal-interval / repeat-history / unknown, plus stopped→excluded
  and identifier-fallback display names.
- `backend/tests/test_data_contracts.py` — contract + fixture invariant tests.

## Limitations

- No live SQL access on this machine; snapshot work proceeds from the synthetic
  fixture and the documented extract until the real export is supplied.
- Prediction/action/sector payloads are Member 2/3 types only — this branch
  serves them, never fabricates them. Missing modules return unavailable, never
  mock numbers under historical mode.
- Workflow writes go to local SQLite (`PECAL_DEMO_DB` or
  `data/runtime/demo.sqlite3`); the SQL source is read-only.
