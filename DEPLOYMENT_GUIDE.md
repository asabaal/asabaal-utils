# 🚀 **Deployment Guide: Claude Tool Bridge**
*Get your tools accessible to Claude anywhere*

---

## 🎯 **Deployment Options**

### **Option 1: Abacus AI VM** (Recommended for Production)
```bash
# 1. Copy setup script to your VM
scp deploy-scripts/abacus-vm-setup.sh ubuntu@your-vm-ip:~/

# 2. SSH into your VM and run setup
ssh ubuntu@your-vm-ip
chmod +x abacus-vm-setup.sh
./abacus-vm-setup.sh

# 3. Your tools are now available at:
# http://your-vm-ip/bridge/  (Claude Tool Bridge)
# http://your-vm-ip/api/     (Converter API)
```

**Why Abacus AI VM?**
- ✅ Always-on availability for Claude
- ✅ Public IP address accessible from browser chat
- ✅ Nginx reverse proxy with health monitoring
- ✅ Systemd services for auto-restart
- ✅ Full tool ecosystem with GPU access

---

### **Option 2: GitHub Codespaces** (Quick Testing)
```bash
# 1. Create a Codespace from your repository
# 2. Run the quick deploy script
./deploy-scripts/quick-deploy.sh

# 3. Your tools will be auto-forwarded
# GitHub will provide public URLs like:
# https://username-repo-7000.preview.app.github.dev
```

**Why GitHub Codespaces?**
- ✅ Zero setup required
- ✅ Automatic port forwarding
- ✅ Free tier available
- ❌ Limited to 120 hours/month (free)
- ❌ Not persistent beyond session

---

### **Option 3: Docker Deployment** (Any Cloud)
```bash
# Build and deploy
docker build -t claude-tools .
docker run -d -p 7000:7000 -p 8000:8000 --name claude-bridge claude-tools

# Deploy to any cloud:
# - Google Cloud Run
# - AWS ECS
# - DigitalOcean Apps
# - Railway
```

---

## 🔧 **Setup Secrets for GitHub Actions**

### **For Abacus AI VM Deployment:**
In your GitHub repository settings → Secrets and variables → Actions:

```bash
# Required secrets:
ABACUS_VM_HOST=your-vm-ip-address
ABACUS_VM_USER=ubuntu
ABACUS_VM_SSH_KEY=your-private-ssh-key
```

### **Generate SSH Key for VM:**
```bash
# On your local machine:
ssh-keygen -t ed25519 -C "github-actions@asabaal-utils"

# Copy public key to VM:
ssh-copy-id -i ~/.ssh/id_ed25519.pub ubuntu@your-vm-ip

# Add private key to GitHub secrets as ABACUS_VM_SSH_KEY
cat ~/.ssh/id_ed25519
```

---

## 🌐 **Using with Claude Browser Chat**

### **Once Deployed, Tell Claude:**
```
Hi Claude! I've deployed my tool bridge to a public server. 
You can access my 40+ development tools at:

🌉 Tool Bridge: http://your-vm-ip/bridge/
🔧 Converter API: http://your-vm-ip/api/

Available tools:
- Document analyzer (text analysis, readability)
- Format converter (CSV↔JSON, Markdown↔HTML)
- Video processing tools (CapCut analysis)
- 21 CLI utilities
- 16 Python scripts

Please test the connection and let me know what tools you can access!
```

---

## 📊 **Monitoring & Maintenance**

### **Check Service Status:**
```bash
# On VM:
sudo systemctl status claude-bridge converter-api
curl http://localhost:7000/health
```

### **View Logs:**
```bash
# Real-time logs:
sudo journalctl -u claude-bridge -f
sudo journalctl -u converter-api -f

# Service management:
sudo systemctl restart claude-bridge
sudo systemctl restart converter-api
```

### **Update Deployment:**
```bash
# Trigger GitHub Action manually, or:
git push origin main  # Auto-deploys via GitHub Actions
```

---

## 🎪 **Success Indicators**

### **✅ Deployment Successful When:**
1. Health check returns 200: `curl http://your-vm-ip/health`
2. Tools list accessible: `curl http://your-vm-ip/bridge/tools`
3. Converter API responds: `curl http://your-vm-ip/api/`
4. Claude can make requests from browser chat

### **🔍 Test with Claude:**
```
POST http://your-vm-ip/bridge/execute
{
  "tool_name": "document_analyzer",
  "parameters": {"content": "Hello world test"}
}
```

---

## 💡 **Pro Tips**

1. **Use Abacus AI VM** for persistent, always-on access
2. **GitHub Actions** automatically deploy on code changes
3. **Health monitoring** ensures Claude gets reliable access
4. **Nginx proxy** provides clean URLs and load balancing
5. **Systemd services** auto-restart if tools crash

Your tools are now accessible to Claude from anywhere! 🎉