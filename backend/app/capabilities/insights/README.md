# Member 3 — sales intelligence (`insights`)

Owner: Member 3 · Branch: `feat/sales-intelligence` · Ranking version: `rank-v1`

Peer discovery, ranked sales actions, and preparation cards. Pure
functions only — no I/O, no imports from data/analytics/agents modules.
Member 1 composes these into `/api/v2` screen responses; Aditya + Codex
wrap them as agent tools.

## Run

```bash
uv run python -m unittest backend.tests.test_insights_services -v
uv run python analysis/challenge2_insights/run_eda.py
```

## Inputs → outputs

| Function | Input (whose) | Output (plan §4C) |
|---|---|---|
| `build_peer_index` / `get_peer_opportunities` | `PortfolioRow[]` + industry map (M1) | `PeerOpportunity[]` |
| `build_account_action` | profile reqs + `CustomerPrediction` (M2) + peers + `AccountWorkflow` (M1) + `SnapshotStats` | `AccountAction \| None` |
| `ranking_fn_for_composition(stats)` | Member 1's `refresh_after_correction` injects the result as `ranking_fn(profile, requirements, prediction, peers, workflow)`; accepts local- or shared-shaped args | `AccountAction \| None` |
| `action_to_shared_payload` | local `AccountAction` | dict validating as shared `AccountAction` |
| `prediction_from_shared` etc. (`compat.py`) | shared nested prediction / full-field workflow / row-count portfolio dicts or objects (never Member 1/2 imports) | local models |
| `get_ranked_actions` | per-customer maps (same as above) | `AccountAction[]` sorted |
| `build_preparation` | profile + action + peers + prediction + reqs + workflow | `PreparationCard` |
| `get_evidence` / `evidence_lookup` | refs from reasons/facts | record table for API/agent |
| `category_prevalence_by_industry`, `opportunity_type_distribution`, `account_coverage` | portfolios / ranked queue | aggregate EDA rows + metric defs |
| `split_followups_first` | ranked actions + workflows + today | (due-first, proactive-rest) |

## Rules that matter

- **Account-level peers:** one account = one vote per category, regardless
  of row counts. `distinct_instruments=None` (row-count export) falls back
  to `calibration_events > 0` as presence; explicit `0` always means not
  owned. Target account excluded. Defaults: ≥20 eligible accounts,
  ≥25% prevalence (configurable). `Unknown`/`Sonstiges` → no discovery.
- **Bundling:** requirements group by (group, window); instrument lists
  deduplicated; each reason keeps its requirement IDs as evidence.
- **Suppression before ranking:** `stopped=True` / `eligibility=excluded`
  never rank. Snooze needs `until` and applies while `today <= until`;
  resolution needs a non-empty note. Suppressed reasons vanish; unrelated
  reasons on the same account remain.
- **Readiness:** inactivity/discovery are always `review_required`.
  Upcoming `recorded`+eligible reasons become `eligible` **only after** a
  human records a quotation or recent-contact check; otherwise they
  downgrade to `review_required` with unknown
  `live quotation/contact checks unchecked`.
- **Ranking:** weights timing .35 / quantity .30 / activity-deviation .20 /
  evidence .15 (business assumptions, `rank-v1`). Components normalized
  against frozen `SnapshotStats`; missing → `null`, contributes 0 (never
  scored as strong). Deterministic: score desc, id asc.
- **Honesty:** absent categories become questions, never owned-equipment
  claims. No churn/revenue/margin/next-order-date claims anywhere.

## Limitations

- Local models stay canonical (team decision); `compat.py` coerces
  shared-shape inputs, `action_to_shared_payload` renders shared-shape
  output. `SnapshotStats` anchors come from Member 1 per snapshot.
- Validated end-to-end on Member 1's `synthetic-v1` snapshot (all four
  requirement tiers, stopped+excluded, null group/windows, null industry):
  SYN-001 ranks 4 upcoming reasons, SYN-002 one unknown review, SYN-003
  correctly absent; sparse peers correctly yield nothing at defaults.
  Member 2 predictions plug in via `prediction_from_shared` once published
  for the same `snapshot_id`.
- No frontend/chat/checkpoint/Daytona code here (Aditya + Codex own that).

## Representative fixture

`analysis/challenge2_insights/fixtures/synthetic_snapshot.json`
(`synth-2026-08-31`): 6 accounts, 2 real industries + Unknown,
recorded/inferred/stopped/unknown requirements, flagged + unsupported
predictions, snooze + follow-up workflow. See
`analysis/challenge2_insights/README.md` for the worked example output.
