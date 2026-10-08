# Challenge implementation checklist

Checked **8 October 2026**, against application commit `d0f59e0` plus this documentation update. Result: **the Challenge 2 prototype is implemented, but the full proposed feature list is not complete. CSV/PDF sharing is missing.**

Evidence: direct review of the supplied Challenge 2 English brief and supporting board photographs in the parent workspace's `hackathon-info/challenge-2/`, the 31-feature research list, [plan](../plan.md), actual frontend/backend code and existing regression tests. Voice, chat and exports are additions to the brief, not five extra official challenge requirements.

“Implemented” below means a concrete application path exists with code/test evidence. “Partial” means only part of the proposed behavior exists or the extract supports a proxy. It does not mean production accuracy or business/user acceptance has been established.

## Official Challenge 2 requirements

| Brief requirement | Status | Actual behavior and limit |
| --- | --- | --- |
| Predict future calibration requirements | Implemented with coverage limits | Recorded dates, usable nominal intervals, supported repeat-history inference and unknown cases. Grouped requirements show their evidence basis; stopped instruments and invalid dates are handled. Unknown instruments do not receive invented dates. |
| Identify customer activity and increased churn risk | Partial | Activity probability, cadence/deviation signals and empirical retention review work. No confirmed churn labels or validated churn probability. |
| Forecast expected order volumes | Partial | Customer three-month **calibration-event totals** and sector one-month calibration outlook work. Commercial orders/order positions are not the app forecast target. Research baselines/static analyses are not an integrated customer-order forecast. |
| Prioritize opportunities by commercial potential | Partial | Transparent timing, quantity, activity and evidence components; frozen opportunity groups and ranked accounts. No validated revenue/margin forecast. Optional backend financial scenarios use supplied assumptions and do not establish actual commercial value. |
| Identify industry-specific portfolio opportunities | Implemented with coverage limits | Peer-supported category prevalence and discovery questions, with support thresholds and miscellaneous/sparse-peer handling. An absent category is not proof of customer equipment ownership or competitor business. |
| Daily recommendations: whom to contact and why | Implemented as a historical prototype | Dashboard shortlist, reason/evidence views, preparation, ownership, suppression and persisted next steps. Evidence is an offline snapshot, not today's live sales activity. |

Code: [requirements](../backend/app/capabilities/data/requirements.py), [analytics pipeline](../backend/app/capabilities/analytics/pipeline.py), [retention](../backend/app/capabilities/analytics/retention.py), [ranking](../backend/app/capabilities/insights/actions.py), [peer discovery](../backend/app/capabilities/insights/peers.py), [opportunity composition](../backend/app/capabilities/data/opportunities.py), [customer workspace](../frontend/src/modules/sales/IntegratedWorkspace.tsx).

## Requested assistant, voice, graphs and sharing

| Function | Status | Evidence / how it works |
| --- | --- | --- |
| Sales AI assistant | Implemented; provider configuration required | [LangGraph agent](../backend/app/agents/react_agent.py), [registered tools](../backend/app/capabilities/registry.py), [stream/history API](../backend/app/api/chat.py), [assistant-ui](../frontend/src/modules/chat/SalesAssistant.tsx). Streamed text, tool traces, provider-returned reasoning, cancellation and SQLite conversation recovery. |
| Assistant controls the workspace | Implemented for registered controls | Navigation, account selection/previews, filters, list pagination, shortlist size, plot sampling, local assignment/checks/tasks and exact calibration-reason corrections. [Tools](../backend/app/capabilities/workspace/tools.py), [workflow tools](../backend/app/capabilities/workspace/workflow_tools.py) and [event router](../frontend/src/core/events/router.ts). New equipment/date-group paginations have manual UI controls only; no browser acknowledgements of applied commands. |
| English/German voice AI | Implemented; LiveKit configuration required | [VoicePanel](../frontend/src/modules/chat/VoicePanel.tsx), [browser transport](../frontend/src/modules/chat/voice-livekit.ts), [server adapter](../backend/app/agents/voice_livekit.py). Deepgram Nova-3 STT, Cartesia Sonic-3 TTS, language selector and automatic submission into the same agent/tool stream. |
| Interrupt a spoken reply or agent turn | Implemented | Space cancels the current agent run and starts another spoken turn; tapping the active orb stops it. Server awaits the speech interruption and discards stale final replies. This is **push-to-talk**, not continuously listening hands-free speech interruption. Completed workflow writes are not rolled back by interruption. |
| Create a graph during chat/voice use | Implemented for six supported views | `create_chart`: industry population, customer activity, customer portfolio, sector activity, sector outlook and sector correlation. Artifacts arrive through the stream and render inline in chat; voice uses those same tools. [Chart tool](../backend/app/capabilities/workspace/tools.py), [renderer](../frontend/src/modules/artifacts/Chart.tsx). |
| Enlarge and restore a chat chart | Implemented | [ChatArtifact](../frontend/src/modules/chat/ChatArtifact.tsx): Maximize, Minimize and Escape with focus return. Artifacts are restored with chat history. |
| Continuously updating live-data graph | Missing | Graphs use the selected prepared snapshot. Workspace/filter changes refresh relevant views, but no live SQL/CRM subscription or continuously refreshed source feed exists. No arbitrary generated chart code or general chart-editing tool. |
| Customer preparation export | Implemented as TXT | `exportBrief` in [customer workspace](../frontend/src/modules/sales/IntegratedWorkspace.tsx) downloads `preparation-<id>.txt`, using [salesBriefLines](../frontend/src/modules/sales/CustomerSignals.tsx). |
| Action shortlist export | Implemented as TXT | `exportList` in [OpportunityDashboard](../frontend/src/modules/sales/OpportunityDashboard.tsx) downloads `pecal-action-shortlist.txt`, including source reference, model, selection/filter scope, owners, readiness and reasons. Exports the displayed shortlist, not every matching account. |
| Saved shortlist export | Implemented as JSON | Dashboard's “Export saved IDs” downloads membership/filter/version metadata. Saved lists themselves are browser-local; restoring a selection rechecks current workflow and does not guarantee identical membership. |
| CSV download | Missing | No CSV serializer, download control or export API in the application. Offline analysis/data export scripts are separate from end-user sharing. |
| PDF download / printable report | Missing | No PDF generator, report route, print control or dedicated print layout. The parent project's saved EDA PDF is an existing research artifact, not application PDF export. |
| Download a generated chat chart/report | Missing | Charts have enlargement controls; no chart-image/data/report download. Browser print or screenshots do not establish an implemented export function. |
| Email drafts and sharing | Partial | Evidence-backed English/German drafts are saved on Follow-ups with Copy email and review notes. No in-app draft editor, verified recipient directory or send-email action. Edit copied text in the external email composer. [Draft display](../frontend/src/modules/sales/FollowupEmail.tsx). |

## All 31 proposed Challenge 2 features

Numbers preserve the parent research document's feature list. Several proposed features combine multiple behaviors, so their status is stricter than “some code exists.”

| # | Proposed feature | Status | Evidence / outstanding portion |
| --- | --- | --- | --- |
| 1 | Manageable daily action queue | Partial | Ranked shortlist and separate follow-ups/deadline coverage exist; no contact-time/effort budget or unified personalized daily queue. |
| 2 | Why this customer, why now | Implemented | Account reasons, quantities, timing, date basis, unknowns and suggested next actions. |
| 3 | Customer history and context | Partial | Calibration history, portfolio, industry and local workflow exist; full order-position/service history and verified relationship/contact context are absent. |
| 4 | Upcoming calibration window | Implemented | 30/60/90-day Dashboard scope, inferred-date and past-due options, grouped requirement evidence. |
| 5 | Cycle-aware missed-activity detection | Implemented | Supported cadence, silence and volume-deviation evidence, with insufficient-history states. |
| 6 | Retention concern with alternatives | Implemented as a review signal | Reduced-activity explanations/questions and retention evidence; not confirmed churn. |
| 7 | Transparent opportunity priority | Implemented as a proxy | Component disclosures, separate purposes and quantity/evidence ranking; financial value remains unavailable. |
| 8 | Account-level instrument bundling | Implemented | Shared insight/action composition bundles reasons and respects reason IDs/suppression. |
| 9 | Industry portfolio discovery | Implemented | Supported peer questions and category evidence. |
| 10 | Confidence, freshness and exceptions | Implemented | Source dates, recorded/inferred/unknown tiers, unsupported analytics and evidence disclosures. |
| 11 | Search, filters and personal views | Partial | Search, industry/segment/action/retention filters and saved Dashboard selections; no full saved personal-view or representative-specific queue system. |
| 12 | Shared action ownership | Partial | Local account ownership and agent bulk assignment exist; no authenticated team claim/locking or authoritative CRM ownership/handovers. |
| 13 | Conversation preparation card | Implemented | Customer Next step and Dashboard preparation drawer use known facts and questions. |
| 14 | Follow-up date and next step | Implemented locally | Owner/date/note/outcome tasks persist in SQLite and can be completed/reopened. |
| 15 | Outcome capture and controlled suppression | Implemented locally | Structured outcomes and exact calibration-reason resolution/snooze; other account reasons survive. |
| 16 | Quotation-request preparation pack | Partial | TXT conversation brief exists; no selectable instrument/service request pack or complete requested-timing/quotation handover. |
| 17 | Current quotation/order checks | Partial | Manual reported check exists; no live quotation/order integration. |
| 18 | Validated contact/account details | Missing | Historical accounts use identifier-derived names; no verified company/contact directory. |
| 19 | CRM context/outcome synchronization | Missing | SQLite workflow is local and separate from SQL/CRM. |
| 20 | Account routing and absence cover | Missing | Assigning an owner is possible; territories, absence cover and escalation rules are absent. |
| 21 | Editable outreach drafts | Partial | Evidence-backed EN/DE drafts and copy work; no in-app editing/sending or verified recipients. |
| 22 | Monetary opportunity/margin | Missing as actual business data | Optional supplied-assumption backend scenario does not supply prices, revenue or actual margins. |
| 23 | Operations feasibility/service handover | Missing | No validated service eligibility, live capacity or booking-confirmation workflow. |
| 24 | Quotation-to-order tracking | Missing | No live quotation lifecycle, conversion links or confirmed commercial outcomes. |
| 25 | Customer demand/order-volume outlook | Partial | Requirements, three-month calibration totals and sector outlook; customer orders and monthly quantity intervals remain unsupported. |
| 26 | Account coverage/unattended actions | Partial | Dashboard forecast coverage, unassigned owners and overdue counts; no complete coverage-goal/team-review system. |
| 27 | Retention review with relationship context | Partial | Historical retention/cadence review exists; live relationship/contact context is absent. |
| 28 | Industry campaign preparation | Partial | Peer discovery, filtered shortlist, export and draft tools; no campaign workflow or validated contact eligibility. |
| 29 | Team priority/effort settings | Partial | Purpose/window/shortlist controls and component explanations; no agreed contact-effort settings or audited priority overrides. |
| 30 | Outcome/recommendation-quality review | Partial | Local outcomes and model-quality/retention analysis exist; no recommendation relevance/rejection trends or quote/conversion review dashboard. |
| 31 | Saved lists/handover summaries | Partial | Browser-local saved selections/IDs and TXT export; no shared server-managed list or complete owner/next-step snapshot. |

Primary implementation surfaces: [Dashboard](../frontend/src/modules/sales/OpportunityDashboard.tsx), [Customers/Insights/Follow-ups](../frontend/src/modules/sales/IntegratedWorkspace.tsx), [instrument timing](../frontend/src/modules/sales/InstrumentTiming.tsx), [data/API composition](../backend/app/api/v2.py), [local workflow](../backend/app/capabilities/data/workflow.py), [insight services](../backend/app/capabilities/insights/), [analytics](../backend/app/capabilities/analytics/).

## Supporting board and remaining plan items

- Observed repeat intervals, due-date tiers and industry/category portfolios are implemented. The extract starts substantively in 2024; the board's “since 2021” is not available history.
- Failed-calibration and first-calibration rate analyses are not exposed as integrated sales features. Due-type business semantics and behavior relative to order receipt dates are not fully validated or implemented; stop/date checks are only part of that work.
- Behavior segmentation, sector history, independently evaluated sector outlook and supported correlation are implemented. Correlation is not multivariate forecasting.
- Daytona code execution/file artifacts, arbitrary report generation, browser command application receipts, contact-effort budgeting, monthly customer forecasts/uncertainty, multivariate forecasting and live CRM/quotes/contacts remain absent.
- Historical analytics need matching prepared artifacts. A fresh synthetic clone deliberately has unavailable model sections; a passing fixture test does not prove every historical account is supported.

## Challenge 1 scope

Challenge 1 is not the selected integrated application. Existing `challenge1_mr7.html`, MR7 analysis and training/EDA scripts are exploratory/static deliverables.

| Official requirement | Integrated application status |
| --- | --- |
| 3/6/12-month capacity utilization | Not complete; analysis/static forecasts are not a full capacity workflow. |
| Bottlenecks for every laboratory | Not complete; no all-room operational board/decision cycle in Pulse. |
| Staff availability and expected orders | Not complete; future staffing and live backlog inputs are missing. |
| Intelligent missing-date handling | Shared sales requirement inference exists; not integrated into validated all-room workload/capacity forecasts. |
| Concrete capacity recommendations | Exploratory scenarios do not establish eligibility, shared comparison, an owned agreed plan or production staffing recommendations. |

## Verification performed in this audit

- Application `.venv/bin/python -m unittest discover -s backend/tests -q`: **211 tests passed**. Includes API/contracts, requirement/peer/ranking rules, chronological analytics, workflow persistence/suppression, deterministic agent tools/history, voice adapter authorization/interruption/stale replies and error handling.
- `node --test tests/*.test.mjs` from `frontend`: all three test files passed. Running each directly additionally confirmed **14 individual cases**: 4 speaker-output, 8 LiveKit transport and 2 VoicePanel handler cases. Voice transport/provider dependencies are mocked.
- `pnpm typecheck` from `frontend`: **passed**.
- Reviewed download handlers, chart tool/renderer, voice/client/server interruption and route wiring. No CSV/PDF path was found. No feature implementation was changed by this audit.
- Inspected only the small manifest in local compact snapshot `historical-full-20260831-v2`: extraction `2026-10-07T12:49:52+00:00`, reference `2026-08-31`, complete month `2026-08`. This is provenance inspection, not independent whole-file hash verification or proof of current server selection.
- No new SQL refresh, model training, live paid-provider request, hardware microphone/speaker test, browser acceptance run or production build was performed. Previous handover records describe browser/generated-audio checks; they are historical evidence, not fresh results of this audit. Automated tests verify implementation paths, not recognition accuracy or real-world commercial forecast quality.

## Remaining work to close the requested gaps

1. Add CSV download for the shortlist/customer evidence with explicit scope, source date and stable IDs.
2. Add a printable/PDF preparation or shortlist report with the same evidence, owners and next steps.
3. Add generated chart download if graph sharing is required.
4. Establish whether “live graph” means on-demand creation (already present) or a continuously refreshed operational feed (requires new source integration).
5. Complete a fresh browser and user microphone acceptance pass before calling voice hardware behavior verified on this machine.

These are outstanding items, not changes implemented by this validation request.
