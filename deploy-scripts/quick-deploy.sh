#!/bin/bash
# Quick deployment script for Claude Tool Bridge

echo "🚀 Claude Tool Bridge - Quick Deploy"
echo "======================================"

# Detect platform
if command -v docker &> /dev/null; then
    PLATFORM="docker"
elif [[ "$HOSTNAME" == *"github"* ]] || [[ "$CODESPACE_NAME" != "" ]]; then
    PLATFORM="github"
elif [[ "$1" == "vm" ]] || [[ "$SSH_CONNECTION" != "" ]]; then
    PLATFORM="vm"
else
    PLATFORM="local"
fi

echo "📍 Detected platform: $PLATFORM"

case $PLATFORM in
    "docker")
        echo "🐳 Deploying with Docker..."
        docker build -t claude-tools .
        docker run -d -p 7000:7000 -p 8000:8000 --name claude-bridge claude-tools
        echo "✅ Docker deployment complete!"
        echo "🌐 Access at: http://localhost:7000"
        ;;
        
    "github")
        echo "🐙 Deploying on GitHub Codespaces..."
        pip install -r requirements.txt
        pip install -e .
        cd tools
        python converter_api.py &
        python claude_tool_bridge.py &
        echo "✅ GitHub deployment complete!"
        echo "🌐 Bridge will be forwarded automatically"
        ;;
        
    "vm")
        echo "☁️ Deploying on VM..."
        if [[ -f "deploy-scripts/abacus-vm-setup.sh" ]]; then
            bash deploy-scripts/abacus-vm-setup.sh
        else
            echo "❌ VM setup script not found"
            exit 1
        fi
        ;;
        
    "local")
        echo "💻 Local development deployment..."
        pip install -r requirements.txt
        pip install -e .
        cd tools
        echo "🔧 Starting converter API..."
        python converter_api.py &
        echo "🌉 Starting Claude bridge..."
        python claude_tool_bridge.py
        ;;
esac