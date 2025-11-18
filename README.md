# 基于DeepSeek大语言模型的教育智能客服系统设计与实现

DeepSeek Education Assistant is a full‑stack educational Q&A system that combines:

- A Vue 3 + Vite + Tailwind chat frontend  
- A FastAPI backend with REST + WebSocket streaming  
- A Neo4j knowledge graph for topics / questions / answers  
- A Retrieval‑Augmented Generation (RAG) layer calling the DeepSeek chat API

The goal is to provide an interactive, streaming chat assistant that answers students’ questions using both a knowledge graph and a large language model.

---

## 1. Project structure

```text
project_root/
├── backend/
│   ├── main.py
│   ├── api/
│   │   ├── websocket_routes.py
│   │   └── rest_routes.py
│   ├── services/
│   │   ├── deepseek_service.py
│   │   └── rag_service.py
│   ├── models/
│   │   └── message.py
│   ├── utils/
│   │   ├── neo4j_client.py
│   │   └── embedding_utils.py
│   ├── config.py
│   └── requirements.txt
│
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   ├── tailwind.config.cjs
│   ├── postcss.config.cjs
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── assets/
│       │   └── main.css
│       ├── components/
│       │   └── ChatBox.vue
│       └── utils/
│           └── websocket.js
│
├── .env.example
└── README.md
```

---

## 2. Environment variables

All backend configuration is loaded via `backend/config.py` using environment variables.  
Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Environment variables:

| Variable          | Description                                             | Example                          |
|-------------------|---------------------------------------------------------|----------------------------------|
| `DEEPSEEK_API_KEY`    | API key for DeepSeek chat completions API             | `sk-xxxx`                        |
| `DEEPSEEK_API_BASE`   | Base URL for DeepSeek API (OpenAI‑compatible)        | `https://api.deepseek.com`       |
| `NEO4J_URI`           | Neo4j Bolt URI                                       | `bolt://localhost:7687`          |
| `NEO4J_USER`          | Neo4j username                                       | `neo4j`                          |
| `NEO4J_PASSWORD`      | Neo4j password                                       | `your_neo4j_password`            |
| `BACKEND_PORT`        | Backend port for FastAPI / uvicorn                   | `8000`                           |
| `FRONTEND_ORIGIN`     | Allowed frontend origin for CORS                     | `http://localhost:5173`          |

> Note: Do not commit `.env` to version control. Use `.env.example` as the non‑secret template.

---

## 3. Backend setup (FastAPI)

### 3.1. Create and activate a virtual environment

From the project root:

```bash
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (cmd)
.venv\Scripts\activate.bat

# Linux / macOS
source .venv/bin/activate
```

### 3.2. Install backend dependencies

```bash
pip install -r backend/requirements.txt
```

### 3.3. Run the backend server

Ensure your `.env` is configured, then:

```bash
uvicorn backend.main:app --reload --port %BACKEND_PORT%
```

By default (from `.env.example`), the backend runs on:

- HTTP base: `http://localhost:8000`
- WebSocket: `ws://localhost:8000/ws/chat`

### 3.4. Health check endpoint

The backend exposes a simple health‑check endpoint:

- `GET http://localhost:8000/api/health`

Response body:

```json
{
  "status": "ok"
}
```

---

## 4. Neo4j setup and demo data

The system uses Neo4j as a knowledge graph storing:

- `Topic` nodes (e.g., Linear Algebra, Calculus, Machine Learning)
- `Question` nodes
- `Answer` nodes
- Relationships: `(:Topic)-[:HAS_QUESTION]->(:Question)-[:HAS_ANSWER]->(:Answer)`

### 4.1. Start Neo4j (Docker example)

If you have Docker:

```bash
docker run \
  --name neo4j-deepseek-edu \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/testpassword \
  neo4j:5
```

Then set in `.env`:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=testpassword
```

### 4.2. Demo data initialization

The file `backend/utils/neo4j_client.py` defines:

- `Neo4jClient` – async client for queries  
- `init_demo_data(client)` – seeds a small demo graph with linear algebra, calculus, and machine learning examples

To initialize demo data, you can run a short Python script after activating the virtualenv:

```bash
python
```

```python
import asyncio
from backend.config import get_settings
from backend.utils.neo4j_client import Neo4jClient, init_demo_data

async def main():
    settings = get_settings()
    client = Neo4jClient(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    await init_demo_data(client)
    await client.close()

asyncio.run(main())
```

If Neo4j is not configured, the RAG layer will still work in a degraded mode and use a fallback context message.

---

## 5. Frontend setup (Vue 3 + Vite)

### 5.1. Install Node dependencies

From the `frontend/` directory:

```bash
cd frontend
npm install
```

### 5.2. Run the frontend dev server

```bash
npm run dev
```

By default, Vite runs at:

- `http://localhost:5173`

The frontend is configured to call the backend over:

- WebSocket: `ws://localhost:8000/ws/chat`

If you change ports or origins, update:

- `FRONTEND_ORIGIN` in `.env`  
- `WS_URL` in `frontend/src/utils/websocket.js`

---

## 6. WebSocket protocol

The chat UI communicates with the backend using a WebSocket endpoint:

- URL: `ws://localhost:8000/ws/chat`

### 6.1. Client → Server message

When the user sends a message, the frontend sends JSON:

```json
{
  "type": "user_message",
  "message_id": "9f2b54b0-cc4b-4a26-9b0a-5c1208f9b1c5",
  "content": "What is a derivative?",
  "conversation_id": "optional-conversation-id"
}
```

- `type` – always `"user_message"` for user messages  
- `message_id` – UUID or unique identifier for correlating responses  
- `content` – user’s question text  
- `conversation_id` – optional identifier for multi‑turn tracking (currently unused by the backend but kept for future extensions)

### 6.2. Server → Client streaming messages

The backend streams assistant responses as a sequence of chunks:

```json
{
  "type": "assistant_chunk",
  "message_id": "9f2b54b0-cc4b-4a26-9b0a-5c1208f9b1c5",
  "content": "A derivative measures how a function ",
  "is_final": false
}
```

The final chunk for a message has:

```json
{
  "type": "assistant_chunk",
  "message_id": "9f2b54b0-cc4b-4a26-9b0a-5c1208f9b1c5",
  "content": "",
  "is_final": true
}
```

- `type` – `"assistant_chunk"`  
- `message_id` – matches the originating user `message_id`  
- `content` – partial text for this chunk (may be empty for the final signal)  
- `is_final` – `false` for streaming chunks, `true` for the final chunk

The frontend (`ChatBox.vue`) aggregates chunks with the same `message_id` into a single assistant message and updates a typing indicator (`Assistant is typing…`) until the final chunk arrives.

---

## 7. RAG and DeepSeek behavior

The WebSocket handler (`backend/api/websocket_routes.py`) processes each `user_message` as follows:

1. Validate and parse the incoming JSON into a `UserMessage` model.  
2. Use `RAGService` (`backend/services/rag_service.py`) to:
   - Embed the query with `embed_text()` from `backend/utils/embedding_utils.py`.  
   - Fetch candidate `(topic, question, answer)` triples from Neo4j via `Neo4jClient.get_related_qa()`.  
   - Re‑rank candidates by cosine similarity and build a compact context string.  
3. Call `DeepSeekService.astream_chat()` with:
   - A system prompt describing the assistant’s role.  
   - A user content string that combines the RAG context and the user question.  
4. Stream the resulting text tokens back to the client as `assistant_chunk` messages.

If Neo4j is unavailable or misconfigured, the RAG layer logs a warning and uses a fallback context string. If DeepSeek returns an error, the backend sends a graceful error message to the client instead of crashing.

---

## 8. Development notes

- Python version: **3.11+**  
- Frontend stack: **Vue 3 + Vite + Tailwind CSS + marked**  
- Backend stack: **FastAPI + uvicorn + httpx + Neo4j driver + numpy + python‑dotenv**  
- Knowledge graph: **Neo4j** (with optional demo seeding via `init_demo_data`)  

For production, consider:

- Running uvicorn/gunicorn behind a reverse proxy.  
- Securing WebSocket and HTTP over HTTPS.  
- Using a managed Neo4j instance or hardened Docker deployment.  
- Implementing authentication and rate limiting as needed.

