# Chatbot with Curated Memory - Setup Instructions

## Quick Start Guide

### Prerequisites
- Python 3.11+ 
- Node.js 18+
- Ollama installed and running (optional for full functionality)

### Step 1: Backend Setup

1. **Navigate to chatbot directory:**
```bash
cd /home/asabaal/repos/asabaal-utils/src/asabaal_utils/agents/chatbot
```

2. **Create Python virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set environment variables:**
```bash
export ADMIN_SECRET=change_me
export OLLAMA_DEFAULT_MODEL=qwen3:30b
export OLLAMA_HOST=http://localhost:11434
```

5. **Start the backend server:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

The backend will be available at: http://localhost:8080
API documentation: http://localhost:8080/docs

### Step 2: Frontend Setup

1. **Navigate to frontend directory (in a new terminal):**
```bash
cd /home/asabaal/repos/asabaal-utils/src/asabaal_utils/agents/chatbot/frontend
```

2. **Install Node.js dependencies:**
```bash
npm install
```

3. **Start the frontend development server:**
```bash
npm run dev
```

The frontend will be available at: http://localhost:5173

### Step 3: Using the Chatbot

1. **Open your browser** and go to http://localhost:5173
2. **Chat Tab**: Talk with your AI assistant
3. **Memory Tab**: Manage your knowledge base

## Features

### Chat Interface
- Real-time conversation with AI
- Shows which memory items were used in responses
- Model selection dropdown
- Message history

### Memory Management
- Add, edit, delete memory items
- Search and filter memories
- Tag-based organization
- Import/export functionality
- File upload support

## Optional: Ollama Integration

For full AI functionality, install and run Ollama:

1. **Install Ollama:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

2. **Pull a model:**
```bash
ollama pull qwen2.5:7b  # or any other model
```

3. **Start Ollama:**
```bash
ollama serve
```

4. **Update environment variable:**
```bash
export OLLAMA_DEFAULT_MODEL=qwen2.5:7b
```

## Troubleshooting

### Frontend Issues
- **OpaqueResponseBlocking**: Ensure backend is running on port 8080
- **CORS errors**: Check that both services are running
- **Build errors**: Run `npm install` to update dependencies

### Backend Issues
- **Import errors**: Activate virtual environment and install requirements
- **Cognee errors**: The app works without Cognee - it will use keyword search fallback
- **Ollama errors**: The app works without Ollama - you'll see placeholder responses

### Port Conflicts
- Backend uses port 8080
- Frontend uses port 5173
- Change ports if needed in the startup commands

## Development Notes

- Frontend proxies API calls to backend automatically
- Memory data is stored in `data/memory.json`
- Chat history is stored in memory (lost on restart)
- All components are responsive and work on mobile

## Next Steps

1. Add some memory items in the Memory tab
2. Try asking questions in the Chat tab
3. Experiment with import/export features
4. Customize the interface as needed