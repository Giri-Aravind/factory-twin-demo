# Groq API Migration Guide

## Changes Made

All LLM agents have been migrated from **Ollama** to **Groq API**. All 9 agents now use `llama-3.3-70b-versatile` via Groq for every call.

---

## Updated Files

### Dependencies
- `backend/requirements.txt`: Replaced `ollama` with `groq`, added `sentence-transformers`

### Environment Config
- `backend/.env`:
  - Removed `OLLAMA_HOST`
  - Added `GROQ_API_KEY`
  - `PRIMARY_MODEL=llama-3.3-70b-versatile`
  - `LIGHTWEIGHT_MODEL=llama-3.1-8b-instant` (defined, available for future use)
  - `EMBEDDING_MODEL=all-MiniLM-L6-v2` (local sentence-transformers, no API needed)

### All 9 LLM Agents

| Agent | File | LLM Role |
|---|---|---|
| Intent Detector | `agents/intent_detector.py` | Classifies user intent into 6 categories |
| LLM Reranker | `agents/llm_reranker.py` | Picks best endpoint from vector search candidates |
| Endpoint Selector | `agents/endpoint_selector.py` | Calls reranker for both single and multi-endpoint paths |
| Query Decomposer | `agents/query_decomposer.py` | Breaks complex queries into multi-step plans |
| Parameter Extractor | `agents/parameter_extractor.py` | Extracts GraphQL parameters from user query |
| SQL Generator | `agents/sql_generator.py` | Resolves entity names to canonical DB names before UUID lookup |
| Entity Extractor | `agents/entity_extractor.py` | Extracts entities from GraphQL results for multi-step carry-forward |
| Plan Manager | `agents/plan_manager.py` | Generates natural step transition messages |
| Response Generator | `agents/response_generator.py` | Writes final natural language response from data summary |
| Supervisor | `agents/supervisor.py` | Handles follow-up rewriting and general chat |

### Embeddings (Local — No API)
- `backend/scripts/vectordb.py`: Uses `sentence-transformers` locally (`all-MiniLM-L6-v2`, 384-dim)
- Groq does not provide embedding models — local embeddings avoid any external dependency
- Vector DB must be repopulated if the embedding model changes

### Response Timing
- `backend/api/server.py`: Returns `response_time_ms` in every `/api/chat` response
- `frontend/src/App.jsx`: Displays response time as a `⏱ Xs` badge under each AI message

---

## Setup Instructions

### 1. Install Dependencies
```bash
pip install --upgrade -r backend/requirements.txt
```

### 2. Get Groq API Key
1. Sign up at https://console.groq.com
2. Create an API key from the dashboard
3. Add to `backend/.env`:
```env
GROQ_API_KEY=your_api_key_here
```

### 3. Populate Vector DB
Must be run once (and again if embedding model changes):
```bash
cd backend
python scripts/populate_vector_db.py
```

### 4. Run the App
```bash
# Backend
cd backend
uvicorn api.server:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

---

## Groq API Usage Pattern

Every agent follows this pattern:

```python
from groq import Groq
import os, json

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
resp = client.chat.completions.create(
    model=os.getenv("PRIMARY_MODEL", "llama-3.3-70b-versatile"),
    messages=[
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."},
    ],
    response_format={"type": "json_object"},
    temperature=0.0,
    max_tokens=512,
)
result = json.loads(resp.choices[0].message.content)
```

---

## Model Recommendations

| Model | Use case |
|---|---|
| `llama-3.3-70b-versatile` | All agents (current) — best reasoning and instruction-following |
| `llama-3.1-8b-instant` | Simpler agents (intent, rerank, params) — faster, lower latency |
| `llama-3.1-70b-versatile` | Alternative to 3.3 if unavailable |

To switch models, update `PRIMARY_MODEL` in `backend/.env` — no code changes needed.

---

## Troubleshooting

### `shapes (20,768) and (384,) not aligned`
Stale vector DB with wrong embedding dimensions. Stop the backend, delete and repopulate:
```bash
rmdir /s /q database\qdrant_data   # Windows
python backend/scripts/populate_vector_db.py
```

### `Storage folder already accessed by another instance`
Another process holds the Qdrant lock. Stop the backend server before running populate scripts.

### `GROQ_API_KEY not found`
Ensure `backend/.env` has `GROQ_API_KEY=your_key` and restart the server.

### `Model not found`
Check available models at https://console.groq.com — model names are case-sensitive.

### Rate limiting
Groq free tier has rate limits. Check quota at https://console.groq.com.

### `No data found for your query`
The GraphQL API returned empty data. Check:
1. VPN (WireGuard) is connected — API is at `http://10.1.10.184:9000/graphql`
2. Backend logs for `[GraphQL] EMPTY result — variables sent: {...}` to see what parameters were used

---

## Reverting to Ollama

1. `pip install ollama`
2. Revert `.env`: set `OLLAMA_HOST=http://localhost:11434`, update model names
3. Revert agent files to use `ollama.chat()` instead of `Groq()`

---

## Summary

- All 9 agents use Groq API with `llama-3.3-70b-versatile`
- Embeddings use local `sentence-transformers` (no external API)
- Response time is tracked and shown in the UI
- `LIGHTWEIGHT_MODEL` is available in `.env` for future per-agent model tuning
