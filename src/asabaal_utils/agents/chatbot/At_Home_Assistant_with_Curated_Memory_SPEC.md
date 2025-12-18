# At Home Assistant with Curated Memory
**Concept and Technical Specification**  
Generated: 2025-11-07 15:56:15

---

## Purpose

Create a local first assistant that you operate through a simple chat interface while keeping a separate memory manager that you control. The assistant can read memory but never writes to it. You add, edit, and remove memory through a dedicated panel. This separation gives you transparency, safety, and easy debugging.

---

## Goals

- Simple chat with your local model
- Human curated memory that the model can query
- Clean separation between chat and memory management
- Local first deployment with optional LAN access
- Clear prompts that include retrieved memory
- Fast iteration for dispatch and research workflows

---

## Non Goals

- Multi agent orchestration
- Automatic memory writing by the model
- Cloud services by default
- Complex analytics or visualization on day one

---

## User Stories

1. As a dispatcher I can open the chat, ask a question, and the assistant uses my saved facts to answer.
2. As a user I can add a new fact in the memory panel and see it appear immediately in search.
3. As a user I can update or delete a memory item and the change is reflected the next time I query.
4. As a user I can upload a file to index for later retrieval.
5. As a user I can export and import memory snapshots for backup.
6. As a user I can see which memory items were used to answer my question.

---

## High Level Architecture

```
[Browser]
  ├── Chat view
  └── Memory view
       ├── List, search, filter
       ├── Create, update, delete
       └── Import, export

[Backend API]
  ├── Chat service
  │     ├── Retrieval from memory
  │     ├── Prompt assembly
  │     └── Call to local model runner
  └── Memory service
        ├── CRUD for items
        ├── File ingestion pipeline
        └── Snapshot import and export

[AI Memory Engine]
  └── Cognee local instance
        ├── Vector store for semantic search
        └── Graph store for entities and relations

[Model Runtime]
  └── Local LLM through Ollama or LM Studio or text generation inference
```

---

## Technology Choices

- Frontend: React with Vite and TypeScript or a minimal HTMX template
- Backend: FastAPI
- Memory engine: Cognee local instance
- Vector store: LanceDB or FAISS for small setups
- Graph store: Kuzu or Memgraph or Neo4j community
- Embeddings: Local with BGE small or e5 small through text embedding inference or model served by Ollama
- Local model: Llama family or Mistral family using Ollama or LM Studio
- Auth: Local admin secret for write access to memory service
- Packaging: Docker compose for reproducible setup
- Storage: Local volumes for vector index, graph database, and uploads

---

## Data Model

### MemoryItem

| Field         | Type        | Notes                                                 |
|---------------|-------------|-------------------------------------------------------|
| id            | string      | UUID                                                  |
| title         | string      | Short human label                                     |
| content       | text        | Main text or extracted summary                        |
| source_type   | enum        | manual or file                                        |
| source_uri    | string      | path to file or external reference                    |
| tags          | array       | freeform strings                                      |
| created_at    | datetime    |                                                       |
| updated_at    | datetime    |                                                       |
| status        | enum        | active or archived                                    |
| provenance    | json        | chunking details and checksums                        |
| graph_nodes   | json        | entities and attributes created by Cognify phase      |
| graph_edges   | json        | relations created by Cognify phase                    |

### ChatTurn

| Field         | Type        | Notes                                                 |
|---------------|-------------|-------------------------------------------------------|
| id            | string      | UUID                                                  |
| ts            | datetime    |                                                       |
| user_text     | text        |                                                       |
| model_text    | text        |                                                       |
| memory_hits   | array       | list of MemoryItem ids and scores                     |
| prompt_meta   | json        | token counts and model parameters                      |

---

## Retrieval Strategy

1. Encode the user query with the embedding model.
2. Query vector store for top N chunks and aggregate back to MemoryItem level.
3. Optionally query the graph for entities and relations to enrich context.
4. Rerank candidates with a lightweight cross encoder or a rule based score.
5. Produce a compact context bundle with strict token budget.
6. Compose the final prompt and call the model.

**Scoring sketch**  
score = 0.6 similarity + 0.2 tag match + 0.2 freshness

**Context budget rule**  
- Max 1 K tokens of memory per answer for small local models
- Prefer exact matches on tags when present
- Never include two items that conflict without a conflict note

---

## Prompt Template

```
System
You are a local assistant. Use only retrieved memory and user input. If a fact is missing say so plainly.

Context
<top memory snippets in bullet form with titles and short quotes>

User
<user message>

Assistant
Provide a concise answer. If you used memory, list which items by title.
```

---

## API Design

Base path: /api

### Chat

- POST /chat/complete
  - body: { "message": str, "max_tokens": int, "temperature": float }
  - returns: { "text": str, "used_memory": [{ "id": str, "title": str, "score": float }] }

- GET /chat/turns?limit=50&cursor=...
  - returns recent turns

### Memory

- GET /memory/items?query=&tags=&status=active&limit=50&cursor=...
- POST /memory/items
  - body: { "title": str, "content": str, "tags": [str] }
- PUT /memory/items/{id}
  - body: partial update
- DELETE /memory/items/{id}
- POST /memory/import
  - multipart file upload for pdf or txt or md
- GET /memory/export
  - returns a zip with json lines and any attachments
- POST /memory/reindex/{id}
  - forces re ingestion

### Admin

- POST /admin/login returns a short lived token
- POST /admin/health checks dependencies and versions

---

## Ingestion Pipeline

1. Extract
   - Read file or manual text
   - Convert pdf and docx to text
   - Split into semantically coherent chunks
2. Cognify
   - Create embeddings
   - Run entity and relation extraction to produce nodes and edges
   - Generate a short summary for each chunk and for the item
3. Load
   - Write chunks to vector store
   - Write nodes and edges to graph store
   - Store provenance and checksums

**Chunking defaults**
- Target 500 tokens per chunk with 100 token overlap
- Merge tiny fragments to avoid noise
- Keep tables as preformatted blocks when possible

---

## Security and Privacy

- Local first deployment
- Memory write endpoints require an admin token
- All storage stays on local volumes
- Optional LAN access with TLS through Caddy reverse proxy
- No telemetry by default
- Clear data retention policy and easy wipe command

---

## Performance Guidelines

- Keep embedding model small for speed
- Limit top N vector hits to a small number like 8
- Cache embeddings for repeated queries
- Use streaming responses from the model
- Monitor token counts and latency in logs

---

## Observability

- Structured logs with request ids
- Per request metrics: latency, tokens, memory hits
- Simple dashboard page that shows recent queries and top memory items

---

## UX Notes

- Two tabs at the top: Chat and Memory
- Memory page has a left column for filters and a main list with titles and tags
- Each item expands to show content and provenance
- Add button opens a dialog with title and content and tags
- Result panel in chat shows which memory items were used

---

## Configuration

- MODEL_BACKEND values: ollama or lmstudio or tgi
- EMBEDDINGS_MODEL name or URL
- VECTOR_STORE_DIR local path
- GRAPH_BACKEND values: kuzu or memgraph or neo4j
- ADMIN_SECRET for write endpoints
- MAX_CONTEXT_TOKENS for memory bundle

---

## Minimal Docker Compose

```yaml
services:
  api:
    image: python:3.12-slim
    volumes:
      - ./app:/app
      - ./data:/data
    environment:
      - MODEL_BACKEND=ollama
      - EMBEDDINGS_MODEL=bge-small
      - VECTOR_STORE_DIR=/data/vector
      - GRAPH_BACKEND=kuzu
      - ADMIN_SECRET=change_me
    command: uvicorn app.main:app --host 0.0.0.0 --port 8080
    ports:
      - "8080:8080"

  kuzu:
    image: kuzudb/duckdb-kuzu:latest
    volumes:
      - ./data/kuzu:/var/lib/kuzu

  lancedb:
    image: lancedb/lancedb:latest
    volumes:
      - ./data/lancedb:/var/lib/lancedb

  frontend:
    image: node:22-alpine
    working_dir: /web
    volumes:
      - ./web:/web
    command: sh -c "npm ci && npm run build && npx serve -s dist -l 5173"
    ports:
      - "5173:5173"
```

This compose is a sketch. Replace images or bind mounts with your preferred setup.

---

## Test Plan

- Unit tests for memory CRUD and ingestion
- Integration tests for retrieval and prompt assembly
- Golden tests for known questions that must pull specific memory
- Load test for concurrent chat sessions with tiny models
- Security test to ensure memory write requires admin secret

---

## Rollout Plan

1. Local development with a toy model
2. Populate memory with a small seed set from dispatch facts
3. Run manual acceptance tests through realistic questions
4. Add export and import to protect your data
5. Harden auth and enable optional LAN access

---

## Roadmap Ideas

- Approval queue where the assistant can suggest a memory addition and you approve
- Memory diff and version history
- Graph view in the UI
- Voice input with local STT and TTS
- Per carrier memory spaces with switches in the chat view
- Simple rule engine for rate safety checks

---

## Implementation Notes for Cognee

- Use the Python SDK for extract, cognify, and load
- Configure LanceDB for vector indexing and Kuzu for graph storage
- Keep the ontology minimal to start
- Expose a memory search that returns both chunk text and graph linked facts
- Store provenance so you can trace every answer back to a source

---

## Risks and Mitigations

- Retrieval returns stale data  
  Mitigation: show item timestamps and prefer active items in scoring

- Conflicting facts  
  Mitigation: surface both and ask the user to resolve in the memory panel

- Local model quality varies  
  Mitigation: keep prompts short and focused and use reranking

- Storage growth  
  Mitigation: snapshots and archiving and pruning by tag and last accessed

---

## Acceptance Criteria

- Chat can answer questions that rely on at least one saved fact
- Memory CRUD works without restarting the service
- Used memory items are visible to the user for each answer
- All components run locally with docker compose

---

## Appendix A  Minimal API Shapes

```ts
// Memory item
type MemoryItem = {
  id: string
  title: string
  content: string
  tags: string[]
  status: "active" | "archived"
  created_at: string
  updated_at: string
  provenance?: Record<string, any>
}

// Chat completion response
type ChatResponse = {
  text: string
  used_memory: { id: string, title: string, score: number }[]
}
```

---

## Appendix B  Developer Setup

- Python 3.11 and Node 22
- Create a virtual environment and install FastAPI and Cognee
- Start Kuzu and LanceDB through docker compose
- Start the API and the frontend
- Populate memory with two or three seed items and run the smoke tests

---

## Appendix C  Memory Curation Guidelines

- Keep titles short and distinctive
- Tag by domain such as dispatch or finance or personal
- Write content as a single clear paragraph per item
- Update or archive outdated facts instead of editing in place if you want history
- Reindex after large edits

---

## References and Background Reading

- Cognee official site and documentation
- Cognee GitHub repository
- Blog articles on Graph RAG with Cognee
- Posts about Cognee integration with databases and embeddings
