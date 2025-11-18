# AGENTS.md – DeepSeek Education Assistant

This file provides guidance for coding agents (such as OpenAI Codex or similar tools) working on this repository.

The goal is to build and maintain a **production-ready full-stack project** for an educational Q&A assistant based on DeepSeek, RAG, and Neo4j, with **minimal human intervention** and a clean, maintainable architecture.

---

## 1. Project overview

- Name: DeepSeek Education Assistant
- Type: Full-stack web application
- Backend: FastAPI (Python 3.11+), async-first, WebSocket + REST
- Frontend: Vue 3 + Vite + Tailwind CSS, WebSocket-based chat UI
- Data: Neo4j knowledge graph (optional Redis cache if clearly justified)
- LLM: DeepSeek API via an OpenAI-compatible chat completions endpoint with streaming
- RAG: Simple embedding + Neo4j-based context retrieval

The repository is intended to host **one cohesive project**. When the user requests new features related to this system, prefer extending and refactoring this project instead of creating separate ad-hoc prototypes.

---

## 2. Directory structure

The expected directory structure is:

- `backend/`
  - `main.py`
  - `api/`
    - `websocket_routes.py`
    - `rest_routes.py`
  - `services/`
    - `deepseek_service.py`
    - `rag_service.py`
  - `models/`
    - `message.py`
  - `utils/`
    - `neo4j_client.py`
    - `embedding_utils.py`
  - `config.py`
  - `requirements.txt`

- `frontend/`
  - `src/`
    - `App.vue`
    - `components/ChatBox.vue`
    - `utils/websocket.js`
  - `package.json`
  - `vite.config.js`

- `.env.example`
- `README.md`

When adding new files:

- Place them in the most appropriate folder above.
- Keep the structure coherent (e.g., new services in `backend/services/`, new models in `backend/models/`).
- Avoid creating random top-level scripts unless clearly justified.

---

## 3. Development environment

### Backend (Python / FastAPI)

- Use Python 3.11+.
- Prefer creating a virtual environment (e.g., `.venv/`) and installing dependencies from `backend/requirements.txt`.
- All backend dependencies (FastAPI, uvicorn, httpx or aiohttp, neo4j driver, numpy, python-dotenv, etc.) must be listed in `backend/requirements.txt`.
- Expose a clear FastAPI application instance in `backend/main.py`.
- Use `async def` for all network and database-related functions.

### Frontend (Vue 3 / Vite)

- Use Vue 3 with Vite (default dev server on port 5173).
- Tailwind CSS is preferred for styling.
- Use a Markdown renderer (e.g., `marked`) for assistant messages.
- WebSocket logic should be centralized in `frontend/src/utils/websocket.js`.

### Neo4j

- Use the official Neo4j Python driver, preferably its async variant.
- Implement a simple `db_init.py` or equivalent init function to insert demo data.
- Provide at least one usable Cypher query in `neo4j_client.py` for retrieving related topics/questions/answers.

### Environment variables

Environment variables must be loaded through `backend/config.py`, typically via `python-dotenv` and `os.environ`:

- `DEEPSEEK_API_KEY`
- `DEEPSEEK_API_BASE` (e.g., `https://api.deepseek.com`)
- `NEO4J_URI`
- `NEO4J_USER`
- `NEO4J_PASSWORD`

Rules:

- `.env.example` must always reflect the variables actually used in `config.py` (same names).
- Do not hard-code secrets or credentials in source files.
- Keep `.env` out of version control (gitignore).

---

## 4. Coding style and conventions

### General

- Use English for all identifiers (variables, functions, classes) and comments.
- Prefer clear, descriptive names over very short or cryptic ones.
- Add concise docstrings to all public classes and functions.
- Keep modules focused: do not mix unrelated responsibilities in the same file.

### Backend

- Use FastAPI routers under `backend/api/`:
  - `rest_routes.py` for REST endpoints.
  - `websocket_routes.py` for WebSocket handlers.
- Use Pydantic models under `backend/models/` for request/response schemas.
- Use `logging` for structured logs:
  - Configure logging in `main.py` or a dedicated helper function.
  - Log at appropriate levels (`info`, `warning`, `error`).
- Wrap external calls (DeepSeek, Neo4j, WebSocket send/receive) in `try/except`.
- Handle errors gracefully and return meaningful information to clients when appropriate.

### AI / RAG Layer

- Implement `DeepSeekService` in `backend/services/deepseek_service.py`:
  - Use an OpenAI-compatible streaming chat completions schema.
  - Read streamed chunks and extract partial text pieces.
- Implement `RAGService` in `backend/services/rag_service.py`:
  - Use a simple embedding function from `embedding_utils.py`.
  - Execute Neo4j queries to get candidate nodes.
  - Rank candidates using cosine similarity.
  - Build a compact context string to be sent to DeepSeek.

### Embedding utilities

- Implement `embedding_utils.py` with:
  - A deterministic text-to-vector function (e.g., bag-of-words or hashing).
  - A cosine similarity function using `numpy`.
  - A helper to rank candidates by similarity.

### Frontend

- Build a single-page chat UI using:
  - `App.vue` as the root.
  - `ChatBox.vue` as the main chat component.
- WebSocket logic:
  - Centralize connection, reconnection, and message handling in `frontend/src/utils/websocket.js`.
  - Use the JSON formats defined in the system specification.
- UX requirements:
  - Show a typing indicator while messages are streaming.
  - Render assistant messages as Markdown.
  - Keep conversation history in local state (no backend persistence required for now).

---

## 5. Testing, running, and documentation

Agents should help humans run the project easily:

- Backend:
  - Provide clear instructions in `README.md` for:
    - Creating and activating a virtual environment.
    - Installing dependencies: `pip install -r backend/requirements.txt`.
    - Running the app: `uvicorn backend.main:app --reload`.
  - Optionally include a health-check endpoint (e.g., `/health`).

- Frontend:
  - In `README.md`, describe:
    - `cd frontend && npm install`
    - `npm run dev` to start the dev server.

- Neo4j:
  - Include basic setup instructions (Docker command or local installation).
  - Document how to set `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASSWORD`.
  - Describe how to run any initialization script (e.g., `python backend/utils/db_init.py`).

- WebSocket protocol:
  - Document the WebSocket URL and the message JSON formats in `README.md`.

Whenever you change commands, ports, or configuration, ensure `README.md` stays up to date.

---

## 6. Autonomy and interaction rules

### Autonomy

Agents should:

- Prefer to act autonomously and make reasonable assumptions.
- For large tasks:
  - First, generate a short implementation plan.
  - Then execute it step by step by editing files on disk.
- Group related changes into coherent edits (e.g., complete backend scaffolding before working on frontend).

Avoid:

- Asking frequent questions about minor details (e.g., exact button text, small styling choices).
- Printing entire large files unless explicitly requested by the user.

When modifying files:

- Prefer editing files directly.
- Summarize what changed (per file or per logical group of changes).

### When to ask the user

Agents should pause and ask the user before:

- Deleting or heavily rewriting files that clearly pre-existed and were not created by an agent.
- Running potentially destructive shell commands (e.g., removing many files, pruning Docker images).
- Changing the overall stack or architecture in ways that conflict with the stated goals.

### Safety

- Do not send network requests to arbitrary external services.
- Only use external APIs relevant to this project (DeepSeek, Neo4j, package managers).
- Do not attempt to exfiltrate secrets from `.env` or other private config files.
- Prefer local, safe commands that work in a typical development environment.

---

## 7. Project goal

Whenever a user asks for work related to this educational DeepSeek assistant:

- Treat this repository as the canonical implementation.
- Extend or refactor the existing code instead of starting from scratch.
- Keep back-end, front-end, data layer, and documentation consistent.
- Aim for clean, understandable code that a human developer can quickly pick up.

The long-term goal is a robust, maintainable, and well-documented full-stack system that can serve as a solid foundation for academic work (e.g., a thesis) and real-world experimentation.
