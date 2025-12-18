from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict
from datetime import datetime

class MemoryItem(BaseModel):
    id: str
    title: str
    content: str
    tags: List[str] = []
    status: Literal["active", "archived"] = "active"
    created_at: datetime
    updated_at: datetime
    provenance: Optional[Dict] = None
    source_type: Literal["user_provided", "chatbot_response", "system_knowledge"] = "user_provided"

class MemoryCreate(BaseModel):
    title: str
    content: str
    tags: List[str] = []
    source_type: Literal["user_provided", "chatbot_response", "system_knowledge"] = "user_provided"

class MemoryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[Literal["active", "archived"]] = None

class UsedMemory(BaseModel):
    id: str
    title: str
    score: float
    source_type: Optional[Literal["user_provided", "chatbot_response", "system_knowledge"]] = None
    tags: List[str] = []

class ChatRequest(BaseModel):
    message: str
    max_tokens: int = 512
    model: Optional[str] = None
    temperature: float = 0.2

class ChatResponse(BaseModel):
    text: str
    used_memory: List[UsedMemory] = []

class ChatTurn(BaseModel):
    id: str
    ts: datetime
    user_text: str
    model_text: str
    memory_hits: List[UsedMemory] = []
    prompt_meta: dict = Field(default_factory=dict)
