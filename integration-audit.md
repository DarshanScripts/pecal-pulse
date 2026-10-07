# Challenge 2 integration audit

Date: 7 October 2026. Historical source reference: 31 August 2026. This is a local historical prototype, not live sales operations.

## Merge and ownership verification

Member 3 (`origin/feat/sales-intelligence`, `015ee7b`) delivered peer portfolio discovery, instrument bundling, transparent ranking, preparation and compatibility adapters. Member 1 (`origin/member-1`, `5938324`) incorporated it and delivered shared contracts, immutable snapshots, requirements, v2 APIs and SQLite workflow. Member 2 (`origin/feat/ml-analytics`, `67b0f54`) incorporated both and delivered offline segmentation, activity/volume evaluation, inactivity and sector analytics.

All three tips are ancestors of main. They were not all merged into Member 3's branch: Member 2's branch contained all three. Separate merge commits preserve the original work. Our streaming agent, expandable assistant-ui panel, returned reasoning, tool traces, cancellation and SQLite chat recovery were retained.

## Work completed during integration

- Connected all three frontend pages to typed v2 responses instead of legacy mock cards. Dropdowns use real industry IDs and learned segment labels; customer lists are server-filtered and paginated. Any known account can open independently of the loaded list page.
- Connected chatbot evidence, filter, selection, tab, navigation and chart tools to the same snapshot. Page snapshots provide exact labels, values, units, scope and definitions. Tool responses have explicit evidence counts and bounded samples; chart data comes from observed source services.
- Added historical source/quality and model coverage disclosures; unsupported forecasts remain unavailable. Displayed calibration events, distinct instruments and order counts are not interchangeable.
- Wired manual quotation checks, preparation exports, reason-specific suppression/snooze and local follow-ups. Workflow corrections refresh only the affected account and update the ranked queue. Invalid reasons are rejected before writes. Legacy synthetic tasks remain stored but are not shown as historical customer tasks.
- Corrected calendar month length, unknown-date eligibility, peer portfolio lookback and miscellaneous-industry exclusions. Protected immutable snapshot publication and validated snapshot paths.
- Fixed expensive repeated population scans with snapshot/customer/peer indexes and cached queue composition. Cold full-snapshot loading remains substantial; measured initial bootstrap was 56 seconds on this machine.
- Restricted due-window outreach reasons to supported windows within 90 days either side of the historical reference. This is an explicit business policy, not a model finding. Past-due records require review; older/far-future evidence remains available. Initial reason and preparation lists are bounded for usability.

## SQL evidence and repairs

Source queries were read-only. Raw data and runtime artifacts remain ignored.

The calibration customer number is varchar while the instrument master uses nvarchar. Hashing their native encodings produced incompatible IDs and zero current-owner/history joins. Casting instrument customer numbers to the same varchar encoding before hashing repairs the join: 6,507 of 6,525 current owners match historical accounts; 18 remain new/unsupported cases. Historical events keep their historical customer attribution.

Numeric interval units were verified against repeated calibration/recorded-due gaps: 1 = years, 2 = months, 3 = weeks, 4 = days. Evidence medians were approximately 365.2, 30.42, 7 and 1 days per unit. Day/week-to-month conversion is approximate and flagged; implausible >10-year month/year intervals are rejected. A slow all-history MAX join was replaced by bounded streaming SELECT exports. Last observed calibration is derived only from events before the history cutoff.

The instrument master was extracted now; it is not reconstructed point-in-time as of August. Stop flags and current due dates must not be presented as historical proof or live readiness. Explicit unknowns and manual checks remain necessary.

## Selected local data and measured models

Local snapshot: `historical-full-20260831-v2`; actual extraction timestamp `2026-10-07T18:58:19Z`. It contains 6,564 accounts, 156,117 monthly rows (118,844 covered zero rows), 20,300 portfolio rows, 488,699 instruments/requirements and 652,138 calibration events. History covers January 2024–August 2026. Current-owner-only accounts do not gain fabricated history.

3,180 accounts meet prediction support criteria. Unsupervised clustering selected three readable segments. Activity target is **at least one observed calibration at Perschmann in September–November 2026**, not an order, conversion or churn.

| Evaluation | Selected method | Historical holdout result |
|---|---|---|
| Three-month activity | Logistic regression, raw probability | ROC AUC 0.7887; AP 0.8181; Brier 0.1860 |
| Recency activity baseline | Recency | ROC AUC 0.7081; Brier 0.2615 |
| Three-month calibration volume | Previous 12 months / 4 | MAE 11.5166; WAPE 65.05% |

Training/calibration/selection/test boundaries are disjoint by label window. Test origins are December 2025–May 2026, with outcomes ending August 2026. These are repeated customer-origin observations, not independent customers or causal outreach results. Customer quantities are directional because volume error is high; no monthly customer forecasts or uncertainty intervals are supplied.

Sector output supplies an independently evaluated one-month baseline forecast and Pearson correlation of monthly log1p volume changes. Correlation needs at least 24 aligned changes; unsupported pairs remain blank. It does not establish causation or produce a multivariate forecast.

## Verification and remaining scope

119 backend regression tests pass, including source repairs, shared contracts, chronological evaluation, suppression/persistence, checkpoint recovery, tool validation and snapshot-grounded context. Frontend TypeScript and production build pass.

Browser verification confirmed historical totals/coverage, filtered Automotive accounts, portfolio and due-date evidence, and expandable chat. An approved live OpenRouter test read the exact dashboard values (6,564 accounts and 347,923 recorded requirement records), explained their all-snapshot/all-date scope, and visibly applied the actual Automotive dropdown and Customers navigation. Streaming Markdown, Thinking and completed tool blocks were visible. A second live turn opened a real account outside the loaded page, retrieved historical evidence, created its observed activity chart and correctly described its 93.1% probability as any calibration in September–November 2026. Browser verification caught a leftover synthetic artifact label; it was corrected to follow the artifact source.

Remaining enhancements: Daytona arbitrary code/file artifacts, explicit browser event application receipts/revisions, voice, live CRM/contact/order integration, commercial value, confirmed churn labels, monthly customer predictions/uncertainty and multivariate sector forecasting. Standard service-backed chart artifacts already work. These enhancements must not be represented as implemented.

Manual workflow inputs are local prototype facts. No customer outreach, CRM writes, confirmed churn, revenue gain or staffing commitment has been established.
