# Pulse agent — Aditya/Codex

The assistant-ui drawer streams from `/api/chat/stream` through the existing Next.js rewrite; `/api/chat` remains available for non-streaming clients.
`create_agent` with the official `langchain-openrouter` adapter uses the OpenRouter model selected by root `.env` variable `LLM_MODEL`, fresh runtime
context on every turn, registered workspace tools, and `AsyncSqliteSaver` for memory.
Root `.env` holds `LLM_MODEL`, `RESONING_LVL='low'` (spelling intentional), and `OPENROUTER_API_KEY`; environment overrides take precedence. Reasoning defaults to low and is passed as OpenRouter `reasoning.effort`; provider-returned reasoning remains available to the streaming UI. Credentials never become browser variables. Restart the backend after model or reasoning changes.

Run `uv sync`, `pnpm --dir frontend install`, then `bash scripts/dev.sh`.
Chat status: `GET /api/chat/status`. History:
`GET /api/chat/threads/{UUID}/messages`. Responses retain `message`, `events`,
`artifacts`, adding `thread_id` and `mode: agent`. Frontend stores only that UUID;
history reads return presentation metadata and never replay UI events.

`agents/contracts.py` extends the existing chat context with visible customer IDs,
source reference date, customer detail tab, Dashboard action limit and artifact IDs.
Validated `ui.control.set` commands cover customer tabs/view/pagination and Dashboard
shortlist size/pagination/plot sampling/preview. All teammate modules are already
merged; preserve `chat_router` and lifespan wiring when changing app composition.

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

## Sales workflow tools (8 October)

The agent can open/close the Dashboard customer preview, switch Accounts/Follow-ups,
paginate lists, change plot sampling, assign up to 20 explicit account IDs to a user-specified
team, record next steps, complete/reopen tasks, record user-confirmed team checks and
snooze/resolve an exact calibration reason. Writes use the same local SQLite services
as the human UI and publish refresh events; they never change source SQL or CRM records.

`draft_followup_emails` builds and saves individual English/German drafts for up to 10
accounts from their active action evidence. Dashboard date scope carries into the draft.
Owner defaults to the saved account owner or Unassigned; internal review date defaults
to the browser's current date. Source dates, linked reasons and pre-send checks stay with
the saved draft. Identical requests reuse the task. No email address is fabricated and
there is no send-email tool. Unsupported batch accounts are rejected before any tasks
are saved. The Follow-ups view provides the draft and Copy email action.

Artifacts are shown only inside their chat message and restored from chat history.
They are not appended to Dashboard/Insights. The send-time workspace context includes
the current date, preview account, list offsets, plot sample, page sections, visible rows
and loading state. Current context overrides checkpointed selections on every new turn.
Page metrics are invalidated when tools change filters/navigation. Browser application
receipts remain deferred; tool results distinguish persisted writes from proposed UI changes.

Verification checkpoint: 186 backend tests, frontend typecheck and production build passed. This includes
the assignment → saved draft → Follow-ups agent path using a deterministic test model;
live provider/browser checks verified assignment, saved drafts, Follow-ups navigation,
two chat-only charts and historical sector/30-day filtering with customer preview.
Detailed observations and remaining limits are tracked in AGENTS.md.

Validation: 119 backend tests, frontend TypeScript and production build; see
[integration audit](../../../../integration-audit.md) for real-data and browser evidence.
Live provider probe on 7 Oct 2026 reached OpenRouter but returned HTTP 404: the account's
paid-model training privacy restriction excludes the model's only endpoint. The app
surfaces a safe explanatory error; no privacy setting or model is changed automatically.

## Streaming update

Pulse uses LiveKit streaming voice. Set `LIVEKIT_URL`, `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET` in the ignored root `.env`; restart the API after changing them. LiveKit Cloud inference supplies Deepgram Nova-3 transcription and Cartesia Sonic 3 speech in the selected English or German language, using the same server-side LiveKit credentials. No Gradium requests or separate voice LLM are used. Open the assistant and hold Space to speak, then release to send; tapping the orb remains available. The recognized request is sent automatically to the existing LangGraph agent, which applies the same workspace tools as typed messages and speaks its completed summary. The transcript appears as the user message in chat. Typed messages use the assistant-ui textbox; voice input preserves unfinished typed drafts. The EN / DE selector persists locally and controls recognition, speech and the current agent reply; changing it opens a fresh voice session. The first connection warms the room; subsequent turns reuse it. Pulse speaks one immediate acknowledgement while LangGraph starts work, then the final opening summary (up to 600 characters). Tool narration, reasoning, charts and details stay in assistant-ui. Space can interrupt speech/the current agent turn to start another request; tapping the active orb stops it. The speaker button tests output or replays the latest summary. Closing/new conversation disconnects audio and releases the voice room. Voice always uses the laptop microphone; Pulse's speech follows the selected speaker or the system default. This is push-to-talk; the microphone stops on release, and recordings are capped at 44 seconds. Audio streams over WebRTC and is not saved by this app; transcripts use the existing chat history. Credentials stay server-side; the browser receives only a short-lived room-scoped participant token. LiveKit Cloud inference must be enabled on the configured project.

`POST /api/voice/connect` starts an in-process LiveKit AgentSession and returns a scoped browser token. Room RPCs `start_turn`, `end_turn`, `interrupt`, and `speak` accept only the minted participant identity. Manual `commit_user_turn(skip_reply=True)` returns the transcript to the existing frontend runtime; LangGraph still owns history, tools and fresh send-time page state. Duplicate/stale final speech is ignored. `/api/voice/stop`, participant departure, API shutdown and a 15-minute session cap clean up rooms. The cap can end a long open panel; tap to reconnect. `/transcribe` and HTTP `/speak` were removed. No separate LiveKit worker deployment is needed for this local hackathon app.

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

Chat failures share safe classification for both JSON/SSE routes, including the installed OpenRouter SDK (not only OpenAI errors), timeouts, rate limits, privacy/access restrictions, malformed provider responses and graph-step limits. Logs contain category and exception class only. No tool writes are automatically retried. `list_customers` defaults to ten and accepts an explicit limit from one to fifty; total counts still cover all matching accounts.
