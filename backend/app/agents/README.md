# Pulse agent — Aditya/Codex

The assistant-ui drawer streams from `/api/chat/stream` through the existing Next.js rewrite; `/api/chat` remains available for non-streaming clients.
`create_agent` with the official `langchain-openrouter` adapter uses the OpenRouter model selected by root `.env` variable `LLM_MODEL`, fresh runtime
context on every turn, registered workspace tools, and `AsyncSqliteSaver` for memory.
Root `.env` holds `LLM_MODEL` and `OPENROUTER_API_KEY`; environment overrides take precedence. Credentials never become browser variables. Restart the backend after model changes.

Run `uv sync`, `pnpm --dir frontend install`, then `bash scripts/dev.sh`.
Chat status: `GET /api/chat/status`. History:
`GET /api/chat/threads/{UUID}/messages`. Responses retain `message`, `events`,
`artifacts`, adding `thread_id` and `mode: agent`. Frontend stores only that UUID;
history reads return presentation metadata and never replay UI events.

`agents/contracts.py` extends the existing chat context with visible customer IDs,
source reference date, customer detail tab, Dashboard action limit and artifact IDs.
New `ui.control.set` commands have two validated controls: `customers.tab` and
`dashboard.action_limit`. Other command names remain unchanged. The sales API no
longer owns `/chat`; Member 1 should retain `chat_router` and lifespan wiring when
merging app composition. Core dependencies were added here so Member 1 must merge
these `pyproject.toml`/`uv.lock` changes before editing dependency files.

Tools use shared v2 APIs/services whenever WorkspaceContext.snapshot_id is supplied.
The selected historical snapshot and exact page metrics ground each turn. Legacy
contexts without a snapshot retain the original mock service for compatibility. Tools read
context/account evidence, list accounts, change filters, select customers, navigate,
change tabs/list size, and create service-backed industry/activity/portfolio charts.
Tool validation is applied before event publication. Replies propose actions for
the frontend event router; they cannot confirm the browser applied them yet.

One active run per thread, maximum 12 tools, 30 graph steps, 90-second turn timeout.
Checkpoint and normalized display history persist in the ignored runtime database.
Cancelling the stream stops token updates and releases the active thread. Completed tools may already have applied reversible UI events; cancellation does not roll these back. Browser application acknowledgements remain follow-up work.
No direct SQL execution, arbitrary browser JavaScript, live outreach, or Daytona code
execution is exposed in this slice. Next slice: sandbox execution/artifact downloads,
application receipts with state revision handling.

Validation: 119 backend tests, frontend TypeScript and production build; see
[integration audit](../../../../integration-audit.md) for real-data and browser evidence.
Live provider probe on 7 Oct 2026 reached OpenRouter but returned HTTP 404: the account's
paid-model training privacy restriction excludes the model's only endpoint. The app
surfaces a safe explanatory error; no privacy setting or model is changed automatically.

## Streaming update

SSE events: `start`, `part`, `delta`, `workspace`, `done`, `error`.
`eventsource-parser` handles framing on the frontend. assistant-ui `GroupedParts`
scopes live text/reasoning/tool parts; MarkdownTextPrimitive renders Markdown as
it arrives, with `remark-gfm` for tables and task lists. Reasoning stays in a collapsible Thinking block and appears only when
the provider returns it. Tool blocks disclose arguments, running/completed/error
state and results. Completed content parts persist with the normalized history.
Restoring history never replays workspace commands. UI events apply once during
the stream, deduplicated by event ID. Failures leave the partial response visible.

The active model now comes from root `LLM_MODEL`; the configured DeepSeek model
was verified live with streamed reasoning, Markdown tokens and a completed tool
call. The original Muse account-policy error above describes an earlier probe.
