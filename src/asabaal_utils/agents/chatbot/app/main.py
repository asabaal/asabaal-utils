import os, uuid
import ollama
from datetime import datetime
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from .schemas import ChatRequest, ChatResponse, UsedMemory, MemoryItem, MemoryCreate, MemoryUpdate, ChatTurn
from . import memory as mem
from . import ollama_utils

ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "change_me")

app = FastAPI(title="Assistant with Curated Memory — Starter")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory chat history (for demo)
_CHAT_TURNS: List[ChatTurn] = []

def require_admin(secret: Optional[str] = None):
    if secret is None or secret != ADMIN_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.post("/api/chat/complete", response_model=ChatResponse)
async def chat_complete(req: ChatRequest):
    # Retrieve memory using Cognee
    hits: List[UsedMemory] = await mem.cognee_retrieval(req.message, top_k=5)

    # Generate response with Ollama
    try:
        text = ollama_utils.generate_response(req.message, hits, req.model)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    turn = ChatTurn(
        id=str(uuid.uuid4()),
        ts=datetime.utcnow(),
        user_text=req.message,
        model_text=text,
        memory_hits=hits,
        prompt_meta={
            "max_tokens": req.max_tokens, 
            "temperature": req.temperature,
            "model": req.model or os.environ.get("OLLAMA_DEFAULT_MODEL", "qwen3:30b")
        },
    )
    _CHAT_TURNS.append(turn)

    return ChatResponse(text=text, used_memory=hits)

@app.get("/api/chat/turns", response_model=List[ChatTurn])
def list_turns(limit: int = 50):
    return _CHAT_TURNS[-limit:]

# Memory endpoints
@app.get("/api/memory/items", response_model=List[MemoryItem])
def get_items(query: str = "", tags: str = "", status: str = "active", limit: int = 50):
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    return mem.list_items(query=query, tags=tag_list, status=status, limit=limit)

@app.post("/api/memory/items", response_model=MemoryItem)
async def post_item(payload: MemoryCreate):
    return mem.create_item(payload)

@app.put("/api/memory/items/{item_id}", response_model=MemoryItem)
def put_item(item_id: str, payload: MemoryUpdate):
    updated = mem.update_item(item_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Not found")
    return updated

@app.delete("/api/memory/items/{item_id}")
def del_item(item_id: str, admin_secret: Optional[str] = Body(None, embed=True)):
    require_admin(admin_secret)
    ok = mem.delete_item(item_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Not found")
    return {"ok": True}

@app.post("/api/memory/import")
async def import_file(file: UploadFile = File(...)):
    # Minimal import: read text files and create a MemoryItem per file
    content = await file.read()
    try:
        text = content.decode("utf-8", errors="replace")
    except Exception:
        raise HTTPException(400, "Only text-like files supported in the stub importer.")
    item = mem.create_item(payload=MemoryCreate(title=file.filename or "imported_file", content=text, tags=["import"]))
    return {"ok": True, "item": item}

@app.get("/api/memory/export")
def export_items():
    items = mem.list_items(status="active", limit=10000)
    return {"count": len(items), "items": [i.model_dump() for i in items]}

# Admin health
@app.post("/api/admin/health")
def health():
    return {
        "status": "ok",
        "version": "0.1.0-starter",
        "memory_store_path": os.environ.get("MEMORY_JSON_PATH", "data/memory.json"),
    }

@app.get("/api/models")
def list_models():
    """List available Ollama models"""
    return {"models": ollama_utils.get_available_models()}
