# Chatbot with Curated Memory - Usage Guide

## Quick Start

### 1. Start the Server
```bash
cd /home/asabaal/repos/asabaal-utils/src/asabaal_utils/agents/chatbot
uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
```

### 2. Access Interactive Docs
- **Swagger UI**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc

## Adding Memories (No Admin Required!)

### Simple Memory Addition
```bash
curl -X POST "http://localhost:8002/api/memory/items" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Your Topic",
    "content": "Detailed information about your topic...",
    "tags": ["tag1", "tag2"]
  }'
```

### Example: Add Programming Knowledge
```bash
curl -X POST "http://localhost:8002/api/memory/items" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "JavaScript Fundamentals",
    "content": "JavaScript is a dynamic programming language primarily used for web development. It supports object-oriented, imperative, and functional programming styles.",
    "tags": ["javascript", "programming", "web"]
  }'
```

## Chat with the Assistant

### Ask Questions
```bash
curl -X POST "http://localhost:8002/api/chat/complete" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is JavaScript used for?"}'
```

The assistant will automatically find relevant memories and use them as context!

## List All Memories
```bash
curl "http://localhost:8002/api/memory/items"
```

## Search Memories
```bash
curl "http://localhost:8002/api/memory/items?query=javascript&tags=programming"
```

## Update Memories
```bash
curl -X PUT "http://localhost:8002/api/memory/items/{memory_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Title",
    "content": "Updated content...",
    "tags": ["new", "tags"]
  }'
```

## Import from Files
```bash
curl -X POST "http://localhost:8002/api/memory/import" \
  -F "file=@your_text_file.txt"
```

## Key Features

✅ **Open Memory Addition** - Anyone can add memories without admin permissions  
✅ **Semantic Search** - Finds memories based on meaning, not just keywords  
✅ **Automatic Indexing** - Memories are automatically processed by Cognee  
✅ **Context-Aware Chat** - Responses include relevant memories  
✅ **Simple API** - RESTful endpoints for easy integration  

## How It Works

1. **Add Memories**: Use POST to add knowledge to the memory store
2. **Automatic Processing**: Cognee indexes memories for semantic search
3. **Chat**: Ask questions and get responses with relevant memory context
4. **Manage**: List, search, and update memories as needed

The system combines Ollama's language models with Cognee's semantic search to create an intelligent assistant that learns from your curated knowledge!