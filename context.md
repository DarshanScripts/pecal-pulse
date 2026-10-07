# PeCal Pulse — context for the three backend members and their coding agents

Updated: 8 October 2026. Read [AGENTS.md](AGENTS.md) first for the current implementation checkpoint, then read this for team/product context. [plan.md](plan.md) is the detailed work split and contract specification; [README.md](README.md) contains current run commands. Earlier dated notes below are historical; current-state instructions in `AGENTS.md` take precedence over stale implementation descriptions.

## Model selection update — 7 October 2026

The user has superseded the fixed Muse model choice: use `LLM_MODEL` from the root `.env`, with environment overrides. Earlier fixed-model references below describe the original selection. Chat status reports the active configured model.

## Product and user

We chose **Perschmann Challenge 2: Customer Activity Monitoring**. The primary user is an Inside Sales representative with little time for proactive contact because quotation preparation occupies their day.

The product answers: **“Which customer should I contact next, why now, what should I ask, and what happens after the conversation?”**

The challenge asks for future calibration requirements, activity/retention concerns, expected volume, prioritized opportunities and industry-specific portfolio discovery. The source photographs are in `chl_media/`; the English brief is `photo_6210931557002842947_y.jpg` and the Challenge 2 data diagram is `photo_6210931557002842946_y.jpg`.

The demo should show a complete customer action, not just prediction dashboards: select an opportunity → inspect evidence/unknowns → prepare a conversation → record “timing changed” → save a follow-up and suppress the old reason → see the persisted next step while other valid reasons remain.

## Fixed decisions from the user

- **Frontend and chatbot owner:** Aditya with Codex. We own the ReAct agent, checkpointing, artifact creation, data-analysis tools and website manipulation in addition to the frontend. The other three people build data/API, ML/analytics and sales-intelligence functionality.
- **Frontend:** Next.js + TypeScript; three main navigation pages: Dashboard, Customers, Insights. Follow-ups live inside Customers; legacy routes remain compatible. Soft, rounded, attractive UI; usability first.
- **Chat:** assistant-ui thread/composer/actions in a drawer. Reuse React Bits and `/c/micro` components where suitable; do not rebuild library behavior.
- **Backend:** FastAPI, uv, NumPy/scikit-learn as needed. SQLite for local workflow and conversation persistence.
- **Agent:** LangChain/LangGraph ReAct via `langchain.agents.create_agent`, using registered sales tools.
- **Provider/model:** OpenRouter; use root `LLM_MODEL`. The earlier fixed Muse choice is superseded.
- **Credential:** `OPENROUTER_API_KEY` in the repository-root `.env`, already supplied on Aditya's machine. Do not display/copy/commit its value; it is not part of a clone. Backend settings load the root file and respect environment overrides. Never expose the key to Next.js/browser code.
- **Conversation memory:** `langgraph-checkpoint-sqlite`, async `AsyncSqliteSaver`, persistent `thread_id` and conversation history recovery.
- **Agent UI control:** typed filters/navigation/customer-selection/chart commands through the existing event router. No generated JavaScript/React or arbitrary SQL.
- **Current page context:** the agent receives the active page/tab, selected account, visible IDs/metrics, filter values/options, sorting/pagination, plot settings, source dates, artifacts and the registry of available controls. It can explain the displayed page or change actual dropdowns/plots through typed commands. See plan §4G.
- **Optional coding/artifacts:** use Daytona for sandboxed Python/bash if needed; `DAYTONA_API_KEY` is configured in root `.env` on Aditya's machine. Reuse the template sandbox/files/artifacts implementation. Aditya + Codex own this, and the normal evidence/control tools work without it.
- **Hackathon focus:** core workflow and defensible data/ML results within roughly 16 productive implementation hours; leave integration time. Voice and multivariate forecasting remain later enhancements; chat streaming is implemented.

## What exists now — distinguish implementation from the plan

The current application integrates all three members' shared v2 services with the frontend and chatbot. Read [integration-audit.md](integration-audit.md) before extending it.

- Dashboard: opportunity map with four shaded model regions, frozen relative axes, shared filters/selection, scoped metrics, ranked accounts and preparation drawer. Sector history/correlation/one-month outlook and quality disclosures are on Insights.
- Customers: paginated server-side filters, independent account details, history and supported three-month forecasts, due-date tiers, peer discovery, preparation export and local workflow corrections.
- Follow-ups inside Customers: persisted local tasks, completion/reopening; historical views exclude old synthetic account tasks.
- Chat: assistant-ui streamed Markdown, returned reasoning/tool parts, history/cancellation, exact page metrics, actual industry/segment controls and observed-data chart artifacts.
- `PECAL_SNAPSHOT` selects the source. Default `synthetic-v1` is a fixture with unsupported analytics. Aditya's ignored `.env` selects `historical-full-20260831-v2`; private extracts and model artifacts are not in Git.
- New UI types: `frontend/src/types/sales-v2.ts`. Preserve v1 compatibility routes and chat history while changing v2 APIs.
- Current validation: 142 backend tests, frontend typecheck/build, live browser grounding and industry-filter/navigation checks. Daytona/voice/CRM and browser event receipts remain enhancements.

### Current code map

| Path | Meaning |
|---|---|
| `frontend/src/modules/sales/` | Dashboard, Customers, Follow-ups, API client and Zustand state |
| `frontend/src/modules/chat/SalesAssistant.tsx` | assistant-ui external-store runtime and drawer |
| `frontend/src/types/sales.ts` | Compatibility and chat/context/control TypeScript contracts |
| `frontend/src/core/events/router.ts` | One command/domain-event application boundary |
| `frontend/src/modules/artifacts/Chart.tsx` | ECharts lifecycle and constrained bar/line artifacts |
| `backend/app/api/sales.py` | Current `/api` routes including bootstrap/chat/follow-ups |
| `backend/app/capabilities/sales/` | Current mock service, models, tools and scripted responder |
| `backend/app/capabilities/registry.py` | Tool registration boundary |
| `backend/app/realtime/publisher.py` | Shared event envelope |
| `backend/tests/test_sales_contract.py` | Existing focused tests |
| `data/mock/workspace.json` | Shared synthetic fixture, not real predictions |
| `data/runtime/` | Ignored local workflow, future snapshots and checkpoints |
| `analysis/export_customer_data.py` | Starting read-only export queries |
| `analysis/train_customer_models.py` | Existing supervised benchmarks, KMeans, peer/ranking prototype |
| `analysis/customers/dashboard_data.json` | Saved real historical analysis; use its actual reference date |

Next.js sends `/api/sales/*` through its rewrite to Python `/api/*`. New `/api/v2/...` responses will therefore be requested as `/api/sales/v2/...` in the frontend.

## Existing analysis and important meanings

The selected integrated snapshot is **as of 31 August 2026**, targeting September–November 2026. It contains 6,564 accounts (including current owners without historical activity) and 3,180 model-supported accounts. Earlier analysis had 6,515/3,321 under different extraction filters; use the current model report for performance claims. The mock instead uses fictional names and a 30 September reference. These dates/data must not be substituted for one another.

- Integrated activity benchmark selects raw logistic regression using disjoint chronological evaluation stages (analytics-v3 ROC AUC 0.810; Brier 0.176). Earlier isotonic results refer to the previous analysis.
- Current volume comparison selected the **previous 12 months divided by four** baseline. Do not claim a boosted volume model won.
- Behavioral segment labels come from the active analytics artifacts. They are independent of the four opportunity groups; do not hardcode segment labels from earlier experiments.
- The shared offline analytics runner uses the snapshot cutoff and emits a three-month total. Older standalone training scripts describe previous experiments; do not fabricate monthly predictions from a quarterly total.
- Existing groups export counts calibration rows; it is not a distinct-instrument portfolio count. Member 1 supplies both measures explicitly.
- Existing display IDs truncate a customer hash. The shared integration ID must be stable/full or have demonstrated collision safety.

### Limits the product must handle

Activity probability means **at least one observed calibration at this provider in the next three full months**. It is not churn probability, order probability or the causal benefit of contacting someone.

Missing due dates require evidence tiers: valid recorded date, usable nominal interval, supported repeated history, then unknown. Stop flags/date anomalies must be respected. Unknown status cannot automatically become outreach eligibility.

History describes equipment calibrated with Perschmann. An absent category supports a discovery question; it does not establish owned equipment, competitor use or missed sales. Peer denominators/support and window dates must be shown.

Confirmed churn, live quotations, recent sales contacts, verified contacts/owners, prices, revenue and margins are not established by the extract. Manually supplied workflow facts remain separate. Use calibration events/instruments and, where valid, order positions as distinct quantities. Do not turn delivered positions into distinct orders or receipt-date demand without justification.

## Your assignment

Use the role given by your teammate or infer it from the assigned branch. If neither is provided, ask which of Members 1/2/3 you are before editing owned implementation files. Read your section of `plan.md`, all shared contracts in §4, and the merge sequence in §6.

| Role | Branch | Deliverables | Input → output |
|---|---|---|---|
| Member 1: data/API/workflow | `feat/data-api` | Normalized read-only snapshot; profiles/history/portfolio; requirement evidence; v2 contracts/API composition; SQLite ownership/checks/corrections/snoozes/follow-ups | Source records → shared typed snapshot, requirements and screen responses |
| Member 2: ML/analytics | `feat/ml-analytics` | Features; KMeans; calibrated activity prediction; validated volume baseline/model; inactivity evidence; sector forecast/correlation; model report | Member 1 snapshot → typed prediction/segment/sector outputs |
| Member 3: sales intelligence | `feat/sales-intelligence` | Peer discovery; bundled/ranked reasons; preparation cards; explainable EDA/evidence services | Profiles + requirements + predictions + workflow → actions, briefs and typed aggregate evidence for API/agent consumers |

Member 1 owns shared backend schemas, app wiring and Python dependencies. Member 2 owns analytics modules and their tests. Member 3 owns insight/peer/ranking/preparation modules and their tests. **Aditya + Codex own `frontend/**`, agent/checkpoint/chat routes, tool registry, workspace controls, sandbox/artifacts and main-branch integration.** Detailed file ownership is in the plan; coordinate boundary changes rather than editing each other's modules.

### First tasks for Member 1's agent

1. Inspect source export/schema/quality evidence and the v1 API without executing source writes.
2. Freeze `backend/app/contracts/sales_v2.py` with Aditya/Members 2/3 and a small synthetic normalized fixture.
3. Add the v2 skeleton and separate chat routing ownership with Aditya + Codex. Keep current mock runnable.
4. Publish normalized snapshot/manifest with stable IDs, attribution, units and complete-month cutoff.
5. Implement customer/requirement endpoints and workflow persistence, then integrate downstream validated outputs.

### First tasks for Member 2's agent

1. Reproduce the saved benchmark and read its split/label construction; inspect actual schema differences from the mock.
2. Agree input/output types with Member 1. While waiting for the shared schema commit, develop against the agreed synthetic fixture and existing local analysis; do not invent a competing contract.
3. Separate reusable features, segmentation, prediction, inactivity and sector functions from the existing monolithic script.
4. Export typed immutable outputs and a model report for the **same snapshot ID/reference date** as Member 1.
5. Validate baselines, chronological leakage boundaries, calibration, sparse/unsupported accounts and correlation sample support before handoff.

### First tasks for Member 3's agent

1. Read existing peer prevalence, activity-review ranking and preparation needs in `analysis/train_customer_models.py` and plan §4C.
2. Implement peer/action/preparation functions on shared fixtures while data/ML members work. Exclude the target account from peers; disclose denominator/window and avoid claiming equipment ownership.
3. Implement reason bundling, deterministic priority components, readiness and signal-scoped suppression. Consume Members 1/2's shared types rather than duplicating their calculations.
4. Expose typed service functions and aggregate evidence suitable for both Member 1's API composition and Aditya + Codex's agent tools. Provide queryable facts/metric definitions and grounded questions, not frontend charts or LLM-generated facts.
5. Test stopped/resolved/snoozed cases, duplicate instrument reasons, small industries, peer support, unknown inputs and repeated-ranking consistency.
6. Deliver the insight module/README/fixtures and validate the same services on the shared historical snapshot. Chat, provider configuration, checkpoints, workspace manipulation and Daytona are owned by Aditya + Codex.

### Aditya + Codex's parallel track (for coordination)

We reuse the supplied template's agent/model/async-saver lifecycle, implement current-page context and state-control tools, connect the exact OpenRouter model, restore conversations, create/update artifacts and optionally execute analysis code in Daytona. On Aditya's machine the template is `/home/adityaladawa/Aditya/hack_n_slash/hackathon-template/`; imported components must be copied into this repo, never left as absolute runtime imports. Backend members provide callable typed services and do not create another agent or modify the frontend.

## Contracts and collaboration rules

The detailed schemas and examples live in **plan §4**, not in each person's notebook:

1. Member 1 exports `MonthlyHistoryRow`, `CustomerProfile`, `PortfolioRow`, `InstrumentRecord`, `InstrumentEvent`, `SnapshotManifest`, and supported `Requirement` records.
2. Member 2 exports `CustomerPrediction`, `VolumeForecast`, `SegmentSummary`, sector data and model-quality report.
3. Member 3 produces `PeerOpportunity`, `AccountAction`/`ActionReason`, `PreparationCard` and structured insight metrics.
4. Member 1's composition service serves the screen response. The frontend consumes this API; it does not assemble model files or compute business scores itself.
5. Dashboard cards and chatbot grounding share `frontend/src/modules/sales/page-context.ts`. `WorkspaceContext.page_snapshot` carries exact displayed metric labels, values, units, definitions and scope at send time. The backend must preserve this optional snapshot; never substitute the selected account for a dashboard aggregate. Snapshots from a different page are omitted by the context tool.
6. Aditya + Codex own `WorkspaceContext`, `ChatReply`, thread history, control/artifact events and registered agent tools wrapping these services.

Use opaque consistent IDs; dates/months in ISO forms; explicit units; probabilities `[0,1]`; null for unknown. Match snapshot IDs. Do not divide a quarterly prediction into fake monthly values, invent uncertainty bounds, or return mock values under historical mode.

Preserve existing event names: `ui.navigate`, `customers.filters.set`, `customers.select`, `artifact.created`, `followup.created`, `followup.updated`. The planned `customer.workflow.updated` event is added with the frontend contract change. Aditya + Codex add registered `ui.control.set` and artifact update/delete commands with state revisions/application receipts. Agent events use the publisher and one frontend router. All chart datasets align with labels. Sandbox code may generate files/specifications; live page manipulation still uses typed commands. No arbitrary page JS or general-purpose database execution tool.

Readiness is explicit. A missing analytics module returns unavailable/null or leaves the whole workspace in mock mode. No hidden mixture. Heavy training runs offline; APIs/chat read validated outputs.

Data modules do not import analytics/agents. Analytics consumes data contracts. Insights consumes profiles/requirements/predictions/workflow through pure functions. Composition joins them. Agents/tools call composition/services, not API route handlers. No circular dependencies.

## Run and verify

```bash
uv sync
cd frontend
pnpm install
cd ..
bash scripts/dev.sh
```

Frontend: http://127.0.0.1:3000. Backend API docs: http://127.0.0.1:8001/docs. Check ports before starting another copy. ODBC/network/source extract access is documented by Member 1; root `.env` and ignored runtime files are not supplied by `git clone`.

```bash
uv run python -m unittest discover -s backend/tests -v
cd frontend
pnpm typecheck
pnpm build
```

Stop the Next.js dev server before production build. Add focused tests for your actual module invariants, not copies of the implementation. Each member supplies a module README and a representative valid synthetic output for integration.

## Handoff and merge

Commit small, runnable increments on your assigned branch. Fetch and merge `origin/main` into that branch before a PR; coordinate conflicts with file owners. Do not force-push shared branches. Service merge order: contract baseline → data/API → analytics → peer/ranking. Aditya + Codex build the checkpointed agent and workspace controls on main in parallel and wire those merged services into the integrated demo. Independent fixture-based work can proceed before upstream production wiring merges.

Your PR/handoff must state:

- Implemented functionality and owned files.
- Inputs, output schemas/endpoints/events and a representative fixture.
- Data/model/reference versions and unsupported cases.
- Setup/run commands, dependencies and access requirements.
- Checks run and any remaining integration work.

A coding agent receiving this document should **implement its assigned scope**, not just propose another plan. Preserve current runnable behavior, reuse available code, and finish the role's acceptance checks. Do not implement the other two members' modules or redesign the frontend.

Suggested prompt for a teammate's agent:

> Read context.md and plan.md. You are Member [1/2/3] on branch [assigned branch]. Implement that member's functionality, follow the shared contracts and file ownership, and reuse existing analysis/template code. Keep the mock runnable until integration is ready. Provide focused tests, a synthetic response fixture and a concise integration handoff. Coordinate shared-contract changes with Aditya/Member 1.

## Context maintenance

Keep assignments and contracts in `plan.md`; keep this file as a short onboarding/state guide. Update the “What exists now” section when major slices merge so the next agent can distinguish shipped features from proposed ones. Put module implementation notes in that module's README rather than duplicating the whole contract here.

Customer overview now uses historical calibration bars plus a shaded three-month forecast window, with no future bars or line. The quantity estimate is not orders or sales. `forecast_quality` on the detail response reports input months for baseline methods and the selected quantity model’s test WAPE/MAE and customer-origin sample size. Keep aggregate historical error distinct from individual accuracy and activity probability. The assistant’s activity-view control selects 24 versus 3 months of visible history; both retain the shaded forecast window. Current analytics-v3 improves activity prediction (ROC AUC 0.810); the previous-12-month average still wins quantity validation (test WAPE 65.05%). Financial scenarios are parked outside the main sales UI.

Detailed customer reasons now use compact batch cards: quantity, equipment label, readable date/window, status and recorded/estimated timing. Technical explanation and unresolved checks live behind an info icon. Keep each batch’s original reason ID for snooze/resolution; do not merge workflow actions across batches or equate a historical passed date with confirmed outstanding work.

Batch cards use “Recorded due date” rather than “Date on file”, and show past calibration events for the matching equipment category with the actual portfolio period. This is category-level history, not a count of prior calibrations for the displayed batch. Instrument IDs are lookup references, not an opportunity score; current instrument exports do not include product names, manufacturer or model descriptions. Do not infer their absence from the underlying SQL schema.

Sales-facing preparation is organized as: confirm the calibration need, check in after a longer gap, ask about specific additional services, and check current team activity before contact. Next step and exported briefs use these concise prompts instead of raw preparation facts. Equipment history shows completed calibrations without an unavailable inventory-count column; peer suggestions use actual category names and a discovery question, with supporting industry numbers behind an info icon. Batch resolution/snooze is shown only for calibration batches; inactivity and discovery are handled through conversation and follow-up. Pulse’s system prompt uses the same nontechnical sales vocabulary.
