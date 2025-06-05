#!/bin/bash
# description: Starts the complete Claude Tool Integration system
# version: 1.0.0
# category: integration

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Claude Tool Integration System..."
echo "=============================================="
echo "📁 Working directory: $SCRIPT_DIR"

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to start a service in background
start_service() {
    local name=$1
    local script=$2
    local port=$3
    
    echo "🔧 Starting $name..."
    
    if check_port $port; then
        echo "⚠️  $name already running on port $port"
    else
        python $script &
        local pid=$!
        echo "✅ $name started (PID: $pid) on port $port"
        echo $pid > "/tmp/claude_bridge_$(echo $name | tr '[:upper:]' '[:lower:]' | tr ' ' '_')_pid"
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local name=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s $url > /dev/null 2>&1; then
            echo "✅ $name is ready!"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
        printf "."
    done
    
    echo ""
    echo "❌ $name failed to start after ${max_attempts}s"
    return 1
}

# Check dependencies
echo "🔍 Checking dependencies..."
python -c "import fastapi, uvicorn, requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing dependencies. Installing..."
    pip install fastapi uvicorn requests
fi

# Start the converter API (if not already running)
start_service "Converter API" "converter_api.py" 8000

# Wait for converter API to be ready
if wait_for_service "Converter API" "http://localhost:8000"; then
    echo "🔌 Converter API ready at http://localhost:8000"
    echo "📚 API docs at http://localhost:8000/docs"
else
    echo "⚠️  Converter API may not be fully ready"
fi

echo ""

# Start the Claude Tool Bridge
start_service "Claude Bridge" "claude_tool_bridge.py" 7000

# Wait for bridge to be ready
if wait_for_service "Claude Bridge" "http://localhost:7000"; then
    echo "🌉 Claude Bridge ready at http://localhost:7000"
    echo "🔗 Tool schema at http://localhost:7000/claude/tools.json"
else
    echo "❌ Claude Bridge failed to start"
    exit 1
fi

echo ""
echo "🎉 Claude Tool Integration System is READY!"
echo "============================================="
echo ""
echo "🔧 Available Services:"
echo "   🛠️  Converter API:    http://localhost:8000"
echo "   🌉 Claude Bridge:     http://localhost:7000"
echo "   📋 Tool List:         http://localhost:7000/tools"
echo "   🏥 Health Check:      http://localhost:7000/health"
echo ""
echo "🧪 Quick Tests:"
echo "   curl http://localhost:7000/tools"
echo "   curl http://localhost:8000/tools/test/converter"
echo "   python tools/claude_client.py"
echo ""
echo "🛑 To stop all services:"
echo "   ./stop_claude_bridge.sh"
echo ""
echo "✨ Claude can now access all your tools through the bridge!"