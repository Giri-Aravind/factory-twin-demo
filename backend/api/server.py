"""FastAPI server."""
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from main import main
from scripts.chatdb import chatdb

app = FastAPI(title="FactoryTwin AI", version="5.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "5.0.0"}


@app.post("/api/chat")
async def chat(req: ChatRequest):
    try:
        t0 = time.perf_counter()
        result = main.process_query(req.query, req.conversation_id)
        result["response_time_ms"] = round((time.perf_counter() - t0) * 1000)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/conversations")
async def create_conv():
    return {"conversation_id": chatdb.create_conversation()}


@app.get("/api/conversations")
async def list_convs():
    return {"conversations": chatdb.get_conversations()}


@app.get("/api/conversations/{cid}")
async def get_conv(cid: str):
    return {"conversation_id": cid, "messages": chatdb.get_messages(cid)}


@app.delete("/api/conversations/{cid}")
async def delete_conv(cid: str):
    chatdb.delete_conversation(cid)
    return {"deleted": True}
