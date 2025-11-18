# Codex Session Summary – DeepSeek Education Assistant

## Overview

During this session, we scaffolded and implemented a production‑ready full‑stack system for an educational Q&A assistant titled **“基于DeepSeek大语言模型的教育智能客服系统设计与实现”**. The stack includes:

- Backend: FastAPI (Python 3.11+ compatible), async REST + WebSocket.
- AI/RAG: DeepSeek streaming chat integration + Neo4j‑backed retrieval layer with simple embeddings.
- Frontend: Vue 3 + Vite + Tailwind CSS chat UI with WebSocket streaming and Markdown rendering.
- Data: Neo4j knowledge graph (optional demo seeding).

The project follows the structure and conventions described in `AGENTS.md`.

---

## Backend Work

### 1. Package layout and requirements

- Created `backend/` as a proper Python package with:
  - `backend/__init__.py`
  - `backend/api/__init__.py`
  - `backend/services/__init__.py`
  - `backend/models/__init__.py`
  - `backend/utils/__init__.py`
- Added `backend/requirements.txt` listing core dependencies:
  - `fastapi`, `uvicorn[standard]`, `httpx`, `python-dotenv`, `neo4j`, `numpy`, `pydantic`.

### 2. Configuration

- Implemented `backend/config.py`:
  - Uses `python-dotenv` (`load_dotenv()`) to load environment variables from `.env`.
  - Defines a `Settings` Pydantic model with:
    - `deepseek_api_key`, `deepseek_api_base`.
    - `neo4j_uri`, `neo4j_user`, `neo4j_password`.
    - `backend_port`, `frontend_origin`.
  - Exposes a cached `get_settings()` accessor for consistent configuration.

### 3. Pydantic models

- Implemented `backend/models/message.py`:
  - `UserMessage`: WebSocket input model with `type="user_message"`, `message_id`, `content`, optional `conversation_id`.
  - `AssistantChunk`: WebSocket output model with `type="assistant_chunk"`, `message_id`, `content`, `is_final`.
  - `HealthResponse`: simple `{"status": "ok"}` response body for health checks.

### 4. REST API

- Implemented `backend/api/rest_routes.py`:
  - Defines `router = APIRouter(prefix="/api", tags=["api"])`.
  - `GET /api/health` → returns `HealthResponse(status="ok")` to validate backend availability.

### 5. WebSocket API with RAG + DeepSeek

- Implemented `backend/api/websocket_routes.py`:
  - Creates a WebSocket router at `/ws/chat`.
  - Initializes:
    - `Neo4jClient` (if Neo4j config is present).
    - `RAGService` (using the Neo4j client, or `None` with graceful fallback).
    - `DeepSeekService` (using `DEEPSEEK_API_KEY` and `DEEPSEEK_API_BASE` from settings).
  - Defines a system prompt (`_SYSTEM_PROMPT`) describing the assistant’s educational role.
  - Core flow for each WebSocket message:
    1. Accept the connection and continuously read `receive_text()` messages.
    2. Parse incoming JSON into `UserMessage`; on parse error, send a single error `AssistantChunk` and continue.
    3. Build context via `RAGService.build_context(message.content)`:
       - On RAG error, log and send a warning chunk, then fall back to the raw user query.
    4. Compose `user_prompt = context + "\n\nUser question: " + message.content`.
    5. Call `DeepSeekService.astream_chat(system_prompt, user_prompt)`:
       - For each text chunk from DeepSeek, send an `AssistantChunk` with `is_final=False`.
       - After streaming completes, send a final `AssistantChunk` with `content=""` and `is_final=True`.
    6. On DeepSeek error, log and send a final error `AssistantChunk` with `is_final=True`.
  - Handles `WebSocketDisconnect` and unexpected exceptions without bringing down the process.

### 6. Application entrypoint and logging

- Implemented `backend/main.py`:
  - `configure_logging()` sets up a root logger using `logging.config.dictConfig` with a console handler and structured format.
  - `create_app()`:
    - Calls `configure_logging()` and loads settings via `get_settings()`.
    - Creates the FastAPI app with title/version.
    - Configures CORS to allow `settings.frontend_origin` (default `http://localhost:5173`).
    - Includes REST and WebSocket routers.
  - Exposes a top‑level `app = create_app()` for uvicorn (`uvicorn backend.main:app --reload`).

---

## AI / RAG Layer

### 1. Embedding utilities

- Implemented `backend/utils/embedding_utils.py`:
  - Defines `EMBEDDING_DIMENSION = 256`.
  - `_tokenize(text)`: simple lowercase whitespace tokenization.
  - `embed_text(text)`: hashed bag‑of‑words:
    - Hashes tokens into a fixed‑size vector (`numpy` array).
    - Normalizes to unit length to approximate cosine behavior.
  - `cosine_similarity(a, b)`: standard cosine similarity with safe denominator.
  - `rank_by_similarity(query_embedding, candidate_embeddings)`:
    - Computes similarity for each candidate.
    - Returns sorted `(index, score)` pairs in descending similarity order.

### 2. Neo4j client and demo data

- Implemented `backend/utils/neo4j_client.py`:
  - `Neo4jClient`:
    - Manages an async `AsyncDriver` from the Neo4j driver.
    - `_get_driver()` lazily constructs and caches the driver.
    - `close()` closes the driver when done.
    - `get_related_qa(query, limit=20)`:
      - Runs a Cypher query that:
        - Matches `(:Question)-[:HAS_ANSWER]->(:Answer)` with optional `(:Topic)-[:HAS_QUESTION]->(:Question)`.
        - Filters where topic, question, or answer text `CONTAINS` the query (case‑insensitive).
        - Returns `topic`, `question`, `answer` fields.
      - Catches and logs errors instead of raising them.
  - `init_demo_data(client)`:
    - Seeds a small knowledge graph using `MERGE`:
      - Topics: Linear Algebra, Calculus, Machine Learning.
      - Questions/answers for each topic.
      - Relationships: `HAS_QUESTION` and `HAS_ANSWER`.
    - Safe to call multiple times due to `MERGE`.

### 3. RAG service

- Implemented `backend/services/rag_service.py`:
  - `RAGService`:
    - Holds an optional `Neo4jClient`.
    - `build_context(query, top_k=5)`:
      - If Neo4j is not configured: logs a warning and returns a simple fallback context.
      - Otherwise:
        1. Embeds the query via `embed_text()`.
        2. Retrieves candidate `(topic, question, answer)` records from Neo4j.
        3. Builds textual snippets per candidate:
           - `"Topic: {topic}\nQuestion: {question}\nAnswer: {answer}"`.
        4. Embeds each snippet, ranks candidates via `rank_by_similarity`.
        5. Selects top‑`k` indices, concatenates snippets into a compact context string prefixed with a short explanation for the LLM.
      - Returns the context to prepend to the user’s question when calling DeepSeek.

### 4. DeepSeek service

- Implemented `backend/services/deepseek_service.py`:
  - `DeepSeekService`:
    - Initialized with `api_key` and `api_base`.
    - Uses `httpx.AsyncClient` with `base_url` and a reasonable timeout.
    - `astream_chat(system_prompt, user_content, model="deepseek-chat")`:
      - Builds an OpenAI‑style request:
        - `model`, `messages` (system + user), `stream=True`.
      - Sends a POST to `/v1/chat/completions` using an async streaming response.
      - Parses `data:` lines (Server‑Sent Events style), decodes JSON, and yields `delta["content"]` if present.
      - Stops when `[DONE]` is seen.
      - Logs parsing warnings and HTTP errors cleanly.
    - `aclose()` closes the underlying HTTP client if needed.

---

## Frontend Work

### 1. Vite + Vue + Tailwind setup

- Added `frontend/package.json`:
  - Dependencies:
    - `vue` (Vue 3).
    - `marked` for Markdown rendering.
  - Dev dependencies:
    - `vite`, `@vitejs/plugin-vue`, `tailwindcss`, `postcss`, `autoprefixer`.
  - Scripts: `dev`, `build`, `preview`.
- Added `frontend/vite.config.js`:
  - Uses `defineConfig` with Vue plugin.
  - Sets dev server port to `5173`.
- Added `frontend/index.html`:
  - Basic HTML shell with a root `#app` and script entry `src/main.js`.
- Tailwind configuration:
  - `frontend/tailwind.config.cjs`:
    - Scans `index.html` and `src/**/*.{vue,js,ts,jsx,tsx}`.
  - `frontend/postcss.config.cjs`:
    - Enables `tailwindcss` and `autoprefixer`.
  - `frontend/src/assets/main.css`:
    - Imports Tailwind base/components/utilities.
    - Applies a light background via `body { @apply bg-slate-100; }`.

### 2. Vue app entry

- Implemented `frontend/src/main.js`:
  - Imports and mounts `App.vue` onto `#app`.
  - Includes global Tailwind styles from `./assets/main.css`.

### 3. WebSocket utility

- Implemented `frontend/src/utils/websocket.js`:
  - Defines `WS_URL = 'ws://localhost:8000/ws/chat'`.
  - Manages a singleton `WebSocket` instance with:
    - `setupSocket()`:
      - Creates the socket.
      - Logs on `open`, attempts reconnection 2 seconds after `close`.
      - Parses incoming `event.data` as JSON and dispatches to all registered listeners.
    - `initWebSocket()`:
      - Ensures a socket is created if not already open.
    - `addMessageListener(listener)`:
      - Registers a listener and returns an unsubscribe function.
    - `sendUserMessage(payload)`:
      - Sends JSON on the socket if it is `OPEN`; logs a warning otherwise.

### 4. Root layout

- Implemented `frontend/src/App.vue`:
  - Centered layout with:
    - Title: **DeepSeek Education Assistant**.
    - Subtitle: Chinese system title.
    - Display of the WebSocket URL for reference.
  - Embeds `<ChatBox />` as the main content area inside a card‑like container.

### 5. Chat UI and behavior

- Implemented `frontend/src/components/ChatBox.vue`:
  - Local state:
    - `messages`: reactive array storing both user and assistant messages.
    - `inputText`: bound to the textarea.
    - `isTyping`: boolean flag controlling the “Assistant is typing…” indicator.
  - Message structure:
    - Each message has `id`, `role` (`'user'` or `'assistant'`), `content`, and `isStreaming` for assistant messages.
  - Markdown rendering:
    - Uses `marked.parse()` to render assistant content as HTML (`v-html`), wrapped in a `.prose` container.
  - ID generation:
    - `generateMessageId()` uses `crypto.randomUUID()` when available, with a timestamp/random fallback.
  - Sending messages:
    - `handleSubmit()`:
      - Reads and trims `inputText`.
      - Appends a user message and an empty assistant message with the same `messageId` and `isStreaming=true`.
      - Sets `isTyping=true`.
      - Calls `sendUserMessage()` with:
        - `type: 'user_message'`
        - `message_id`
        - `content`
        - `conversation_id: null`
      - Clears the input.
    - Enter key behavior:
      - `@keydown.enter.exact.prevent="handleSubmit"` sends the message on Enter.
  - Receiving streamed chunks:
    - `handleAssistantChunk(chunk)`:
      - Ignores messages where `chunk.type !== 'assistant_chunk'`.
      - Finds existing assistant message by `message_id` and appends `chunk.content` to `existing.content`.
      - On `chunk.is_final`, sets `isStreaming=false` and `isTyping=false`.
      - If none exists yet, creates a new assistant message with `content=chunk.content` and `isStreaming=!is_final`.
  - Lifecycle:
    - On mount:
      - Calls `initWebSocket()`.
      - Subscribes to WebSocket messages via `addMessageListener(handleAssistantChunk)` and stores the unsubscribe function.
    - On unmount:
      - Unregisters the listener.
  - UI details:
    - User messages are right‑aligned blue bubbles.
    - Assistant messages are left‑aligned white bubbles with border and Markdown formatting.
    - Typing indicator appears at the bottom of the message list while streaming.

---

## Configuration & Documentation

### 1. Environment template

- Added `.env.example` at project root with:
  - `DEEPSEEK_API_KEY`
  - `DEEPSEEK_API_BASE`
  - `NEO4J_URI`
  - `NEO4J_USER`
  - `NEO4J_PASSWORD`
  - `BACKEND_PORT`
  - `FRONTEND_ORIGIN`
- This is aligned with `backend/config.py` and serves as the template for `.env`.

### 2. README

- Created `README.md` with:
  - High‑level description of the system and its Chinese title.
  - Full project structure tree.
  - Environment variable descriptions and usage of `.env` (with a note not to commit secrets).
  - Backend setup:
    - Creating and activating a virtualenv.
    - `pip install -r backend/requirements.txt`.
    - Running `uvicorn backend.main:app --reload --port 8000`.
    - Using `GET /api/health` for a quick health check.
  - Neo4j setup:
    - Example Docker command to run Neo4j (`neo4j:5`) with `NEO4J_AUTH`.
    - Instructions for setting `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`.
    - Example script to seed demo data using `Neo4jClient` and `init_demo_data`.
  - Frontend setup:
    - `cd frontend && npm install && npm run dev`.
    - Default dev URL `http://localhost:5173`.
    - Notes on adjusting `FRONTEND_ORIGIN` and `WS_URL` if ports/origins change.
  - WebSocket protocol:
    - Client → Server `user_message` JSON format.
    - Server → Client `assistant_chunk` streaming format, including behavior of `is_final`.
    - Explanation of how the frontend aggregates chunks and uses a typing indicator.
  - RAG + DeepSeek behavior:
    - Step‑by‑step description of how the backend uses RAG context and then calls DeepSeek.
  - Development notes and production considerations.

---

## Runtime Environment Notes

From quick checks performed:

- `.env.example` exists; `.env` must be created by copying and editing it.
- No virtual environment (`.venv`) existed initially; the README instructs how to create one.
- Python version detected: `Python 3.13.5` (meets the ≥3.11 requirement, but library compatibility should be watched).
- Backend dependencies (`fastapi`, `httpx`, `neo4j`, `numpy`) were not installed in the global environment; installation via `pip install -r backend/requirements.txt` inside a venv is required.

The README now provides a clear, step‑by‑step guide to:

1. Configure `.env`.
2. Create and activate a Python virtualenv.
3. Install backend dependencies and run FastAPI + WebSocket via uvicorn.
4. Start Neo4j (e.g., with Docker) and seed demo data.
5. Install and run the Vue 3 + Vite frontend.
6. Exercise the full streaming chat path between frontend and backend.

This summary reflects the state of the repository at the end of the Codex CLI session.

