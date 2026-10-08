# PeCal Pulse — agent handover

Last updated: 8 October 2026. Applies to this repository. Keep this file current when implementation, source data, contracts or verification status change. It should let a new agent resume without replaying the conversation.

## Start here

1. Read this file, then inspect `git status --short` and recent commits. Preserve unrelated work.
2. Read `README.md` for run commands, `context.md` for product/team context and `plan.md` for contracts and intended scope. Older checkpoints in those files describe earlier states; this handover's current-state section supersedes them.
3. Read `integration-audit.md` and `backend/app/agents/README.md` when working on integration or chat. Inspect the actual implementation before treating a planned feature as finished.
4. Continue the user's latest request. Do not restart scaffolding, retrain models or rebuild already working features without a reason.

## Product and working preferences

- Challenge 2: an Inside Sales assistant for Perschmann. Help choose a customer, understand why now, prepare a useful conversation and record a follow-up.
- Aditya and Codex own frontend/chatbot/UI manipulation. The three teammate modules have already been integrated into `main`; the old branch assignments are historical context, not outstanding merge instructions.
- At most three main navigation pages: **Dashboard, Customers, Insights**. Follow-ups are accessible inside Customers; preserve existing compatibility routes.
- Prefer a compact, rounded, approachable UI. Sales users should see a short fact and a useful next question. Put methods, thresholds, limitations and detailed evidence behind accessible info icons or expansion.
- Reuse assistant-ui for chat, existing React Bits/micro components when suitable, and ECharts for charts. Do not introduce a second chart library or rebuild existing library behavior.
- Maintain stable, tested commits as work progresses, with descriptive messages. The user has authorized pushing these completed changes to `origin/main`. Never commit credentials, private extracts, generated historical artifacts or unrelated changes.

## Current implementation

Verified code checkpoint: `3f5161b` (compact customer layout and grouped timing details), following sales-language checkpoints `f723c68` / `407b735`. This handover is a subsequent documentation change.

- Dashboard: a larger two-axis opportunity map, four clickable shaded model regions, bounded customer dots, scoped metrics and ranked accounts. Group selection and filters update cards/table from the same full cohort. One global top-bar assistant entry replaces repeated Ask Pulse buttons.
- Opportunity groups are separate from behavioral customer segments. Coordinates use frozen mid-rank cohort percentiles, displayed from −100 to +100, with zero at the median. Identical evidence retains identical positions. Market filters do not refit the model or change reference normalization.
- Default opportunity model passed quality gates: silhouette 0.450, seed ARI 0.999, outlier ARI 0.972. It has 2,670 scored accounts; discovery-only accounts without timing evidence stay in the list but receive no invented urgency. Other filter/evidence configurations have their own published artifacts.
- Customers: filters/list and independently selected account; Overview, Equipment and Next step tabs. Existing local ownership, workflow checks, batch snooze/resolution and follow-ups persist separately from SQL history.
- Activity chart: historical calibration bars (24 or 3 displayed months) followed by a **shaded three-month forecast window**, labelled with its estimated total. No future monthly bars/line and no fabricated uncertainty interval. Info icon shows forecast input window and quantity-model holdout WAPE/sample size.
- Overview: grouped reasons and compact calibration batch cards. Cards show quantity, equipment category, readable timing, recorded/estimated date source and previous work in that category. Previous category work is not restricted to the displayed batch. Keep each original reason ID for workflow updates.
- Next step: **confirm the calibration need → check in after a longer gap → ask about specific additional services → check team activity → save the next step**. Raw preparation paragraphs were replaced by short facts/questions. Exported briefs use this sales language too.
- Equipment: “Calibration work with us” shows category and completed calibrations; the unavailable inventory-count column was removed. “Services to ask about” gives a named category, an actual conversation question and peer-supported context. Instrument-date records are collapsed.
- Customer tabs and Accounts/Follow-ups are styled pill buttons with visible selection and keyboard focus. Desktop Customers uses the viewport height, independently scrollable account/detail panels and a compact toolbar. At the verified 830px viewport height, page height was also 830px. Small screens retain natural page scrolling.
- Equipment categories paginate five per page. `InstrumentTiming.tsx` replaces repeated raw rows with full-account recorded/estimated/missing timing counts and expandable, paginated groups of the loaded sample (five groups per page). Group by equipment, basis, date range and eligibility; deduplicate instrument IDs within each group. Sample group quantities must never be presented as full-account totals. These new category/date paginations are manual UI controls, not yet typed chatbot controls.
- Batch action controls appear only for calibration batches. Inactivity/discovery are conversation reasons, not generic “Review opportunity” batch cards. Do not reintroduce duplicate technical paragraphs.
- Chat: assistant-ui streamed Markdown, reasoning returned by the provider, tool-call displays, cancellation, history, expandable drawer and SQLite checkpointing. Typed tools manipulate existing controls and create supported chart artifacts. Pulse's system prompt now asks for nontechnical sales language. No new live LLM test was performed after that wording change.
- Financial scenarios are retained as an optional backend capability but removed from the main sales UI. Do not add unsupported profit cards.

## Data and model meanings — preserve these distinctions

- Local historical snapshot: `historical-full-20260831-v2`; source reference **2026-08-31**, forecast **September–November 2026**, 6,564 accounts, 3,180 supported activity/quantity forecasts. A fresh clone defaults to explicit `synthetic-v1`, not historical data.
- Private snapshots, model outputs and workflow/chat SQLite files live in ignored `data/runtime/`; source extracts live in ignored `analysis/customers/`. A clone does not contain them. Do not silently substitute mock data when historical artifacts are missing.
- Root `.env` selects `PECAL_SNAPSHOT` and `PECAL_ANALYTICS_ROOT=data/runtime/analytics-v3` locally. Use `LLM_MODEL` and `OPENROUTER_API_KEY` from backend settings; do not hardcode the earlier Muse choice. Daytona is an optional later execution capability, not evidence of an implemented arbitrary-code tool.
- Analytics v3 adds annual/seasonal features. Chronological validation selects logistic activity prediction (test ROC AUC 0.810; Brier 0.176). Quantity still selects **previous 12 months divided by four**, despite comparing Extra Trees and boosting. Its test WAPE is **65.05%**, MAE about **11.52 calibrations**, over **18,363 customer-origin windows / 3,515 distinct test accounts**. Read the active model report before repeating metrics.
- WAPE is aggregate absolute error divided by aggregate actual volume, not an individual customer's accuracy or “35% accurate.” Repeated customer-origin windows are not independent customers. Keep activity-model discrimination separate from quantity-model error.
- Activity probability means **at least one observed calibration in the next three complete months**. It is not an order/conversion/churn probability and does not estimate outreach benefit.
- Calibration events, distinct instruments, requirements, service records and order positions are different units. “64 instruments” is a batch quantity, not 64 orders. Instrument IDs are lookup references, not sales priority.
- Current instrument exports contain categories, IDs, dates, interval and stop fields; they do not include individual product names/brands/models. Do not conclude that the underlying SQL database lacks those fields without inspecting its schema.
- “Recorded due date” is a real source date; “Estimated due window” comes from supported inference. A passed date does not prove outstanding work. Respect stop flags, date anomalies, sparse history and unknown eligibility.
- Industry peers support a discovery question, not proof that this customer owns missing equipment or uses a competitor. “Longer gap than usual” warrants investigation; it is not confirmed customer loss.
- Historical extracts do not establish today's live quotations/orders, contact people, recent sales conversations, revenue or margins. Manual workflow checks must remain identifiable as manually supplied facts.

## Code map and integration rules

| Area | Primary paths |
|---|---|
| Dashboard/map | `frontend/src/modules/sales/OpportunityDashboard.tsx`, `opportunity-regions.ts` |
| Customer views/copy | `frontend/src/modules/sales/IntegratedWorkspace.tsx`, `CustomerSignals.tsx` |
| Date coverage / grouped sample | `frontend/src/modules/sales/InstrumentTiming.tsx` |
| UI state / commands | `frontend/src/modules/sales/store.ts`, `frontend/src/core/events/router.ts` |
| Chat UI | `frontend/src/modules/chat/SalesAssistant.tsx` |
| Shared frontend contracts | `frontend/src/types/sales-v2.ts`, `frontend/src/types/sales.ts` (also compatibility/chat types) |
| API and scoped detail | `backend/app/api/v2.py`, `backend/app/capabilities/data/opportunities.py` |
| Snapshot/evidence/workflow | `backend/app/capabilities/data/service.py`, `requirements.py`, `workflow.py` |
| Offline analytics | `backend/app/capabilities/analytics/`, `analysis/challenge2_ml/run.py` |
| Agent prompt/tools/contracts | `backend/app/agents/react_agent.py`, `backend/app/capabilities/workspace/tools.py`, `backend/app/agents/contracts.py` |

- Frontend `/api/sales/*` rewrites to Python `/api/*`; do not create a parallel backend path.
- UI manipulation goes through typed events, the event router and Zustand. Update backend contracts, frontend types, state, event application and send-time page context together when adding a control. Do not execute generated JavaScript in the app.
- Use current page snapshots with exact visible labels, values, units, filters and source dates. A snapshot is send-time context, not confirmation of what happened after navigation. Do not claim a UI action was observed unless verified.
- Dashboard preparation is scoped to its due window, inferred-date and past-due settings. Do not accidentally replace that scoped action with the broader account action. Customers can intentionally show broader account history.
- `forecast_quality` on customer detail carries selected quantity-model holdout metrics and baseline input months. Never replace it with the activity model's ROC AUC.
- Existing v1 routes/chat history remain compatible. Preserve suppression IDs and local workflow persistence during UI changes.

## Memory, runtime and verification

- This machine has limited RAM; earlier large loads crashed the shell/browser. Compact runtime JSON is about 63 MB versus roughly 652 MB raw; indexed SQLite retains full requirement evidence. API memory was measured around 724–850 MB after the fix.
- Never load the full raw snapshot into the API or browser. The API rejects raw snapshots above 100 MB. Keep compact JSON and its evidence index together; use `analysis.build_runtime_snapshot` for streaming generation.
- Plot sample defaults to 200, capped at 1,000. Samples do not change full-cohort totals. Account detail loads at most 500 evidence records; date details group this loaded sample into five rows per page, with separate full-source tier counts. Chat evidence is independently capped; do not confuse its limits with UI grouping.
- Train offline, with the existing single-thread limit. Prefer the snapshot-ID loader. Stop owned previews before heavy training/building when needed; avoid duplicate API processes, concurrent cold loads and unnecessary browser tabs. Preserve old analytics directories for rollback, and republish compatible opportunity artifacts after changing analytics versions.
- Standard development: `uv sync`, `pnpm --dir frontend install`, `bash scripts/dev.sh`. Preview ports: frontend 3000, API 8001. Check existing listeners before starting another server; stop only processes you verified belong to this task.
- Latest frontend verification: TypeScript and production build passed; browser verified account `20ADBF21`, category page 1→2, grouped timing sample and desktop viewport fit. Last backend verification remains **142 passing tests** (backend unchanged in this layout slice). Earlier browser verification covered account `970CE027` preparation and specific peer-category questions. No customer outreach or SQL writes were performed.

```bash
uv run python -m unittest discover -s backend/tests -q
pnpm --dir frontend typecheck
pnpm --dir frontend build
git diff --check
```

Use checks appropriate to the change; do not add tests that merely mirror trivial copy. For visible behavior, inspect the actual browser after loading the new build. Avoid changing persisted workflow data solely for visual verification unless it is explicitly disposable.

## Remaining work and handover maintenance

- No unfinished implementation from the latest sales-language request. Await the user's next priority.
- Planned later work includes contact-time budgeting and clearer shared follow-up handling. CRM/live quote checks, confirmed churn labels, validated financial inputs, monthly customer quantity forecasts/intervals, causal uplift and full sandbox execution remain unimplemented or unsupported; do not present them as working.
- Update this file after material changes: current code checkpoint, what shipped, latest checks, source/model configuration, risks and any precise outstanding task. Correct stale summaries in `context.md`/`README.md` instead of appending contradictory claims. Never copy `.env` values or credentials into handover documents.
