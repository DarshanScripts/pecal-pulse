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
| `get_ranked_actions` | per-customer maps (same as above) | `AccountAction[]` sorted |
| `build_preparation` | profile + action + peers + prediction + reqs + workflow | `PreparationCard` |
| `get_evidence` / `evidence_lookup` | refs from reasons/facts | record table for API/agent |
| `category_prevalence_by_industry`, `opportunity_type_distribution`, `account_coverage` | portfolios / ranked queue | aggregate EDA rows + metric defs |
| `split_followups_first` | ranked actions + workflows + today | (due-first, proactive-rest) |

## Rules that matter

- **Account-level peers:** one account = one vote per category, regardless
  of row counts. Target account excluded. Defaults: ≥20 eligible accounts,
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

- Needs Member 1's `SnapshotStats` + normalized snapshot and Member 2's
  `CustomerPrediction` for production data; until then runs on the
  synthetic fixture in `analysis/challenge2_insights/fixtures/`.
- No frontend/chat/checkpoint/Daytona code here (Aditya + Codex own that).
- At the shared-contract freeze these models stay the canonical insight
  I/O (Member 1 imports/composes them into `sales_v2.py` and screen
  responses; this module is not rewritten as aliases).

## Representative fixture

`analysis/challenge2_insights/fixtures/synthetic_snapshot.json`
(`synth-2026-08-31`): 6 accounts, 2 real industries + Unknown,
recorded/inferred/stopped/unknown requirements, flagged + unsupported
predictions, snooze + follow-up workflow. See
`analysis/challenge2_insights/README.md` for the worked example output.
