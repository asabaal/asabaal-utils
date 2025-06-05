#!/bin/bash
# Abacus AI VM Setup Script for Claude Tool Bridge

set -e

echo "🔧 Setting up Claude Tool Bridge on Abacus AI VM..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/ubuntu/asabaal-utils"
REPO_URL="https://github.com/asabaal/asabaal-utils.git"
SERVICE_USER="ubuntu"

# Create project directory
echo -e "${YELLOW}📁 Creating project directory...${NC}"
sudo mkdir -p $PROJECT_DIR
sudo chown $SERVICE_USER:$SERVICE_USER $PROJECT_DIR

# Clone or update repository
cd $PROJECT_DIR
if [ -d ".git" ]; then
    echo -e "${YELLOW}📥 Updating repository...${NC}"
    git pull origin main
else
    echo -e "${YELLOW}📥 Cloning repository...${NC}"
    git clone $REPO_URL .
fi

# Install system dependencies
echo -e "${YELLOW}📦 Installing system dependencies...${NC}"
sudo apt update
sudo apt install -y python3-pip python3-venv nginx ffmpeg curl

# Setup Python environment
echo -e "${YELLOW}🐍 Setting up Python environment...${NC}"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# Create logs directory
mkdir -p logs

# Setup systemd services
echo -e "${YELLOW}⚙️ Setting up systemd services...${NC}"

# Claude Tool Bridge service
sudo tee /etc/systemd/system/claude-bridge.service > /dev/null << EOF
[Unit]
Description=Claude Tool Bridge
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR/tools
Environment=PATH=$PROJECT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/python claude_tool_bridge.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Converter API service
sudo tee /etc/systemd/system/converter-api.service > /dev/null << EOF
[Unit]
Description=Converter API
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR/tools
Environment=PATH=$PROJECT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/python converter_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Setup Nginx reverse proxy
echo -e "${YELLOW}🌐 Setting up Nginx reverse proxy...${NC}"
sudo tee /etc/nginx/sites-available/claude-tools > /dev/null << EOF
server {
    listen 80;
    server_name _;

    # Claude Bridge
    location /bridge/ {
        proxy_pass http://localhost:7000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Converter API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:7000/health;
    }

    # Default page
    location / {
        return 200 '{"message": "Claude Tool Bridge", "bridge": "/bridge/", "api": "/api/"}';
        add_header Content-Type application/json;
    }
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/claude-tools /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Start and enable services
echo -e "${YELLOW}🚀 Starting services...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable claude-bridge converter-api
sudo systemctl start claude-bridge converter-api

# Wait for services to start
echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
sleep 15

# Test services
echo -e "${YELLOW}🔍 Testing services...${NC}"
if curl -f http://localhost:7000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Claude Bridge is running${NC}"
else
    echo -e "${RED}❌ Claude Bridge failed to start${NC}"
    sudo systemctl status claude-bridge
fi

if curl -f http://localhost:8000/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Converter API is running${NC}"
else
    echo -e "${RED}❌ Converter API failed to start${NC}"
    sudo systemctl status converter-api
fi

# Get public IP
PUBLIC_IP=$(curl -s http://checkip.amazonaws.com/ || echo "unknown")

echo -e "${GREEN}🎉 Setup complete!${NC}"
echo -e "${GREEN}📍 Public IP: $PUBLIC_IP${NC}"
echo -e "${GREEN}🌐 Claude Bridge: http://$PUBLIC_IP/bridge/${NC}"
echo -e "${GREEN}🔧 Converter API: http://$PUBLIC_IP/api/${NC}"
echo -e "${GREEN}💚 Health Check: http://$PUBLIC_IP/health${NC}"

echo -e "${YELLOW}📝 Service Management:${NC}"
echo "  • View bridge logs: sudo journalctl -u claude-bridge -f"
echo "  • View API logs: sudo journalctl -u converter-api -f"
echo "  • Restart bridge: sudo systemctl restart claude-bridge"
echo "  • Restart API: sudo systemctl restart converter-api"