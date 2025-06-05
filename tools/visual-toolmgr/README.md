# 🔧 Visual Tool Manager

A user-friendly web interface for the command-line tool manager (`toolmgr`). Perfect for non-technical users who want to easily install and manage command-line tools without touching the terminal.

## ✨ Features

- **🌐 Web-based Interface**: No command line knowledge required
- **📂 Directory Browser**: Navigate your filesystem visually  
- **🔍 Tool Discovery**: Automatically detects tools in directories
- **📦 One-Click Installation**: Install tools with a single click
- **📋 Tool Management**: View, update, and remove installed tools
- **🏥 Health Monitoring**: Check the status of installed tools
- **📱 Responsive Design**: Works on desktop and mobile

## 🚀 Quick Start

1. **Start the Visual Wizard**:
   ```bash
   ./tools/visual-toolmgr/start-wizard.sh
   ```

2. **Open Your Browser**:
   Navigate to `http://localhost:5000`

3. **Start Installing Tools**:
   - Browse to a directory containing tools
   - Click "Scan" to discover available tools
   - Click "Install All" or install individual tools

## 🎯 Test Tools Included

The wizard comes with 5 sample tools for testing:

- **📁 file-organizer**: Organizes files by type into subdirectories
- **💾 quick-backup**: Creates timestamped backups of files/directories  
- **🖥️ system-info**: Displays system information and resource usage
- **📊 text-counter**: Counts lines, words, and characters in text files
- **🌐 port-checker**: Checks if network ports are open

## 📖 How to Use

### 🔍 Browse & Install Tab
1. **Select a Directory**: Choose from common directories or enter a custom path
2. **Browse Filesystem**: Click directories to navigate through your system
3. **Scan for Tools**: Click "Scan Current Directory" to find tools
4. **Review Found Tools**: See tool details like name, version, category, description
5. **Install Tools**: Use "Install All" or install individual tools
   - Check "Force overwrite" to replace existing tools

### 📋 Installed Tools Tab
- **View Installed Tools**: See all tools currently installed
- **Tool Status**: Check if tools are working properly (✅/❌)
- **Tool Information**: View details about each installed tool

### 🏥 Health Check Tab
- **System Health**: Check the status of all installed tools
- **Setup Tool Manager**: Initialize the tool manager environment
- **Diagnostics**: Identify broken or missing tools

## 🛠️ Architecture

```
visual-toolmgr/
├── backend/
│   ├── app.py              # Flask API server
│   ├── requirements.txt    # Python dependencies
│   └── static/
│       ├── index.html      # Main interface
│       ├── style.css       # Styling
│       └── app.js          # Frontend logic
├── test-tools/             # Sample tools for testing
├── start-wizard.sh         # Startup script
└── README.md              # This file
```

## 🔧 API Endpoints

The backend provides these REST API endpoints:

- `GET /api/directories` - List common tool directories
- `GET /api/browse?path=<path>` - Browse filesystem  
- `GET /api/scan?directory=<dir>` - Scan directory for tools
- `GET /api/installed` - List installed tools
- `POST /api/install` - Install all tools from directory
- `POST /api/install-single` - Install specific tool
- `POST /api/remove` - Remove installed tool
- `GET /api/tool-info?tool_name=<name>` - Get tool details
- `GET /api/health-check` - Check tool health
- `POST /api/setup` - Setup tool manager

## 📋 Requirements

- Python 3.6+
- Flask and Flask-CORS
- The `toolmgr` script (located at `../toolmgr`)
- Modern web browser

## 🎨 Design Philosophy

This visual wizard was designed with **non-technical users** in mind:

- **Intuitive Navigation**: File browser similar to desktop file managers
- **Visual Feedback**: Clear icons, colors, and status indicators
- **Helpful Messages**: Descriptive output and error messages  
- **Safe Operations**: Confirmation dialogs for destructive actions
- **Progressive Disclosure**: Advanced options hidden by default

## 🧪 Testing Workflow

The included test tools are perfect for testing the install/uninstall workflow:

1. **Initial Setup**: Run the wizard and scan the `test-tools` directory
2. **Install All**: Use "Install All Tools" to install the 5 test tools
3. **Verify Installation**: Check the "Installed Tools" tab
4. **Health Check**: Run health check to ensure all tools work
5. **Reinstall Testing**: Use "Force overwrite" to reinstall tools
6. **Removal Testing**: Remove individual tools and verify they're gone

## 🔒 Security Notes

- The web interface only runs locally (localhost:5000)
- File system access is limited to readable directories
- No external network access required
- All tool installations use the existing `toolmgr` security model

## 🚀 Future Enhancements

Potential improvements for the visual wizard:

- **Tool Categories**: Filter tools by category
- **Search Functionality**: Find tools by name or description
- **Bulk Operations**: Select multiple tools for batch operations
- **Tool Updates**: Check for and install tool updates
- **Import/Export**: Backup and restore tool configurations
- **User Profiles**: Different tool sets for different users

---

**🎉 Enjoy your new visual tool management experience!**