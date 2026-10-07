# perschmann-hack
Hack The Lab by Perschmann Calibration


## Local development

Run `uv sync`, `pnpm --dir frontend install`, then `bash scripts/dev.sh`.
Open http://127.0.0.1:3000. API docs: http://127.0.0.1:8001/docs.
Copy `.env.example` to a local `.env` and supply `OPENROUTER_API_KEY` privately.

Team ownership and contracts: [plan.md](plan.md) and [context.md](context.md).
Implemented chatbot routes, controls, tests and remaining work: [agent README](backend/app/agents/README.md).
