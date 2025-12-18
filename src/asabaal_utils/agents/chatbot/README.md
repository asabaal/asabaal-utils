# Assistant + Curated Memory — Starter Scaffold

This is a minimal FastAPI backend that matches the API shapes in the spec:

- `/api/chat/complete` (stubbed)
- `/api/chat/turns`
- `/api/memory/items` (CRUD)
- `/api/memory/import` and `/api/memory/export` (basic stubs)
- `/api/admin/health`

It ships with an in-memory search and a tiny JSON file store (`data/memory.json`)
so you can test the flow before wiring to Cognee.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run
export ADMIN_SECRET=change_me
uvicorn app.main:app --reload --port 8080
```

Open: http://localhost:8080/docs

## Notes

- Chat endpoint **does not** call a local LLM yet. It echoes and shows which memory items would be used.
- Memory CRUD writes to `data/memory.json` so your edits persist across restarts.
- Replace `stub_retrieval` with your Cognee search client to make it real.
- Add authentication for write routes if exposing beyond localhost.
