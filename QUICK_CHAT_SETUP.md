# 🚀 **Quick Chat Setup Card**
*Keep this handy for instant Claude tool access!*

---

## ⚡ **30-Second Setup**

### **1. Start Bridge (Terminal)**
```bash
cd ~/asabaal_ventures/repos/asabaal-utils
./tools/claude-tools start
```
**Wait for:** `🎉 Claude Tool Integration System is READY!`

### **2. Quick Test**
```bash
./tools/claude-tools demo
```
**Expect:** Document analysis + format conversion demos

### **3. Go to Chat**
- Open `claude.ai` (regular chat)
- Start new conversation

### **4. Copy-Paste This to Claude:**
```
Hi Claude! I have a tool integration bridge running locally that gives you access to my tools.

BRIDGE URL: http://localhost:7000
STATUS: Running (39 tools available)

Tools include document analyzer, format converter, CLI tools, and more. Can you connect and help me use these tools?
```

---

## 🎯 **Instant Commands**

| **Need** | **Terminal Command** | **Result** |
|----------|---------------------|------------|
| Start everything | `./tools/claude-tools start` | Bridge + API running |
| Test it works | `./tools/claude-tools demo` | Live demonstration |
| List all tools | `./tools/claude-tools tools` | 39 tools categorized |
| Check health | `./tools/claude-tools health` | System status |
| Stop everything | `./tools/claude-tools stop` | Clean shutdown |

---

## 💬 **Chat Examples**

**Analyze Text:**
> "Analyze this document for readability and patterns: [your text]"

**Convert Formats:**  
> "Convert this CSV to JSON: name,age\nJohn,25\nJane,30"

**Chain Operations:**
> "First analyze this data, then convert CSV to JSON, then analyze the JSON"

**Use CLI Tools:**
> "Run my system-info tool and show the results"

---

## 🔧 **Troubleshooting**

**Bridge not responding?**
```bash
./tools/claude-tools stop
./tools/claude-tools start
```

**Tools missing?**
```bash
./tools/claude-tools tools
```

**Need help?**
```bash
./tools/claude-tools
```

---

## ✅ **Success Checklist**

- [ ] Bridge shows "READY!" message
- [ ] Demo runs successfully  
- [ ] Claude can connect in chat
- [ ] Tools execute in <100ms
- [ ] 39 tools discovered

**🎉 Ready for AI-powered workflows!**