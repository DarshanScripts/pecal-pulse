# PeCal Pulse

An Inside Sales assistant for Perschmann Calibration's **Challenge 2: Customer Activity Monitoring**. Choose a customer, understand the evidence, prepare a conversation, and save the next step.

## What works

- **Dashboard:** filtered opportunity map, explainable account ranking, shortlists, ownership and overdue-task coverage.
- **Customers:** calibration history, recorded/inferred requirement windows, supported three-month calibration outlook, industry portfolio questions and conversation preparation.
- **Insights:** sector history/outlook, correlation, retention evidence and model-quality disclosures.
- **Pulse:** streamed English/German chat, conversation history, workspace controls, local workflow tools, email drafts and on-demand charts with an enlarged view.
- **Voice:** English/German LiveKit push-to-talk. Hold Space and release to send, or tap the orb to start/finish. Space starts a new request during a reply; tapping the active orb stops it.
- **Sharing:** TXT preparation briefs/action shortlists and JSON saved shortlist IDs.

**CSV/PDF export is not implemented.** Charts use the selected snapshot; they are not a live SQL feed. Forecast volume means calibration events, not commercial orders. Churn signals and quantity-based priority are proxies; CRM, live quotation/contact feeds and validated revenue/margin are unavailable. See the [complete implementation checklist](docs/challenge-validation.md).

## Run locally

Requires Python 3.13+, uv, Node.js and pnpm (the frontend declares pnpm 11.21.0). From this directory, create an ignored `.env` using [.env.example](.env.example), then:

```bash
uv sync
pnpm --dir frontend install
bash scripts/dev.sh
```

Open [the app](http://127.0.0.1:3000) or [API docs](http://127.0.0.1:8001/docs).

Set `OPENROUTER_API_KEY` and `LLM_MODEL` for AI chat. Voice additionally needs `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` and enabled LiveKit Cloud inference. Voice uses Deepgram Nova-3 transcription and Cartesia Sonic-3 speech. Restart the API after changing configuration; keep keys server-side.

A fresh clone uses the labeled `synthetic-v1` fixture. Historical data and trained outputs are private local files, not bundled in Git. For a prepared historical dataset, set `PECAL_SNAPSHOT` to its snapshot ID and `PECAL_ANALYTICS_ROOT` to its matching analytics directory. Keep compact snapshot JSON and its indexed requirements database together. See [data preparation and refresh](docs/data-refresh.md).

## Checks

```bash
uv run python -m unittest discover -s backend/tests -q
node --test frontend/tests/*.test.mjs
pnpm --dir frontend typecheck
pnpm --dir frontend build
```

Stop the frontend before building into its active `.next` directory. The 8 October audit passed 211 backend tests, 14 frontend voice/output cases and typecheck; fresh browser/hardware acceptance remains separate.

Next.js/TypeScript, assistant-ui, Zustand and ECharts provide the UI; FastAPI, LangGraph/OpenRouter, SQLite and offline scikit-learn analytics provide the backend. [Agent details](backend/app/agents/README.md), [project plan](plan.md), [handover](AGENTS.md).
