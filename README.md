# AI Agent Template

FastAPI-based boilerplate for building LangGraph-powered agents with streaming, observability, and modularity in mind.

[![CI](https://github.com/assada/agent_template/actions/workflows/ci.yml/badge.svg)](https://github.com/assada/raw_langgraph/actions/workflows/ci.yml)

## TL;DR

This is a minimal and extendable template for running LangGraph agents over HTTP.

It supports:

* Server-Sent Events (SSE) streaming for real-time response updates
* Swagger/OpenAPI docs out of the box (thanks to FastAPI)
* Langfuse observability and prompt tracing
* User feedback tracking and thread history
* Clean FastAPI + Uvicorn setup with Docker, ruff, mypy, and pyright
* Plug-and-play LangGraph integration, including tool support and memory
* Dev-friendly structure with clear separation between core app and agent logic

Use it as a starting point for building custom AI agents with solid HTTP and observability layers.

---

## Quick Start

1. Clone
2. `cp .env.dist .env` and fill in the required environment variables
3. `docker compose up`
4. Open your browser and go to `http://localhost:8000`

### Setup local langfuse (https://langfuse.com/self-hosting/docker-compose)

1. Clone the langfuse repository: `git clone https://github.com/langfuse/langfuse.git`
2. `cd langfuse`
3. `docker compose up -d`
4. Open your browser and go to `http://localhost:3000` create a new project and copy the `LANGFUSE_API_KEY` and
   `LANGFUSE_API_URL` to your `.env` file.

### Development

1. `uv venv`
2. `uv sync`
4. `npm run build`
5. `cd ..`
6. `uv run dev`

## Status

This is still a work in progress, but usable.

PRs welcome for:

* OAuth2
* Guardrails
* Multi-agent support (with framework abstraction)
* LangFuse abstraction
* Evaluations
* Anything that reduces my boilerplate suffering

### Raw and old TODO:

- [x] Add a way to add tools to the agent
- [x] Add a way to add a database to the agent (memory, checkpoints, feedback?, etc)
- [x] Implement graph instead of simple agent
- [x] Refactor the structure of the project. We need to separate general fastapi app from the agent app.
- [x] Add more model configuration options (temperature, top_p, etc)
- [x] Add a way to get a thread history
- [x] Normalize FastApi headers/request/middleware
- [x] Add Langfuse integration
- [x] Add tests
- [x] refactor checkpointer shit factory
- [ ] 🟠 [**raw api implemented**] thread management Create/Update/Delete (thread model(ulid, user_id, created/updated,
  title, status[]))
- [ ] 🟠 [**50/50 DONE**] Store the thread history in the database (with all custom messages and metadata)
- [ ] 🟠 Add a way to define a custom agent in config?
- [ ] ~~Add Langsmith integration~~
- [ ] ~~Keep alive SSE connection until the user closes the browser tab (??)~~
- [ ] 🟡 Add a way to validate the user's access token (OAuth2)
- [ ] 🟡 Add evaluation metrics
- [ ] 🔴 Add *one more* abstraction layer so the agent can use different frameworks (LangGraph, LlamaIndex, etc.)
- [ ] 🟠 Add even more fucking abstractions to make it independent of observability tools (LangFuse, LangSmith, Grafana
  Alloy, or whatever the fuck else)
- [ ] ⚪ Long-Term memory for each user. I want to add to chat application for real-time per thread prompt tuning - memory
  insights, response strategies, etc. But this is more about agent implementation not template core. Graph node as "
  addon package?" LOL! https://i.imgur.com/k1jk3cx.png here we go again!
- [ ] ⚪ Guardrails ([LLMGuard implementation](https://github.com/assada/agent_template/tree/feat/guardrails) or handle
  by [LiteLLM](https://docs.litellm.ai/docs/proxy/guardrails/quick_start))

⚪ - LOWEST priority | 🟡 - LOW priority | 🟠 - MID priority | 🔴 - HIGH priority | 🟣 - BLOCKER