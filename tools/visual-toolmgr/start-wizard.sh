#!/bin/bash
# description: Starts the Visual Tool Manager web interface
# version: 1.0.0
# category: utility

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
VENV_DIR="$SCRIPT_DIR/venv"

echo "🚀 Starting Visual Tool Manager..."

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r "$BACKEND_DIR/requirements.txt" > /dev/null 2>&1

# Check if toolmgr exists
TOOLMGR_PATH="$(dirname "$SCRIPT_DIR")/toolmgr"
if [ ! -f "$TOOLMGR_PATH" ]; then
    echo "❌ Error: toolmgr not found at $TOOLMGR_PATH"
    echo "Please ensure toolmgr is in the correct location."
    exit 1
fi

echo "✅ Tool manager found at: $TOOLMGR_PATH"

# Start the Flask application
echo "🌐 Starting web server..."
echo "📍 Open your browser to: http://localhost:5000"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

cd "$BACKEND_DIR"
python app.py