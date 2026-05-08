# FactoryTwin AI

A multi-agent AI assistant for manufacturing analytics — demand planning, supply chain, material shortages, and purchase orders.

## Architecture

- **Frontend**: React + Vite (`frontend/`)
- **Backend**: FastAPI + LangGraph (`backend/`)
- **LLM**: Groq API (`llama-3.3-70b-versatile`) — all 9 agents
- **Vector DB**: Qdrant (local file-based) — endpoint selection
- **Embeddings**: `sentence-transformers` (local, no API needed)
- **Databases**: PostgreSQL — manufacturing data + chat history

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (two databases: manufacturing data + chat history)
- WireGuard VPN (to reach the GraphQL backend at `10.1.10.184`)
- Groq API key — get one free at https://console.groq.com

---

## First-Time Setup

### 1. Clone and navigate

```bash
cd factorytwin-ai
```

### 2. Backend — install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `backend/.env` and fill in:

```env
GROQ_API_KEY=your_groq_api_key_here

# PostgreSQL — manufacturing data
FACTORYTWIN_DB_HOST=localhost
FACTORYTWIN_DB_PORT=5432
FACTORYTWIN_DB_NAME=project
FACTORYTWIN_DB_USER=postgres
FACTORYTWIN_DB_PASSWORD=your_password

# PostgreSQL — chat history
CHAT_DB_HOST=localhost
CHAT_DB_PORT=5432
CHAT_DB_NAME=factorytwin_chat
CHAT_DB_USER=postgres
CHAT_DB_PASSWORD=your_password
```

### 4. Set up databases

```bash
cd backend
python scripts/setup_db.py
```

### 5. Populate the vector DB (one-time only)

```bash
cd backend
python scripts/populate_vector_db.py
```

> Only needs to be re-run if you add/change endpoints or change `EMBEDDING_MODEL`.

### 6. Frontend — install dependencies

```bash
cd frontend
npm install
```

---

## Running the App

Start both servers in separate terminals:

**Backend:**
```bash
cd backend
uvicorn api.server:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

Open http://localhost:5173 in your browser.

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `GROQ_API_KEY` | Groq API key (required) | — |
| `PRIMARY_MODEL` | LLM model for all agents | `llama-3.3-70b-versatile` |
| `LIGHTWEIGHT_MODEL` | Available for future per-agent tuning | `llama-3.1-8b-instant` |
| `EMBEDDING_MODEL` | Local sentence-transformers model | `all-MiniLM-L6-v2` |
| `FACTORYTWIN_GRAPHQL_URL` | GraphQL API endpoint (requires VPN) | `http://10.1.10.184:9000/graphql` |
| `FACTORYTWIN_DB_*` | Manufacturing PostgreSQL connection | — |
| `CHAT_DB_*` | Chat history PostgreSQL connection | — |
| `QDRANT_PATH` | Qdrant vector DB storage path | `../database/qdrant_data` |
| `CONTEXT_WINDOW_MESSAGES` | Conversation history window | `10` |

---

## Agent Overview

All 9 agents use `llama-3.3-70b-versatile` via Groq API:

| Agent | Role |
|---|---|
| Intent Detector | Classifies user query intent |
| LLM Reranker | Picks best endpoint from candidates |
| Endpoint Selector | Vector search + reranking |
| Query Decomposer | Breaks complex queries into steps |
| Parameter Extractor | Extracts GraphQL parameters |
| SQL Generator | Resolves entity names to DB UUIDs |
| Entity Extractor | Extracts entities for multi-step plans |
| Plan Manager | Manages multi-step plan progression |
| Response Generator | Writes final natural language response |

---

## Troubleshooting

**`shapes not aligned: 768 != 384`**
Vector DB has stale embeddings. Stop the backend, then:
```bash
rmdir /s /q database\qdrant_data
cd backend && python scripts/populate_vector_db.py
```

**`Storage folder already accessed by another instance`**
Stop the backend before running populate scripts — Qdrant allows only one process at a time.

**`No data found for your query`**
- Check WireGuard VPN is connected
- Check backend logs for `[GraphQL] EMPTY result — variables sent: {...}`

**`GROQ_API_KEY not found`**
Ensure `backend/.env` has the key set and restart the server.

**Rate limiting**
Groq free tier has rate limits. Check usage at https://console.groq.com.

---

## Project Structure

```
factorytwin-ai/
├── backend/
│   ├── agents/          # All 9 LLM agents
│   ├── api/             # FastAPI server
│   ├── data/            # Endpoint description text files
│   ├── database/        # Qdrant vector DB storage
│   ├── schema/          # Endpoint schemas and prompts
│   ├── scripts/         # DB setup, vector DB, utilities
│   ├── main.py          # Query processing entry point
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   └── App.jsx      # React UI
│   └── package.json
├── GROQ_MIGRATION.md    # Groq migration details
└── README.md
```
