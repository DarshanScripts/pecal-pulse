# Challenge 2 implementation plan — PeCal Pulse

Date: 7 October 2026. Team: Aditya + three backend members. Replace the member labels below with names when assigning work. Aditya and Codex own **both the frontend and the chatbot/agent/workspace manipulation**, including conversation checkpointing and optional Daytona execution.

## Model selection update — 7 October 2026

The user has superseded the fixed Muse model choice: use `LLM_MODEL` from the root `.env`, with environment overrides. Earlier fixed-model references below describe the original selection. Chat status reports the active configured model.

## Implementation update — 7 October 2026

All three teammate branches are integrated into main, preserving assistant-ui streaming, provider-returned reasoning, tool calls, cancellation and checkpoint recovery. The frontend now consumes the shared v2 APIs on Dashboard, Customers and Follow-ups; chatbot tools use the same selected snapshot. Historical extraction and offline training have run on Aditya's machine. See [integration-audit.md](integration-audit.md) for delivered scope, source repairs, measured results, verification and remaining enhancements.

The active model is read from `LLM_MODEL`. Live historical page grounding and filter/navigation controls were verified with the configured OpenRouter model. Daytona execution, browser application acknowledgements, voice and live CRM integrations remain pending; standard charts and evidence tools work without them.

## 1. What we are building

An Inside Sales assistant answering: **“Which customer should I contact next, why now, what should I ask, and what happens afterwards?”**

Keep the current three pages: **Dashboard, Customers, Follow-ups**. Chat remains a drawer using assistant-ui. The frontend uses Next.js/TypeScript, Zustand and ECharts; the backend uses Python/FastAPI and scikit-learn/NumPy where needed. Reuse the existing template and analysis instead of rebuilding them.

**User-selected chatbot stack:** a LangChain/LangGraph ReAct tool-calling agent; OpenRouter model `meta/muse-spark-1.3-contributor`; root `.env` variable `OPENROUTER_API_KEY`; LangGraph SQLite conversation checkpointing. Use assistant-ui for the thread/composer/actions and React Bits, including `/c/micro` components, where they improve the interface. These choices are fixed for this project.

The complete demo is:

1. Review a manageable, ranked customer queue.
2. Open an account and inspect its history, due requirements, predictions and flag evidence.
3. Ask the assistant to explain it, filter customers or create a chart.
4. Prepare a conversation, record a correction/outcome and save the next follow-up.
5. See that follow-up and the corrected recommendation in the workspace after reloading.

### Hackathon scope

| Feature | Backend owner | Frontend destination |
|---|---|---|
| Customer history, industry, observed equipment portfolio, source quality | Member 1 | Customers: list and evidence workspace |
| Recorded due windows and supported missing-date inference | Member 1 | Upcoming-needs reason, due-date tiers and relevant instrument list |
| Behavior clustering and readable segment descriptions | Member 2 | Dashboard segment chart; Customers dropdown |
| Probability of future calibration activity | Member 2 | Customer activity card and explanation |
| Expected calibration volume and sector outlook | Member 2 | Customer forecast; Dashboard sector chart |
| Cycle-aware unusual inactivity and volume decline | Member 2 | Activity-review evidence, consumed by Member 3 ranking |
| Sector correlation heatmap | Member 2 | Dashboard; optional industry filter interaction |
| Peer-supported industry portfolio discovery | Member 3 | Customer opportunities and conversation questions |
| Transparent opportunity ranking and account-level bundling | Member 3 | Dashboard top 10; Customers action filters |
| Grounded sales assistant, page context and typed workspace/chart tools | Aditya + Codex | Existing assistant-ui drawer and page controls |
| Persistent conversation threads and restart recovery | Aditya + Codex | Chat drawer: restored history and new-conversation action |
| Agent data analysis and optional sandbox-generated artifacts | Aditya + Codex; Members 1/2/3 provide queryable data services | Chat artifacts and workspace plots |
| Preparation brief and export | Member 3 supplies facts; Aditya renders/export | Customer conversation section and chat |
| Ownership, outcomes, manual checks, snoozes and follow-ups | Member 1 | Customer form; Follow-ups page; recommendation suppression |
| Model quality, data freshness and unsupported cases | Members 1/2 supply evidence | Small dashboard/customer disclosures; no extra navigation page |

**Do not claim:** confirmed churn, revenue/margin, incremental outreach benefit, exact next-order dates, ownership of unobserved equipment or live quotation availability. These need inputs not established by the extract. Commercial prioritization is quantity/timing/evidence based until validated financial data exists.

**Only after the core works:** aggregate delivered order-position forecasts, correlation-based multivariate forecasting, voice, CRM integration, additional horizons, sophisticated explanations. An order-position count must never be labelled a distinct-order count. Exact next-contact/follow-up dates are workflow inputs; predicted next calibration timing is a supported window, not a promised order date.

## 2. Branches and responsibilities

Use **four long-lived branches total**: `main` plus three backend branches. Aditya owns frontend work and integration on `main`; each backend member develops on their assigned branch and opens small PRs into `main`. Short-lived frontend branches are optional, not required for this workflow.

| Person | Branch | Main responsibility | Files/directories they own |
|---|---|---|---|
| Aditya + Codex | `main` | Frontend, ReAct chatbot/checkpoints, page context, agent UI tools, optional sandbox/artifacts, integration and demo | `frontend/**`, `backend/app/agents/**`, proposed `backend/app/api/chat.py`, sales `tools.py`/`mock_assistant.py`, capability registry, proposed `backend/app/capabilities/workspace/**` and `shell/**`, agent/workspace tests, this plan, context, README |
| Member 1 | `feat/data-api` | SQL/extract pipeline, data contracts, API composition, workflow persistence | `backend/app/capabilities/data/**`, `backend/app/contracts/**`, `backend/app/api/sales.py`, proposed `backend/app/api/v2.py`, current sales `service.py`/`models.py`, `backend/app/main.py`, `backend/app/realtime/publisher.py`, data scripts and corresponding tests |
| Member 2 | `feat/ml-analytics` | Features, segmentation, activity/volume models, inactivity and sectors | `backend/app/capabilities/analytics/**`, `analysis/challenge2_ml/**`, analytics tests and model reports |
| Member 3 | `feat/sales-intelligence` | Peer discovery, ranked sales actions, preparation and explainable evidence services | `backend/app/capabilities/insights/**`, `analysis/challenge2_insights/**`, insight tests and fixtures |

Member 1 owns `pyproject.toml` and `uv.lock`: all teammates send dependency requirements early so they are added once. Do not independently restructure the API, edit another person's modules or copy their unfinished files into your branch. Small wiring changes in `main.py`/API composition go through Member 1; frontend/agent/registry changes go through Aditya + Codex. Member 3 delivers callable insight services, not a second chatbot.

### Member 1 — data, API and sales workflow

Deliver these in order:

1. A read-only, reproducible source snapshot and manifest: source tables, extraction timestamp, complete-month cutoff, counts, join checks and data exceptions. Support a local extract so the demo does not depend on the lab network.
2. Stable customer/instrument IDs and normalized tables defined in §4. Use historical customer attribution for historical activity; current instrument ownership is a separate field. Check join cardinality and deduplicate events before aggregating.
3. Customer profiles, monthly history, industry mapping and observed portfolio. Keep **calibration events** and **distinct instruments** separate. Missing names become identifier-based display names, not invented companies.
4. Recorded upcoming requirements, valid nominal-interval inference and repeated-history inference. Attach method, evidence, support count and window to each result. Invalidate implausible dates; exclude explicitly stopped instruments. A null stop flag remains unknown, not “active confirmed”.
5. Version 2 read endpoints and bootstrap composition. Join Member 2 predictions and Member 3 insights by the same full customer ID and snapshot ID. Pending modules return explicit unavailable states, never substitute mock numbers into historical records.
6. Extend the existing local SQLite workflow: owner, structured outcome, next step/date, manual quotation/contact checks, signal-scoped snooze/correction. Persist workflow outside the SQL source. Publish the existing follow-up events after committed writes.
7. Refresh/recompute an affected account's actions after a correction, consuming Member 3's pure ranking function. Completing a follow-up does not automatically mean the calibration need was resolved.

Due-date inference starts with an explicit usable interval plus last calibration, then a supported repeated-instrument interval. A pragmatic minimum for repeated-history inference is three positive gaps, with median and observed spread recorded. Nominal intervals need unit conversion and business-semantic checks. Group/cohort estimates are optional and must remain group-level when individual evidence is inadequate. Do not assign a fake exact date to every unknown instrument.

**Acceptance:** an account's quantities can be traced to source records; joins do not multiply events; unsupported dates remain unknown; workflow changes survive restart; a stop/snooze applies to the intended signal only; the app runs from a local snapshot without SQL availability.

### Member 2 — supervised/unsupervised ML and sector analytics

Deliver these in order:

1. Consume Member 1's normalized history; reuse/refactor `analysis/train_customer_models.py`. Parameterize dates instead of its current hard-coded month indices. Publish functions and offline outputs, not a notebook that the API must execute per request.
2. Behavior features: recency, tenure, frequency/active-month fraction, volume, gaps/cadence, gap variability, recent-versus-prior momentum, seasonality and observed portfolio breadth. Fit preprocessing on training data when evaluating predictive models.
3. KMeans segmentation with log/scaled features; compare a small set of cluster counts and check silhouette, seed stability and cluster sizes. Publish dynamic segment IDs/labels/profiles. Sparse-history accounts may be unassigned; do not force the three mock segment labels onto real clusters.
4. Supervised target: **at least one observed calibration at Perschmann during the next three full calendar months**. Compare logistic regression/boosted trees against recency/prevalence baselines; assess discrimination and probability calibration. Return null plus a reason outside model eligibility.
5. Three-month calibration-count forecast, including zero outcomes. Compare recent, seasonal and historical-average baselines with the supervised regressor. Ship the strongest validated choice, even when it is a simple baseline. Publish measured uncertainty only when it has actually been evaluated.
6. Inactivity evidence: recency/cadence ratio, recent volume deficit, history support and alternate explanations. These are retention-review signals, not supervised churn labels. Keep the model's activity probability separate from the deterministic review rule.
7. Monthly sector history and a simple sector forecast with walk-forward evaluation. Produce a correlation matrix on aligned, complete periods; default to Pearson correlation of month-to-month changes in `log1p(calibration_events)`, with sample counts and method shown. Require at least 24 common changes; otherwise return null. Flag small cohorts/unstable results. Correlation alone does not produce a forecast.
8. If the baseline already wins, spend remaining time on coverage, calibration and usable evidence rather than adding algorithms. Optional cross-sector forecasting must beat the same univariate baseline in time-based testing before becoming the default.

**Acceptance:** labels start after the feature cutoff; train/calibration/validation targets finish before the next evaluation stage begins; model selection never uses test outcomes; results include baselines, sample counts and coverage. Quarter-only predictions are not divided by three and presented as a trained monthly forecast. Monthly points require their own model/baseline evaluation. Unsupported probabilities, volumes and uncertainty bounds remain null.

### Member 3 — sales intelligence and preparation services

Deliver these in order:

1. Peer portfolio prevalence by industry, using account-level ownership of an **observed calibrated category**, not number of calibration rows. Exclude the target account from its peers. Default minimum peer support: 20 eligible accounts and 25% prevalence; expose these configurable thresholds. Exclude `Unknown`/`Sonstiges` from specific industry-discovery assertions.
2. Account-level action construction with distinct `upcoming`, `inactivity`, `discovery` reasons. Bundle duplicate instrument signals and retain each reason. Apply stop/resolution/snooze rules before ranking; missing live checks make an action `review_required`, not outreach-ready.
3. Transparent priority components: timing, relevant quantity, activity deviation and evidence strength. Normalize against the frozen snapshot, record the ranking version and expose weights. A possible default is 35% timing, 30% quantity, 20% activity deviation, 15% evidence; these are business assumptions, not ML-derived commercial value. Missing components stay explicit; handle absent data without scoring it as strong evidence. Agreed due follow-ups form a separate deadline-first section.
4. Preparation cards with known facts, unknowns, evidence references, discovery questions and a suggested next step. Reuse these structured facts for chat and export; the LLM may phrase them but must not invent inputs.
5. Publish service functions for peer comparisons, ranked actions, preparation and evidence retrieval. Aditya + Codex wrap them as agent tools; Member 1 composes them into screen responses. Provide the quantity basis, support counts, windows, ranking components and unknowns that both consumers need.
6. Add small real-data EDA summaries behind those services: category prevalence by industry, opportunity-type distribution and account coverage. Reuse the same calculations for screen/chart data and agent answers; supply aggregate rows/metric definitions, not frontend code or generated chart JS.
7. Test rules for stopped/resolved/snoozed reasons, portfolio denominator, target-account exclusion, sparse industries, account-level deduplication and deterministic ranking. Deliver a synthetic fixture plus a reproducible report/example for each core service.

**Acceptance:** peer results disclose denominator/window; absent categories become questions, not owned-equipment claims; every action explains its basis; corrected/snoozed reasons disappear appropriately while unrelated reasons remain; the same input gives the same ranked evidence; API and agent consumers use the same insight functions. No chat/checkpoint/frontend implementation is assigned to this member.

### Aditya + Codex — frontend, chatbot, agent workspace and integration

1. Preserve the current visual direction and assistant-ui components; reuse suitable React Bits components and ECharts.
2. Replace hard-coded mock segment choices with backend-provided segment IDs/labels. Support multiple action reasons, unknown values, quality disclosures and an explicit historical reference date.
3. Consume v2 bootstrap/list/detail/sector responses through `frontend/src/modules/sales/api.ts`; keep fetch/normalization logic out of page components. Upgrade `frontend/src/types/sales.ts` with Member 1 at contract freeze.
4. Render real history and the forecast's actual unit/horizon. Show a quarter-total outlook when monthly points are unavailable; never manufacture monthly predictions or confidence shading. Distinguish inferred requirement windows from expected activity.
5. Use server filtering/pagination for the full customer population. Keep dashboard top 10 and “View all”. A selected customer must be loaded independently of the current list page.
6. Add structured manual checks and signal-scoped outcome/snooze inputs. Show agreed deadlines separately from optional proactive actions. Update the selected account and queue after a committed workflow change.
7. Apply agent events through the existing `core/events/router.ts`. Resolve selections even when the customer is outside the loaded page; clear incompatible filters or explicitly load that account. Reuse the constrained artifact renderer.
   Persist only the active conversation ID client-side and load its normalized history from our chat-history endpoint. Add a new-conversation action; preserve the thread across route changes and drawer closure. Update chat context on every turn rather than assuming checkpointed filters/customer selection are still current.
8. Verify desktop/mobile layouts, keyboard access, empty/loading/error states, unknown-data messages and the complete demo. Voice stays deferred unless the end-to-end core is finished.
9. Reuse the template ReAct agent and async SQLite lifecycle; configure the requested OpenRouter model and root `.env`; own history/thread recovery and tool-run receipts. Wrap Members 1/2/3 services in registered tools, keeping business logic in their owning modules.
10. Build the workspace-context/control registry described in §4G: agent reads the active page/tab, customer, visible metrics, filter values/options, chart settings, sorting/pagination, source dates and available controls. It can answer about any of the three pages and manipulate the current page through validated commands.
11. Own artifact creation/update and on-demand analysis. Start with service-backed plots/tables/calculations; add Daytona-backed Python/bash execution when computation needs code. Reuse the template sandbox/file/artifact capability; do not run generated code in the app server or browser.

## 3. What already exists and should be reused

| Existing asset | Reuse / caution |
|---|---|
| Current Next.js/FastAPI mock | Runnable baseline; preserve during integration |
| `frontend/src/types/sales.ts` and Python sales `models.py` | Current v1 shapes; v2 changes below are proposed, not implemented yet |
| `core/events/router.ts`, `realtime/publisher.py` | Retain the command envelope and one event boundary |
| SQLite follow-ups + contract tests | Extend instead of replacing |
| `analysis/export_customer_data.py` | Starting SQL queries; use full stable IDs and expand evidence coverage |
| `analysis/train_customer_models.py` | Existing time-based activity/volume comparisons and KMeans; split into Member 2 models and Member 3 peer/ranking logic |
| `analysis/customers/dashboard_data.json` | Existing historical results, **as of 31 Aug 2026**, targeting Sep–Nov 2026 |
| `hackathon-template/` at the supplied local path | Aditya + Codex reuse agent/tools/checkpoints/sandbox; dependencies must be copied into this repo, not left as absolute-path imports |

The saved historical output contains 6,515 accounts under its extraction filters and 3,321 model-supported accounts. Its selected activity model is logistic regression with isotonic calibration; its selected volume predictor is the previous 12 months divided by four. These are starting results to reproduce, not proof that all future customers/horizons are supported.

The mock is dated 30 September and has fictional companies. **Do not relabel the August historical extract as September.** Default to its explicit historical reference date unless Member 1 verifies a newer complete snapshot and Member 2 generates predictions for that snapshot. Source freshness, forecast origin and workflow date are different concepts.

## 4. Shared data contract — freeze before parallel implementation

### Ownership and conventions

Member 1 owns shared Pydantic models under proposed `backend/app/contracts/sales_v2.py`; Aditya mirrors them in TypeScript. Members 2/3 import these models and produce JSON-valid outputs. Agree on field changes before coding them; a PR changing a response also updates models, a small synthetic fixture and the frontend adapter.

- New read API prefix: `/api/v2`. Existing `/api/*` endpoints remain functional during transition. The current Next.js rewrite maps `/api/sales/v2/...` to Python `/api/v2/...`.
- `contract_version: "2"` appears in read responses. `/api/contracts` continues to describe v1; add `/api/v2/contracts` for complete v2 response/command schemas.
- IDs are opaque strings, consistent across every export, prediction, action and workflow. Do not truncate hashes without collision checks. Keep source-ID mappings private; hashed IDs are pseudonymous, not automatically anonymous.
- Dates: `YYYY-MM-DD`; months: `YYYY-MM`; timestamps: ISO UTC, except existing event `timestamp` which remains epoch milliseconds.
- Use `null` for unknown/unsupported. Zero means measured/predicted zero, not missing. No NaN/Infinity. No fabricated company names, account owners or commercial amounts.
- Probabilities/prevalence/components are `[0,1]`; counts are nonnegative integers; predicted expected counts may be fractional. Score is `[0,100]`; correlations are `[-1,1]` or null.
- Every artifact shares `snapshot_id`, reference date and model/rule version. Reject mismatched snapshots instead of silently joining them.

### A. Member 1 → Members 2/3: normalized snapshot

These are local tables/JSON snapshots, not whole datasets passed through chat. The filename layout can be JSON/Parquet according to size; the row meanings below are fixed.

```ts
type MonthlyHistoryRow = {
  customer_id: string; month: string;
  calibration_events: number; distinct_instruments: number;
  equipment_group_count: number; lab_count: number;
};
type CustomerProfile = {
  customer_id: string; display_name: string;
  name_source: "verified" | "identifier";
  industry_id: string | null; industry_label: string | null;
};
type PortfolioRow = {
  customer_id: string; group_id: string; group_label: string;
  distinct_instruments: number; calibration_events: number;
  window_start: string; window_end: string;
};
type InstrumentRecord = {
  instrument_id: string; current_customer_id: string | null;
  group_id: string | null; last_calibration_date: string | null;
  recorded_due_date: string | null;
  nominal_interval_months: number | null;
  stopped: boolean | null; quality_flags: string[];
};
type InstrumentEvent = {
  event_id: string; instrument_id: string; historical_customer_id: string;
  calibration_date: string; group_id: string | null;
};
type SnapshotManifest = {
  snapshot_id: string; extracted_at: string; reference_date: string;
  complete_through_month: string; history_start: string;
  source_tables: string[]; row_counts: Record<string, number>;
  field_coverage: Record<string, number>; quality_flags: string[];
};
```

Optional order-position history: `{customer_id: string | null, month: string, delivered_order_positions: number, time_basis: "receipt" | "delivery", coverage: number}`. Member 1 must justify customer attribution and timestamp semantics. Delivery history is not automatically demand-arrival history. Missing receipt timestamps are not silently replaced by delivery dates in a single series.

Member 1 also exports instrument-group labels and industry labels and an ordered complete month grid. Months with zero events within verified covered history are zero-filled; periods before observed tenure/uncovered source periods remain distinguishable.

### B. Member 2 → API/Member 3: prediction outputs

```ts
type Support = {
  status: "supported" | "insufficient_history" | "unavailable";
  reason: string | null; history_months: number; active_months: number;
};
type VolumeForecast = {
  metric: "calibration_events" | "order_positions";
  horizon_months: 3; window_start: string; window_end: string;
  expected_total: number | null;
  lower: number | null; upper: number | null;
  interval_level: number | null;
  monthly: null | {
    month: string; expected: number;
    lower: number | null; upper: number | null;
  }[];
  method: string; model_version: string; support: Support;
};
type CustomerPrediction = {
  snapshot_id: string; customer_id: string; reference_date: string;
  segment_id: string | null;
  activity: {
    target: "any_calibration_next_3_months";
    probability: number | null; window_start: string; window_end: string;
    model_version: string; support: Support;
  };
  calibration_volume: VolumeForecast;
  recency_months: number | null; cadence_months: number | null;
  inactivity: {
    flagged: boolean; recency_to_cadence: number | null;
    recent_volume: number; baseline_volume: number | null;
    deficit_fraction: number | null; rule_version: string;
    reasons: string[]; support: Support;
  };
  explanation: {feature: string; value: number; contribution: number | null}[];
};
type SegmentSummary = {
  id: string; label: string; method: "kmeans";
  customers: number; description: string;
  feature_means: Record<string, number>;
};
```

`contribution` is only supplied when computed for the actual model; metadata specifies its scale (e.g. log-odds), not a fabricated probability contribution. Human-readable flags can explain a rule without claiming to explain a supervised model.

Member 2 publishes `predictions.json`, `segments.json`, `sectors.json`, `model_report.json` plus a manifest under `data/runtime/analytics/<snapshot_id>/`. Publication is atomic after successful validation. API serving loads a validated snapshot once; **no model training on page loads or chat requests**.

Model report includes target/units, feature and label windows, train/calibration/validation/test periods, eligibility and coverage, selected method, baseline metrics, and sample counts. Activity metrics: ROC AUC, average precision, Brier/reliability. Volume metrics: MAE, WAPE when denominator is nonzero, and bias. Overlapping customer-origin observations are not independent people; describe the evaluation unit and avoid overconfident error bars.

### C. Member 1/3 → UI: requirements, actions and preparation

```ts
type Requirement = {
  id: string; customer_id: string; instrument_id: string;
  group_id: string | null;
  kind: "recorded" | "nominal_interval" | "repeat_history" | "unknown";
  window_start: string | null; window_end: string | null;
  method: string; evidence_dates: string[]; positive_gap_count: number;
  stopped: boolean | null;
  eligibility: "review_required" | "eligible" | "excluded";
  unknowns: string[];
};
type ActionReason = {
  id: string; // deterministic account + type + instrument/group basis
  type: "upcoming" | "inactivity" | "discovery";
  title: string; explanation: string;
  evidence_refs: string[]; instrument_ids: string[];
  quantity: number | null;
  quantity_unit: "instruments" | "calibration_events" | "categories" | null;
  window_start: string | null; window_end: string | null;
  status: "review_required" | "eligible" | "suppressed";
  suppression_reason: string | null; unknowns: string[];
};
type AccountAction = {
  snapshot_id: string; customer_id: string;
  primary_type: "upcoming" | "inactivity" | "discovery";
  reasons: ActionReason[]; priority_score: number;
  components: {
    timing: number | null; quantity: number | null;
    activity_deviation: number | null; evidence: number | null;
  };
  ranking_version: string; weights: Record<string, number>;
  readiness: "review_required" | "eligible";
  suggested_next_step: string;
};
type PeerOpportunity = {
  group_id: string; group_label: string; industry_id: string;
  peer_count: number; peers_with_group: number; prevalence: number;
  window_start: string; window_end: string;
  question: string; evidence_refs: string[];
};
type PreparationCard = {
  customer_id: string; reference_date: string;
  facts: {text: string; evidence_refs: string[]}[];
  unknowns: string[]; questions: string[]; suggested_next_step: string;
};
```

An account can have several reason types. `action=upcoming` matches an unsuppressed upcoming reason, not only the account's primary reason. Instrument quantities are deduplicated per account/window. Actions without supported reasons are absent from the proactive queue; the customer remains searchable.

### D. API → frontend: screen responses

All v2 reads contain `contract_version`, `snapshot_id`, `reference_date` and `mode: "mock" | "historical"`. Workflow date is supplied separately as `workflow_today`. Each module advertises `ready | unavailable` with a reason, preventing partial backend merges from breaking the UI.

| Python endpoint | Response / important fields | Owner |
|---|---|---|
| `GET /api/v2/bootstrap` | Metadata; module readiness; filter options; segment summaries; dashboard KPI values with units; first 10 proactive account actions; due follow-ups; sector payload | Member 1 composes 1/2/3 outputs |
| `GET /api/v2/customers` | `{items: CustomerSummary[], total: number, limit: number, offset: number}` plus metadata. Filters: `industry_id`, `segment_id`, `action`, `query`, `sort=priority\|name`, `limit` (max 100), `offset` | Member 1, using Member 3 actions |
| `GET /api/v2/customers/{id}` | `{profile: CustomerProfile, history: MonthlyHistoryRow[], portfolio: PortfolioRow[], requirements: Requirement[], prediction: CustomerPrediction\|null, action: AccountAction\|null, peer_opportunities: PeerOpportunity[], preparation: PreparationCard, workflow: AccountWorkflow}` plus metadata | Member 1 composes; Member 3 prepares |
| `GET /api/v2/sectors` | Industry IDs/labels; monthly calibration history; sector forecasts; correlation definition below; peer/window coverage | Member 2 builds; Member 1 serves |
| `GET /api/v2/model-report` | Versioned evaluation report and coverage, not model binaries | Member 2 builds; Member 1 serves |
| `GET /api/v2/followups` | `{items: Followup[]}` and workflow date | Member 1 |
| `GET /api/v2/contracts` | Pydantic JSON schemas for all v2 responses, writes and UI commands | Member 1 |

`CustomerSummary` is `{profile: CustomerProfile, segment_id: string|null, primary_action: AccountAction|null, recency_months: number|null, activity_probability: number|null}`. IDs in filter options come from the same snapshot. Exact matching is case-sensitive for IDs; text search is case-insensitive. Reset means omit filter parameters. Empty matches are `200` with an empty list; unknown customer IDs are `404`.

Sector correlation payload:

```ts
type SectorCorrelation = {
  industry_ids: string[]; labels: string[];
  values: (number | null)[][];
  pair_sample_counts: number[][];
  method: "pearson_log1p_monthly_change";
  window_start: string; window_end: string;
  warnings: string[];
};
```

Matrices are square, symmetric and ordered by `industry_ids`; pair counts describe actual common observations. A diagonal can be null for inadequate/constant series. The heatmap must not turn null into zero correlation. Sector forecasts and correlations remain separate fields/methods.

### E. Workflow writes and events

Preserve the existing `POST /api/followups` and `PATCH /api/followups/{id}` shapes and events for compatibility. Add version 2 writes for richer inputs:

```ts
type Followup = {
  id: string; customer_id: string; customer_name: string;
  owner: string; due_date: string; note: string;
  outcome: "Timing to confirm" | "Timing changed" | "Need confirmed"
    | "Not applicable" | "Equipment retired";
  status: "open" | "done"; source: "mock" | "manual";
};
type AccountWorkflow = {
  account_owner: string | null; // validated owner, separate from action owner
  checks: {
    quotation_order: "unknown" | "reported_none" | "in_progress";
    recent_contact: "unknown" | "checked";
    contact_details: "unknown" | "supplied";
    checked_at: string | null; checked_by: string | null;
  };
  suppressions: {
    reason_id: string; status: "snoozed" | "resolved";
    until: string | null; note: string; updated_at: string;
  }[];
  followups: Followup[];
};
```

- `POST /api/v2/followups`: existing create fields plus optional `reason_ids: string[]`; returns committed `followup.created` envelope, HTTP 201.
- `PATCH /api/v2/followups/{id}`: `{status: "open" | "done"}`; returns `followup.updated` envelope. Repeated same-state updates are safe.
- `PATCH /api/v2/customers/{id}/workflow`: optional `checks` and/or one `suppression` record; validates customer/reason IDs, dates and scope; returns `customer.workflow.updated` with `{customer_id, workflow, action}`. Aditya adds that event to the frontend router.
- A snooze requires an end date. Resolution requires a note. Persist changes with timestamps; keep a simple audit history. A retirement outcome requires explicit instrument scope and manual provenance; do not mark the entire account or update the source DB implicitly.

Readiness rules are shared with Member 3. Workflow facts are manually supplied unless a later integration verifies them. Anonymous workflow users/owners are acceptable for the local demo; do not imply production authentication exists.

Errors: unknown records `404`, Pydantic validation `422`, unavailable required snapshot/model `503` with a useful detail. Writes return only after commit; frontend must not show success for an unsuccessful request.

### F. Assistant and chart contract

Keep current `POST /api/chat` and the existing assistant-ui external-store runtime first. Add optional `snapshot_id` and `thread_id` to its context during contract freeze; preserve existing fields. Return the resolved `thread_id` so the frontend can resume it. An agent response changes `mode` to `"agent"`; explicitly selected scripted demo mode remains `"scripted_mock"`. Provider errors must not silently become a successful scripted answer.

```ts
type ChatRequest = {
  message: string;
  context: {
    page: "dashboard" | "customers" | "follow-ups";
    customer_id: string | null;
    filters: {industry: string | null; segment: string | null;
      action: "all" | "upcoming" | "inactivity" | "discovery" | null;
      query: string | null};
    snapshot_id?: string; thread_id?: string;
  };
};
type ChartArtifact = {
  id: string; title: string; kind: "bar" | "line";
  labels: string[]; datasets: {name: string; values: number[]}[];
  unit: "calibrations" | "instruments" | "customers" | "order_positions";
  source: "mock" | "historical" | "model";
  reference_date?: string; snapshot_id?: string;
};
type EventEnvelope = {
  id: string; type: string; timestamp: number;
  source: {type: "user" | "agent" | "backend" | "frontend"};
  payload: object;
};
type ChatReply = {
  message: string; mode: "scripted_mock" | "agent";
  thread_id: string;
  events: EventEnvelope[]; artifacts: ChartArtifact[];
};
```

For chat filters, `industry`/`segment` carry the v2 industry/segment **IDs** (legacy field names retained), and `"all"` means reset. Member 1 updates command validation from the mock's fixed segment enum; Aditya updates its event handler at the same merge. HTTP list filters use `industry_id`/`segment_id` explicitly.

Preserve command names/payloads: `ui.navigate {page}`, `customers.filters.set {partial filters}`, `customers.select {customer_id}`, `artifact.created {ChartArtifact}`. Chart arrays must have equal lengths; max 50 labels/five datasets initially. Missing points must be omitted/aligned rather than replaced with invented zeroes. No generated executable JS, SQL or arbitrary ECharts option objects. Heatmap is an existing frontend view, not a new arbitrary chart tool.

Aditya + Codex own registry tools: list/filter accounts, read customer evidence/prediction, retrieve ranked actions, retrieve peer opportunities, prepare a conversation, navigate/select/filter, and create a bar/line chart from approved metrics. They wrap Member 3's insight services alongside Members 1/2's evidence/prediction services. Saving/suppressing outcomes remains an explicit form action for this hackathon; the assistant can prepare the proposed change but does not infer user confirmation from conversational context.

HTTP replies with event receipts and persistent thread history are the core integration target. Streaming/SSE/voice can be added after it works; do not introduce a second agent or incompatible event path.

#### Required ReAct agent and SQLite checkpoint implementation

Aditya + Codex own the agent/checkpoint lifecycle, chat routes and conversation serialization. Member 1 coordinates its lifespan/router wiring into the FastAPI app and adds the agreed dependencies: `langchain`, `langgraph`, `langchain-openai`, `langgraph-checkpoint-sqlite`, and the environment loader (reuse template settings or `python-dotenv`). Pin compatible resolved versions in `uv.lock`; async SQLite also needs `aiosqlite`, supplied by the saver package or explicitly declared if directly imported.

Reuse the template's `backend/app/agents/react_agent.py`: it already uses `create_agent`, `ChatOpenAI` pointed at OpenRouter and `AsyncSqliteSaver`. Use the current factory [documented by LangChain](https://docs.langchain.com/oss/python/langchain/agents) rather than implementing a separate reasoning/tool loop. The user-requested persistence package is [LangGraph SQLite checkpointing](https://reference.langchain.com/python/langgraph.checkpoint.sqlite), whose [async saver source](https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint-sqlite/langgraph/checkpoint/sqlite/aio.py) supports this lifecycle.

Backend configuration:

```text
OPENROUTER_API_KEY=<already supplied locally; never commit>
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=meta/muse-spark-1.3-contributor
CHECKPOINT_PATH=data/runtime/chat-checkpoints.sqlite3
```

The key was confirmed present in the root `.env` without displaying its value. Backend settings must load that file using a repository-root path, regardless of working directory. Environment variables take precedence. Do not use `NEXT_PUBLIC_` for secrets or require a second copy in `backend/.env`. The model is listed on [OpenRouter](https://openrouter.ai/meta/muse-spark-1.3-contributor); Aditya + Codex still perform an actual synthetic tool-call smoke test with the supplied account before integration. Preserve the exact model ID; surface account/provider errors rather than silently changing the model. The existing adapter can use OpenRouter's [OpenAI-compatible API](https://openrouter.ai/docs/quickstart).

Implementation outline (configuration/lifecycle sketch, not implemented code):

```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

# Keep this async context open for the application's lifespan.
async with AsyncSqliteSaver.from_conn_string(checkpoint_path) as saver:
    model = ChatOpenAI(
        api_key=settings.openrouter_api_key,
        base_url="https://openrouter.ai/api/v1",
        model="meta/muse-spark-1.3-contributor",
    )
    agent = create_agent(model, tools=registered_sales_tools, checkpointer=saver)
    # Per-turn invoke: only the new message; history is already checkpointed.
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": request.message}]},
        config={"configurable": {"thread_id": thread_id}},
        context=current_workspace_context,
    )
```

Add a typed `context_schema` for `current_workspace_context`; use it in tools so every request has the latest page, selected customer, filters and snapshot. Reuse the template's tested lifecycle rather than copying this sketch without settings/prompts/error handling. Retain one active run per thread, bounded tool/model calls and request timeouts. Keep UI receipts scoped to the current run so concurrent threads cannot collect each other's events. Historical tool messages must not re-execute operations on restore.

Proposed history endpoint owned by Aditya + Codex:

```text
GET /api/chat/threads/{thread_id}/messages
-> {thread_id: string, items: ChatHistoryMessage[]}
ChatHistoryMessage = {
  id: string, role: "user" | "assistant", text: string,
  artifacts?: ChartArtifact[], actions?: string[]
}
```

Generate a UUID thread on first chat when omitted and return it in `ChatReply`. The frontend stores that ID and reads messages on reload; “New conversation” clears its active ID and begins another thread on the next turn. Persist displayable artifact/action metadata with the conversation state or a small associated runtime table; do not expose internal reasoning/tool payloads as user messages. Returning restored action labels is presentation only, never dispatching old events again. SQLite workflow records and agent checkpoints live in separate files with separate owners/lifecycles.

Conversation tests: multi-turn recall; same-thread recovery after app restart; different-thread isolation; no duplicated/replayed UI events after history restore; current workspace context overrides stale selection; provider failure is clearly reported. Use synthetic prompts for provider tests and minimal account evidence for normal tool responses.

### G. Current-page context, control tools and optional Daytona analysis

This section is owned end-to-end by **Aditya + Codex**. Members 1/2/3 expose typed, queryable facts so the agent and UI answer from the same source. “Complete page context” means the semantic state and available capabilities of all three pages, with current visible data and access to details; it does not mean dumping every customer/instrument row into each model prompt.

Extend `ChatRequest.context` with a `workspace` snapshot:

```ts
type WorkspaceContext = {
  state_revision: number; page: "dashboard" | "customers" | "follow-ups";
  active_tab: "activity" | "portfolio" | "next-step" | null;
  snapshot_id: string; reference_date: string;
  selected_customer_id: string | null;
  visible_customer_ids: string[];
  filters: {industry: string; segment: string; action: string; query: string};
  list: {sort: "priority" | "name"; offset: number; limit: number; total: number};
  action_limit: number;
  followup_status: "open" | "done" | "all";
  charts: {
    id: string; title: string; metric: string; unit: string;
    kind: string; window_start: string | null; window_end: string | null;
    series_ids: string[]; source: "mock" | "historical" | "model";
  }[];
  controls: {
    id: string; label: string; kind: "select" | "search" | "tab" | "number";
    value: string | number;
    options?: {value: string; label: string}[];
    min?: number; max?: number;
  }[];
  visible_summary: {id: string; label: string; value: number | null; unit: string}[];
  artifact_ids: string[];
};
```

Aditya's frontend creates this context from the same Zustand/component state used to render the screens; keep tab/plot controls in shared state so the agent can read/change them. No separate stale parallel UI state. Backend validates IDs/control values and resolves displayed facts from the supplied snapshot; UI-provided labels/counts provide context, not authority over source records.

Register tools such as `get_workspace_context`, `describe_page`, `query_customer_data`, `get_customer_evidence`, `get_prediction`, `get_ranked_actions`, `get_sector_data`, `get_peer_opportunities`, `prepare_conversation`, `set_customer_filters`, `select_customer`, `set_workspace_control`, `create_chart`, `update_chart`, `remove_artifact`. The page registry documents all three layouts, metrics and available controls even when inactive. Query tools have approved metrics/aggregation/filter inputs, row limits and unit definitions; no general SQL execution tool.

Extend commands with `ui.control.set {control_id, value, expected_revision}`. Allow only registered controls: customer detail tab, shortlist limit, list sort/page, follow-up status and supported chart selectors. Filter/dropdown commands use exact option IDs. Add `artifact.updated`/`artifact.deleted` with validated artifact IDs/specs; frontend keeps one artifact store and renders them through its registry. Existing heatmap remains its own known renderer. New artifact kinds require a typed renderer/contract, not arbitrary HTML/JS injection.

Use command IDs/revisions for application receipts. Frontend applies only valid commands, acknowledges `applied`/`rejected` with a reason, and the chat shows successful manipulation only after application. A stale revision returns a useful retry result rather than overriding a newer user selection. No DOM clicking is required to operate our own app: commands update the actual state behind dropdowns/plots/pages.

Acceptance scenarios: “Why is this account flagged?” refers to the selected customer; “Explain this plot” identifies its metric/horizon/source; “Only show automotive inactive accounts” changes both controls; “Switch to portfolio” selects the right detail tab; “Plot monthly activity for these accounts” creates a supported artifact; switching pages during a conversation updates the next turn's context.

**Optional code execution:** the user supplied `DAYTONA_API_KEY` in the root `.env`, verified present without displaying it. Reuse the template's `capabilities/shell/`, file transfer and artifact implementation with the [Daytona Python SDK](https://www.daytona.io/docs/en/python-sdk/) and [process/code execution](https://www.daytona.io/docs/en/process-code-execution/). The supplied dashboard URL is a management page, not an API base URL.

- Reuse one sandbox per conversation with the thread/sandbox mapping recorded locally. Execute Python or bash there for an on-demand calculation, CSV, figure or report; UI manipulation still uses typed commands, not sandbox browser scripts.
- Upload only a scoped, approved data slice returned by query tools plus its manifest/units. Do not forward root `.env`, source credentials or the whole database. Generated code cannot edit the application repository or write SQL source records.
- Return exit status, bounded output and typed artifact references. Pull artifacts back through the backend file service before displaying them. Handle timeouts/provider unavailability; recover produced files before stopping/cleanup. Use existing template lifecycle behavior.
- Begin with charts from structured queries. File artifacts can later use `artifact.file.created` with `{id, title, mime_type, download_url, source, snapshot_id, reference_date}`; render safe image/table/file previews through registered components. Generated HTML, if supported, requires a separate sandboxed preview; never insert it as executable page markup.

Daytona execution is an enhancement to our agent, not another teammate's training/runtime pipeline. Backend members still train offline and supply reproducible outputs. Its absence must not disable standard evidence tools, filters or chart creation.

## 5. Internal module boundaries and build order

No circular imports. Data services do not import analytics/agents. Analytics consumes normalized snapshot rows; insights consumes profiles/requirements/predictions/workflow. A composition service owned by Member 1 joins their outputs; tools call that service. Keep heavier training code outside API startup.

Agree on these callable seams in hour 1 (names below are proposed):

```text
data.service.load_snapshot(snapshot_id) -> normalized snapshot + manifest
data.service.get_customer_profile(customer_id) -> profile/history/portfolio/requirements
data.service.get_workflow(customer_id) -> AccountWorkflow
analytics.service.load_outputs(snapshot_id) -> validated immutable outputs
analytics.service.get_prediction(customer_id, snapshot_id) -> CustomerPrediction | None
analytics.service.get_sectors(snapshot_id) -> sector payload
insights.service.build_account_action(profile, requirements, prediction, peers, workflow) -> AccountAction | None
insights.service.build_preparation(profile, action, peers, workflow) -> PreparationCard
agents.sales.reply(ChatRequest) -> ChatReply
```

Member 3 starts peer analysis and actions on small **shared synthetic fixtures**, not on Member 2's internal features. The composition layer calls pure insight functions; Aditya + Codex's agent calls the composition API/service rather than insights importing API routes. This allows data → analytics → insights outputs to evolve without everyone editing the same `service.py`.

Each backend member creates a module README with the run command, required inputs, output models, limitations and one representative fixture. Tests stay under member-specific filenames/directories. Shared synthetic fixtures are in `data/mock/`; real exports/models stay under ignored `data/runtime/`. Team members need the same approved extract or independent read-only SQL access; cloning code alone does not supply the data.

## 6. Clone, commit and merge workflow

**Current filesystem check:** this workspace is not yet a Git repository and has no remote configured. Treat the current runnable setup as the intended `main` baseline. The repository owner must create/publish the team repo and commit this baseline before members can clone it. Do not include credentials, runtime databases, real extracts or model binaries in that first commit; review tracked files, including existing analysis outputs, before publishing.

Member onboarding after the repo exists:

```bash
git clone <team-repository-url>
cd <repository-folder>
git switch main
git pull --ff-only origin main
git switch -c feat/data-api       # Member 1
# Member 2 uses feat/ml-analytics; Member 3 uses feat/sales-intelligence
uv sync
cd frontend
pnpm install
cd ..
bash scripts/dev.sh
```

Supply SQL/LLM secrets locally via ignored environment/config; never paste credentials into this plan, a commit or a PR. Member 1 documents ODBC/network requirements and the authorized local snapshot location. Source queries are read-only; workflow writes go to local SQLite.

### Merge order — small increments, not three huge final merges

| Order | PR / integration | Owner and required proof |
|---|---|---|
| 0 | Publish runnable mock baseline; freeze schemas, module seams and small fixtures; extract chat routing ownership; add v2 skeleton | Aditya + Member 1. Chat/agent/registry belong to Aditya + Codex; all branches start from this contract commit |
| 1 | Data profiles/history/requirements + workflow API; keep mock mode selectable | Member 1: source checks, endpoint responses, persistence; Aditya connects customer evidence/form |
| 2 | Analytics outputs + evaluation report | Member 2: reproducible offline results and baseline comparisons; Member 1 adds loader/composition; Aditya connects segments/plots/sectors |
| 3 | Peer discovery + account actions + corrections affecting ranking | Member 3: evidence/quantity/suppression tests; Member 1 composes; Aditya connects dashboard queue/opportunity cards |
| 4 | Template ReAct agent + SQLite checkpoints + page context/tools/artifacts | Aditya + Codex on main: grounded chat, restart/history and applied UI receipts; Member 1 coordinates app wiring |
| 5 | Final integrated demo and regression fixes | All four, with Aditya owning merge/build/demo verification |

Member 3 can deliver peer/ranking fixtures before analytics is merged. Aditya + Codex build the checkpointed agent and workspace tools against fixtures in parallel; connect production data after the service PRs merge. While a module is unavailable, show its unavailable state or remain entirely in mock mode. Keep each UI mode coherent.

Before a PR, commit your work, fetch `origin`, and merge `origin/main` into your branch; avoid rebasing a shared branch or force-pushing. Resolve conflicts with the owning member. PR body: implemented features, touched contracts, setup requirements, representative response and tests. Aditya merges after review/checks, then everyone syncs `main` back into their branches.

## 7. Sixteen-hour working schedule

Times are relative to implementation start; all backend tracks run in parallel.

| Time | Aditya | Member 1 | Member 2 | Member 3 |
|---|---|---|---|---|
| 0–1 h | Freeze UI/agent contracts and publish baseline | Shared schemas, normalized fixture, v2/chat route ownership | Inspect current benchmark; agree input/outputs | Inspect existing peer/ranking logic; agree insight shapes |
| 1–4 h | Reuse ReAct/checkpoint agent; provider test; dynamic filters | Snapshot/profile/history/requirements and first API PR | Reproduce features/clusters/activity baselines | Peer discovery, ranking and preparation on fixtures |
| 4–8 h | Current-page context, UI commands, history restore; data UI | Persistence, corrections/checks; endpoint composition | Volume forecasts, coverage, inactivity, model report | Action bundling/suppression; first insight PR |
| 8–11 h | Queue/plots, registered service tools, grounded chat | Wire validated analytics/insights snapshots | Sector forecast/correlation; publish analytics PR | Real-data peer/preparation validation; evidence aggregations |
| 11–13 h | Artifact controls/export; optional Daytona; full workflow | API edge cases; reproducible refresh | Backtest/unsupported cases; chart-ready outputs | Ranking/unknown handling and insight integration fixes |
| 13–16 h | Integrated browser/chat checks, UX and demo | Integration fixes | Metrics/data audit | Insight/demo fixes |

Reserve the final three hours for integration and presentation. If delayed, cut voice/streaming first, then multivariate/next-order-time work, then extra horizons. Keep one validated forecast target, due-date evidence, useful ranking, industry discovery, working chat commands and the full correction/follow-up cycle.

## 8. Definition of done

- Every member's code runs after clone with documented dependencies and access to the approved snapshot; no absolute imports from one person's home directory.
- Contract fixtures validate in Python and match frontend types; null, empty lists, sparse accounts and unavailable modules render correctly.
- Extraction checks attribution, duplicates, unit meanings, source cutoff and instrument-date support. Actual rows are never mixed with synthetic predictions without explicit separation.
- Model results can be reproduced with a fixed seed and dataset version; baselines, holdout periods and coverage are available for judges. No unsupported churn/revenue claims.
- The queue explains quantity and timing, exposes unknown checks, respects stop/snooze/corrections and groups account reasons without double-counting.
- Chat uses the requested OpenRouter model and LangChain/LangGraph ReAct agent; answers cite evidence dates; filtering/selection/navigation/chart commands visibly update the UI through the existing router. Async SQLite checkpoints recover the conversation after restart without repeating UI actions or crossing thread boundaries.
- A representative records “timing changed”, saves the next step, suppresses only the old reason and sees the persisted follow-up after reload. Another valid reason stays visible.
- Python contract/capability tests pass; `pnpm typecheck` and `pnpm build` pass; desktop/mobile browser flow passes. Stop the dev server before production build because both use `.next`.
- Final demo runs from the local snapshot; source/reference/model dates and mock/historical/agent states are visible.

### Start here

**Aditya + Codex:** publish the baseline, agree v2 contracts with Member 1, and own the checkpointed chatbot, page context, workspace controls and artifacts. **Member 1:** produce the normalized snapshot and API/workflow skeleton. **Member 2:** reproduce the existing benchmark and export typed predictions/sector data. **Member 3:** build peer/ranking/preparation and explainable evidence services against the agreed fixture, then validate them on the shared snapshot.


## 9. Proposed opportunity dashboard redesign — 7 October 2026

Status: planning only; this request updates the plan rather than the application. Main was clean and checkpointed first at `04b1182` (after `63b6217`). This section supersedes the earlier dashboard layout proposal after review.

### Manager workflow and layout

The Dashboard becomes an action workspace: filter a market/service cohort → inspect the opportunity map → select a cluster → review four scoped metrics → inspect a priority-sorted account shortlist → open an account or ask Pulse to act on the selected group. Existing frequency/volume segments remain attributes and optional filters; they never define opportunity-cluster membership.

Order: compact page title and filters, large 2D opportunity map with a clickable four-color legend, four selection-dependent metric cards, deadline/unassigned attention strip, then the ranked account table with action controls and a preparation drawer. Cluster selection has an obvious All opportunities reset and a compact label showing the selected group and account count. No decorative demo profile or source banner is restored.

Proposed top-level navigation remains three tabs: Dashboard, Customers, Insights. Move sector history, correlation, next-month sector outlook and model quality into Insights. Follow-ups become a Customers subview and remain accessible from the Dashboard follow-up card. Preserve existing `/follow-ups` links and agent navigation during the transition. This keeps the earlier three-tab limit while adding the requested analytics page.

### Agreed Dashboard contents

Primary question: **Which customers should the team act on next, why, and who will handle them?** Implement the following screen composition, reusing the existing services and components:

1. **Filters:** sector/industry, equipment category, behavioral segment, opportunity purpose and due window. Keep advanced evidence and display controls compact.
2. **Opportunity map:** customer points on urgency (X) and opportunity size (Y), with four evaluated clusters or clearly identified priority zones if clustering is unstable. Clicking a group selects its whole filtered cohort; clicking a customer opens evidence. Provide an All opportunities reset.
3. **Four scoped cards:** upcoming due instruments, expected next-three-month calibration volume, accounts needing inactivity review, and open follow-ups with overdue count. Show forecast coverage/target dates where relevant. Optional financial-scenario mode replaces the demand value with estimated contribution from supplied assumptions, retaining the quantity basis.
4. **Attention strip:** overdue follow-ups and timely opportunities without an assigned owner; each links to the relevant account/action rather than creating a second uncoordinated queue.
5. **Ranked customer table:** customer identifier/name when supplied, sector, behavioral segment, opportunity reason, relevant quantity, activity-review signal, priority, owner and suggested next action. Offer supported return probability with its target window as secondary detail. Keep evidence/readiness badges visible.
6. **Preparation drawer:** relevant history and instruments, why this account is flagged, supported forecasts, unknown checks and conversation questions. Support ownership, confirmed outcome and next-follow-up entry without losing the map selection.
7. **Action toolbar:** select five/ten/custom accounts, save the shortlist and export a handover brief. Full time-budget planning follows the core workflow; required effort assumptions must be supplied rather than inferred from the extract.
8. **Pulse drawer:** preserve streaming Markdown, returned reasoning, tool traces and conversation memory. Ground answers and typed filter/cluster/chart actions in the current page, selection and visible metrics; only registered, data-supported chart types are available.

Sector activity, sector-movement correlation, next-month sector outlook and model quality belong on **Insights**. The Dashboard should not duplicate those charts. Keep the initial manager screen minimal; financial scenarios, time-budget planning and outcome analytics must not delay the core selection → preparation → owner/next-step workflow.

Acceptance: selecting a cluster or changing a filter updates all four cards, attention counts and table against the same full cohort; drawing fewer points does not change totals. Closing the preparation drawer preserves selection. Persisted ownership/follow-up changes refresh affected actions, readiness and counts without changing the historical forecast reference date. Unknown forecasts/financial inputs show an unavailable state. Pulse reports the same labels, units, periods and values as the page.

### What the local data actually supports

Current selected snapshot is `historical-full-20260831-v2`, history ending 31 August 2026. Saved predictions contain 6,564 accounts; 3,180 have supported three-month activity and volume predictions; 4,003 have supported inactivity evidence, with 1,805 flagged for review. Existing behavioral clustering assigns 4,113 accounts across three segments; opportunity clustering will be a separate model. These counts describe the saved artifacts, not a refreshed production database.

Activity means at least one calibration at this provider in September–November 2026. Customer volume has 65.05% holdout WAPE and is directional. We have due-date tiers, instrument IDs/groups, observed calibration quantities, industry, cadence, volume deficit, peer discovery, local follow-ups and transparent ranking. Confirmed churn, quotation conversion, distinct future orders, prices/costs/margins and incremental outreach benefit are unavailable.

### Two axes and engineered features

Use two understandable axes, each scaled 0–100:

- **X: action urgency** — how soon a supported need needs attention, or how unusual the activity slowdown is.
- **Y: opportunity size** — a quantity-based proxy for the scale of a relevant conversation. It is a score, not euros, expected profit or an uplift estimate.

Build independent components before fitting clusters. Proposed rules are business assumptions to evaluate and version, not learned commercial returns:

1. **Due quantity D:** unique unstopped, unsuppressed instruments with a supported requirement overlapping the chosen next 30/60/90 days. Recorded evidence dominates inferred evidence for the same instrument. Keep separate counts and evidence strength; unknown dates do not enter D. Past-due records form a separate review toggle and require confirmation.
2. **Activity gap G:** `max(0, prior_year_quarterly_average - recent_3_month_calibrations)` only when inactivity evidence is supported and flagged. This is an observed activity gap against a baseline, not recoverable orders or lost revenue.
3. **Discovery scale H:** prior-12-month observed calibration volume for accounts with a sufficiently supported peer-discovery reason. It estimates account scale, not ownership of missing equipment or cross-sell conversion.
4. Normalize each quantity channel independently using a frozen source-population log transform and a robust upper percentile. Clip scores to [0,100]; do not mix raw instrument and calibration-event counts. Proposed size = max(normalized D, normalized G, 0.5 × normalized H). Using max avoids summing overlapping opportunity signals. Preserve every contributing reason and distinguish the dominant channel.
5. Urgency = max(due-timing urgency, supported cadence/volume-deviation urgency). Due-timing uses days to the supported window; cadence compares observed silence with median recurrence, and deficit uses its supported baseline. Discovery alone receives a lower planning urgency. Follow-up deadlines are displayed separately using the workflow date rather than silently mixing current task dates with historical source cutoffs.

Unknown components remain null with explicit reasons. Accounts with enough due evidence can be scored without a forecast. Accounts without sufficient information for either axis remain in a Needs evidence list and count, rather than receiving fabricated zeros or a low-opportunity assignment. Evidence strength and outreach readiness remain visible; a high score never overrides stop/suppression or missing live checks.

### Four opportunity clusters

Fit a separate deterministic KMeans model with k=4 on the two visible engineered coordinates. Do not include behavioral segment, industry or customer ID as clustering features. Existing supervised activity forecasts and behavioral segments remain separate outputs. No PCA/t-SNE view is needed because the plotted coordinates are the fitted features.

Use four proposed business names only after inspecting actual cluster centers and distributions:

| Center profile | Proposed name | Manager action |
|---|---|---|
| Larger size, greater urgency | Act now | Investigate or prepare the largest timely conversations |
| Larger size, lower urgency | Plan larger opportunities | Prepare batches and peer-supported discovery |
| Smaller size, greater urgency | Focused follow-up | Resolve timely smaller needs or activity concerns |
| Smaller size, lower urgency | Nurture and monitor | Maintain coverage and wait for stronger triggers |

These are proposed interpretations, not predetermined model findings. Check silhouette, cluster sizes, outlier sensitivity and seed agreement. If the data does not produce four stable, distinct groups, show four explicit urgency/size priority zones instead of claiming four natural ML clusters. Clusters can contain any behavioral segment and any industry. Seed/model version and stable cluster IDs are published once per source/configuration; dropdown filters restrict membership without refitting or recoloring the same model.

Render small customer points in four colors, with clickable centroid circles/cluster outlines and a selectable legend. Cluster circles summarize groups; they are not measured confidence regions. Hover shows account, industry, behavioral segment, urgency, size, dominant opportunity reason, evidence status and available forecast. Point click opens account evidence; group click selects the whole cluster. Do not inflate customer bubble size based on invented monetary value.

### Four cards for the selected cohort

Every card and table uses the full intersection of filters and selected cluster, including customers not currently drawn or on the first list page.

| Card | Definition and action |
|---|---|
| Due instruments | Deduplicated supported instruments within the selected window, with recorded/inferred breakdown; prepare a calibration conversation |
| Calibration demand outlook | Sum of supported next-three-month calibration-event forecasts for selected accounts; show forecast coverage and fixed target dates, with directional-quality disclosure |
| Activity concerns | Selected accounts with a supported inactivity flag; show cadence/volume evidence and investigate the explanation |
| Open follow-ups | Open local tasks for selected accounts, including due/overdue subset; progress agreed next steps |

These replace the current all-database totals. Never relabel calibration events as orders or inactivity flags as churn probability. Keep these four cards as the default. Add an optional commercial-scenario mode after the map, cohort totals and evidence workflow work; in that mode, the demand card switches to estimated contribution while retaining forecast quantity and coverage beneath it. The financial calculation and assumptions are specified below. Probability of a return is not probability of recovery after outreach.

The demand card is account-wide. A product/category cohort filter selects relevant accounts, but cannot turn an existing account forecast into a product-specific forecast. Its caption must retain all-services scope. Due-instrument breakdown can additionally show selected-category counts. Do not prorate three-month predictions into 30/60-day figures.

### Model-derived estimates and optional financial scenarios

Requested planning addition: use data-science methods to construct useful activity, quantity and commercial-potential estimates. Keep observed evidence, evaluated predictions, business-rule scores and assumption-based scenarios distinct in contracts and presentation. The additions in this section are proposed work, not features already delivered.

| Output | Method and target | Display and validation |
|---|---|---|
| Expected calibration demand | Forecast next-three-month calibration-event counts from covered historical volume, cadence and seasonality; compare candidate models with the existing baseline | Explicit target dates, supported account count and historical error; current customer baseline WAPE is 65.05%, so treat quantities as directional and improve the model before adding precision |
| Probability of no activity | For the existing any-calibration target, calculate `1 - probability_of_any_calibration_next_3_months` | For example, 81% probability of activity means 19% probability of no activity in the same window; neither percentage establishes churn or the effect of contact |
| Missed-cycle review | Retain current cadence/volume-deviation evidence; optionally define a future missed-expected-cycle label using only cutoff-time history and evaluate chronologically | Keep a rule flag separate from a learned probability. Freeze cycle definitions, support checks and label horizons; do not call a proxy confirmed customer churn |
| Expected next calibration window | Optional survival-analysis experiment using time to next observed provider calibration, with right-censoring for accounts not yet returning | Evaluate against a cadence baseline on later periods; publish supported windows only if the experiment succeeds. Not required for the first dashboard |
| Commercial potential scenario | Multiply supported forecast quantity by explicitly supplied contribution per calibration, or by supplied price minus variable cost | Label as a scenario, publish assumption provenance and quantity coverage, and distinguish revenue, contribution and net profit |
| Opportunity priority | Existing explainable timing/quantity/activity/evidence rule score, plus separate urgency/size axes | Score 0–100 with components and version; it is not a probability or learned monetary return |

Financial example: `100 expected calibrations × (€40 assumed price - €25 assumed variable cost) = €1,500 scenario contribution`. This is contribution associated with forecast activity, not extra contribution caused by outreach; it excludes fixed costs. Allow service-specific inputs only when quantity forecasts have matching service scope. The current account-wide forecast can use an explicitly assumed blended contribution per calibration; filtering to an equipment category must not silently make the forecast category-specific.

- Keep assumed price/cost or unit contribution editable, with currency, unit, author/source and saved scenario name. Do not preset fabricated Perschmann prices.
- Missing financial inputs return null and excluded-account/quantity coverage, never zero-valued profit. Do not monetize due instruments as though each becomes a completed calibration.
- Offer user-supplied low/base/high assumption sets and sensitivity comparisons. These are scenario ranges, not measured prediction intervals or statistical confidence bounds. Forecast uncertainty can be added only after its coverage has been evaluated.
- The existing volume forecast already includes zero-activity outcomes. Do not multiply it by return probability again. A future two-part model may use `P(N > 0) × E[N | N > 0]` only if its count forecast is explicitly conditional and jointly evaluated.
- Incremental-outreach calculations are optional later scenarios: `assumed additional calibrations caused by contact × unit contribution - contact cost`. Keep the extra-activity assumption separate from ordinary return probability. Estimating causal uplift would require contact/intervention and outcome data, with randomization or justified confounding assumptions.
- Future distinct-order forecasts need validated order IDs, deduplication, timestamp semantics and their own temporal evaluation. Calibration counts and order-position counts are not distinct orders.

Proposed optional scenario contract: `scenario_id`, `currency`, `quantity_unit=calibration_event`, `forecast_scope`, `target_start/end`, `assumptions` (blended contribution or price/variable cost, provenance, low/base/high settings), `expected_quantity`, `supported_account_count`, `excluded_account_count`, `estimated_contribution`, and `interpretation=scenario_not_outreach_uplift`. Add typed financial assumptions rather than an unqualified `profit` field. Persist them separately from SQL evidence; recalculation uses the same selected cohort and selection revision. Chat must explain the assumptions and may change them only through validated workspace controls.

### Sales-manager additions to the Dashboard

The manager needs to decide who to review, who owns the next action, what can be done in available time, and which agreed tasks are slipping. Keep the main screen focused on those decisions; detailed sector/model charts stay on Insights. The following are priorities, not measured business improvements.

| Priority | Addition | Decision and implementation boundary |
|---|---|---|
| Core | Act now shortlist with purpose presets | Show a small ranked list for upcoming needs, retention review or discovery; each row has why now, quantity, evidence status and next step. High return probability does not by itself mean the best account to contact |
| Core | Ownership and deadline strip | Show overdue follow-ups and timely unassigned actions; link to claim/assign and customer follow-up controls. Use local workflow owners, not an inferred CRM owner; overdue task dates follow the workflow clock |
| Core | Evidence and readiness badges | Separate supported evidence from manual contact/order checks, unresolved unknowns and suppression. A historical absence is not proof that no quotation or contact exists. Explicit stop/suppression rules remain binding |
| Core | Selection summary and coverage | Show selected account count, share of all matching opportunities, supported forecast count and unsupported evidence count; keep every total on the full filtered cohort, not the plotted sample |
| Core | Conversation preparation drawer | Open an account's existing facts, affected instruments, unknowns and discovery questions from the shortlist; record outcome, owner and next follow-up without losing cluster selection |
| Core | Saved action list and export | Save selected account IDs, cluster/filter settings, evidence/reference dates, model/rule versions and selection time; export a handover brief. Reopening revalidates current workflow suppressions and flags a changed snapshot rather than treating an old list as current |
| Next | Contact-budget planner | Choose 5/10/custom accounts or a supplied time budget, then preview a shortlist and assignments. Start with user-supplied effort assumptions and deadline-first tasks; record manual overrides and do not describe the list as optimized conversion |
| Next | Financial-scenario switch | Use supplied financial inputs to compare the selected cohort's contribution under low/base/high assumptions; preserve the default quantity view when inputs are missing |
| Next | Local outcome funnel | Summarize reviewed, contacted, qualified need, quotation requested and next step where explicitly recorded; missing stages remain unknown. Contacted does not mean sold; quotation requested does not mean quotation issued or converted |
| Later | Recommendation-quality review | Show rejected reasons, snoozes and overdue/completed workflow trends after enough dated local records accumulate; no fabricated historical trend or claimed uplift |

Recommended compact layout: filters → opportunity map → four scoped cards → a small deadline/unassigned strip → priority table with preparation drawer. Put contact-budget, scenario and export controls in the table toolbar. Coverage is a short caption or card footer, not another large chart. Outcome review can be a collapsed panel or Insights subview so the Dashboard remains useful at a glance.

The assistant shares the exact map selection, KPI scope, shortlist, ownership/deadline context, readiness checks and active financial assumptions. It can filter to a cluster, prepare a saved shortlist, explain the assumptions and open the account for recording a confirmed outcome. Unsupported outcomes must not be filled in by generated text, and customer outreach is not automatically sent.

Reuse the existing workflow store and preparation/ranking services. Check which ownership, outcome and assignment operations already exist before proposing new endpoints; add only the missing contract fields/actions. Coverage and financial scenarios use the single opportunity response/composition boundary rather than an independent frontend calculation with different denominators.

Method references: survival analysis and censoring ([lifelines](https://lifelines.readthedocs.io/en/latest/Survival%20analysis%20with%20lifelines.html)); requirements for treatment-effect estimation ([EconML](https://www.pywhy.org/EconML/spec/estimation/dml.html)). These describe candidate methods, not completed evaluations on this dataset.

### Controls and table

First controls: industry, service/equipment category, purpose (all/upcoming/activity review/discovery), requirement window (30/60/90 days), optional behavioral segment, recorded-only/include inferred, and past-due review. Default history lookback is twelve covered months; keep any 6/12-month lookback switch behind separately versioned cached feature sets. Initially support the current historical reference only; arbitrary as-of dates need point-in-time source reconstruction.

Point display limit: 200 (default) / 500 / 1,000. The API caps plotted points at 1,000 to limit browser memory. Sampling is deterministic and balanced across clusters; clearly show displayed count versus all matching accounts. KPI totals and table never aggregate the sampled points. Full filtered count is available even when fewer dots are shown.

Table columns: account, industry, behavioral segment, opportunity reason, due instruments, activity-review badge, supported return probability with target window, priority score, owner, next action. Priority is a rule score rather than a calibrated percentage. Separate the activity-review badge from the return probability. Default sort uses existing transparent priority; purpose-specific sort presets can emphasize due quantity or activity concerns. Opening an account preserves the Dashboard selection for returning to it.

### Integration contracts and agent controls

Implement one cached opportunity-dashboard response keyed by snapshot/model/configuration/filter/selection revision. Reuse Pydantic v2 contracts, the existing composition boundary, Zustand, ECharts and the event router. Avoid N individual customer-detail HTTP calls for plotting.

Proposed point fields: customer_id, industry_id/label, segment_id/label, cluster_id, urgency_score, size_score, size_basis, component values/evidence_refs, priority_score, due counts, inactivity support/flag, activity_probability with horizon, volume outlook with support, and readiness. Missing values are null. No profit/churn_probability fields receive invented numbers.

Response sections: metadata (snapshot/reference/model/rule versions), selection/filters, full eligible/matching/unassigned counts, sampled points and sample count, four cluster summaries/centroids, four scoped metric definitions/values/support counts, and a paginated priority-sorted customer table. Every section carries the same selection revision and metric scope; stale responses cannot overwrite a newer selection.

Planned endpoint: `GET /api/v2/opportunities` using the selected snapshot, versioned config, filters, optional cluster ID, display limit and table pagination. The server calculates totals from the complete cohort and validates cluster/category IDs. Insights reuses current sector/model-report APIs.

Agent context includes current page, selected cluster ID/name, axes and component definitions, filters, counts, card values/scope, visible IDs, sampling state and current model/reference date. Add typed tools/events to select/reset a cluster, change opportunity filters, list selected-cluster accounts, and inspect cluster evidence. Insights must be added to page/navigation schemas, frontend types, tools and routing; retain compatibility for existing Follow-ups links. Extend service-backed chart views explicitly: the current chat create_chart tool only supports industry-population, observed activity and portfolio charts, despite broader plot types existing on the Dashboard.

### Implementation order after plan review

1. Quantify feature coverage/distributions, validate instrument deduplication and score components; fit and assess the separate four-cluster model. Publish immutable opportunity artifacts and quality evidence.
2. Add one shared response contract/composition/API for map, metrics and ranked members. Verify missing-data, stop/suppression, period/product scope and full-cohort aggregation.
3. Build ECharts group/point interactions and Zustand filter/selection state; connect all four cards and the paginated table to the same selection.
4. Move sector/quality views to Insights and fold Follow-ups into Customers while preserving existing routes.
5. Add typed agent selection/filter/evidence tools and exact page context, then exercise the full manager workflow in the browser. Preserve streamed Markdown, returned reasoning, tool traces and chat memory.
6. Connect manager essentials: deadline/unassigned strip, readiness/coverage, preparation drawer and saved action export. Then add the contact-budget planner and optional financial scenarios if the core is complete; survival timing and outcome trends remain later experiments.
7. Commit each passing data, API, UI and agent slice separately. Verify selection totals, deterministic membership, sample-vs-population consistency, product/forecast scope, scenario units/assumptions, legacy navigation and mobile/desktop chart behavior.

Demo: choose Act now, inspect due demand/activity concerns, filter to an industry and service category, open a ranked account, explain the reason with Pulse, record a timing correction, and see its next step reflected in the selected cohort. Success is a coherent supported decision workflow; incremental sales, prevented churn and profit require later outcome evidence.


### Implementation checkpoint — 8 October 2026

The opportunity model/API, scoped dashboard, preparation drawer, saved shortlists, supplied contribution scenario, Insights navigation and typed assistant filter/cluster tools are implemented. Four frozen clusters passed the configured quality checks (default silhouette 0.608, seed agreement ARI 0.983); opportunity groups remain separate from behavioral segments. The model yielded three urgent size groups and one quieter group, so their labels describe the observed centers rather than promising four artificial quadrants.

Runtime processing uses a streamed compact snapshot and indexed account evidence: 63.2 MB runtime JSON instead of approximately 652 MB. A measured API process used about 724 MB rather than roughly 3 GB. Plot sampling defaults to 200 points and never changes full-cohort totals. Account evidence is capped at 500 loaded records, with at most 50 displayed and separate source-wide tier counts. Large source snapshots cannot be loaded directly by the API.

Custom time-budget allocation, low/base/high scenario sensitivity, survival timing and outcome trends remain later work. The implemented contribution scenario uses an explicitly supplied unit contribution and supported calibration quantity; it does not estimate incremental outreach benefit, net profit or confirmed churn.
