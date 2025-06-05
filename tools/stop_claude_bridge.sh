#!/bin/bash
# description: Stops the Claude Tool Integration system
# version: 1.0.0
# category: integration

echo "🛑 Stopping Claude Tool Integration System..."
echo "============================================="

# Function to stop a service
stop_service() {
    local name=$1
    local port=$2
    local pid_file="/tmp/claude_bridge_$(echo $name | tr '[:upper:]' '[:lower:]' | tr ' ' '_')_pid"
    
    echo "⏹️  Stopping $name..."
    
    # Try to stop by PID file first
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill $pid 2>/dev/null; then
            echo "✅ $name stopped (PID: $pid)"
            rm -f "$pid_file"
            return 0
        fi
    fi
    
    # Try to stop by port
    local pids=$(lsof -ti:$port 2>/dev/null)
    if [ -n "$pids" ]; then
        echo $pids | xargs kill 2>/dev/null
        echo "✅ $name stopped (port $port)"
        rm -f "$pid_file"
        return 0
    fi
    
    echo "ℹ️  $name was not running"
    rm -f "$pid_file"
}

# Stop services
stop_service "Claude Bridge" 7000
stop_service "Converter API" 8000

# Clean up any remaining Python processes
echo "🧹 Cleaning up..."
pkill -f "claude_tool_bridge.py" 2>/dev/null
pkill -f "converter_api.py" 2>/dev/null

echo ""
echo "✅ Claude Tool Integration System stopped!"
echo "🔄 Use ./start_claude_bridge.sh to restart"