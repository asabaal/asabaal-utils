#!/usr/bin/env python3
"""
Visual Tool Manager Backend
Flask API that wraps the existing toolmgr bash script
"""

import os
import json
import subprocess
import sys
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configuration
TOOLMGR_PATH = Path(__file__).parent.parent.parent / "toolmgr"
DEFAULT_SCAN_DIRS = [
    str(Path(__file__).parent.parent / "test-tools"),
    str(Path.home() / "bin"),
    str(Path.home() / ".local" / "bin"),
    "/usr/local/bin"
]

def run_toolmgr(command: list, capture_output=True):
    """Run toolmgr command and return result"""
    try:
        cmd = [str(TOOLMGR_PATH)] + command
        result = subprocess.run(
            cmd, 
            capture_output=capture_output, 
            text=True, 
            check=False
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "toolmgr_path": str(TOOLMGR_PATH)})

@app.route('/api/directories')
def list_directories():
    """Get list of common directories to scan"""
    dirs = []
    for dir_path in DEFAULT_SCAN_DIRS:
        if os.path.exists(dir_path):
            dirs.append({
                "path": dir_path,
                "name": os.path.basename(dir_path) or dir_path,
                "exists": True,
                "writable": os.access(dir_path, os.W_OK)
            })
        else:
            dirs.append({
                "path": dir_path,
                "name": os.path.basename(dir_path) or dir_path,
                "exists": False,
                "writable": False
            })
    
    return jsonify({"directories": dirs})

@app.route('/api/browse')
def browse_directory():
    """Browse a directory and return subdirectories and files"""
    path = request.args.get('path', os.path.expanduser('~'))
    
    try:
        if not os.path.exists(path):
            return jsonify({"error": "Directory does not exist"}), 404
        
        if not os.path.isdir(path):
            return jsonify({"error": "Path is not a directory"}), 400
        
        items = []
        for item in sorted(os.listdir(path)):
            item_path = os.path.join(path, item)
            if item.startswith('.'):
                continue
                
            item_info = {
                "name": item,
                "path": item_path,
                "is_directory": os.path.isdir(item_path),
                "is_executable": os.access(item_path, os.X_OK) if os.path.isfile(item_path) else False
            }
            items.append(item_info)
        
        parent_path = os.path.dirname(path) if path != '/' else None
        
        return jsonify({
            "current_path": path,
            "parent_path": parent_path,
            "items": items
        })
        
    except PermissionError:
        return jsonify({"error": "Permission denied"}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scan')
def scan_directory():
    """Scan directory for tools"""
    directory = request.args.get('directory')
    if not directory:
        return jsonify({"error": "Directory parameter required"}), 400
    
    if not os.path.exists(directory):
        return jsonify({"error": "Directory does not exist"}), 404
    
    # Use toolmgr to scan the directory
    result = run_toolmgr(['scan', directory])
    
    if not result["success"]:
        return jsonify({
            "error": "Failed to scan directory",
            "details": result["stderr"]
        }), 500
    
    # Parse the output to extract tool information
    tools = []
    lines = result["stdout"].split('\n')
    
    # Look for the table content
    in_table = False
    for line in lines:
        if '│' in line and 'Name' in line and 'Version' in line:
            in_table = True
            continue
        elif '└' in line:
            in_table = False
            continue
        elif in_table and '│' in line and 'ERROR' not in line:
            # Parse table row
            parts = [part.strip() for part in line.split('│') if part.strip()]
            if len(parts) >= 4:
                tools.append({
                    "name": parts[0],
                    "version": parts[1],
                    "category": parts[2],
                    "description": parts[3]
                })
    
    return jsonify({
        "directory": directory,
        "tools": tools,
        "raw_output": result["stdout"]
    })

@app.route('/api/installed')
def list_installed():
    """List installed tools"""
    result = run_toolmgr(['list'])
    
    if not result["success"]:
        return jsonify({
            "error": "Failed to list tools",
            "details": result["stderr"]
        }), 500
    
    return jsonify({
        "output": result["stdout"],
        "success": True
    })

@app.route('/api/install', methods=['POST'])
def install_tool():
    """Install a tool from directory"""
    data = request.get_json()
    directory = data.get('directory')
    force = data.get('force', False)
    
    if not directory:
        return jsonify({"error": "Directory parameter required"}), 400
    
    command = ['install-dir', directory]
    if force:
        command.append('--force')
    
    result = run_toolmgr(command)
    
    return jsonify({
        "success": result["success"],
        "output": result["stdout"],
        "error": result["stderr"] if not result["success"] else None
    })

@app.route('/api/install-single', methods=['POST'])
def install_single_tool():
    """Install a single tool file"""
    data = request.get_json()
    file_path = data.get('file_path')
    force = data.get('force', False)
    
    if not file_path:
        return jsonify({"error": "file_path parameter required"}), 400
    
    command = ['install', file_path]
    if force:
        command.append('--force')
    
    result = run_toolmgr(command)
    
    return jsonify({
        "success": result["success"],
        "output": result["stdout"],
        "error": result["stderr"] if not result["success"] else None
    })

@app.route('/api/remove', methods=['POST'])
def remove_tool():
    """Remove an installed tool"""
    data = request.get_json()
    tool_name = data.get('tool_name')
    
    if not tool_name:
        return jsonify({"error": "tool_name parameter required"}), 400
    
    result = run_toolmgr(['remove', tool_name])
    
    return jsonify({
        "success": result["success"],
        "output": result["stdout"],
        "error": result["stderr"] if not result["success"] else None
    })

@app.route('/api/tool-info')
def tool_info():
    """Get information about a specific tool"""
    tool_name = request.args.get('tool_name')
    
    if not tool_name:
        return jsonify({"error": "tool_name parameter required"}), 400
    
    result = run_toolmgr(['info', tool_name])
    
    return jsonify({
        "success": result["success"],
        "output": result["stdout"],
        "error": result["stderr"] if not result["success"] else None
    })

@app.route('/api/health-check')
def health_check_tools():
    """Check health of installed tools"""
    result = run_toolmgr(['health'])
    
    return jsonify({
        "success": result["success"],
        "output": result["stdout"],
        "error": result["stderr"] if not result["success"] else None
    })

@app.route('/api/setup', methods=['POST'])
def setup_toolmgr():
    """Setup toolmgr environment"""
    result = run_toolmgr(['setup'], capture_output=False)
    
    return jsonify({
        "success": result["success"],
        "message": "Setup initiated. Check console for interactive prompts."
    })

# Serve static files
@app.route('/')
def serve_index():
    """Serve the main interface"""
    return send_from_directory('static', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

if __name__ == '__main__':
    # Ensure toolmgr exists
    if not TOOLMGR_PATH.exists():
        print(f"Error: toolmgr not found at {TOOLMGR_PATH}")
        sys.exit(1)
    
    print(f"Starting Visual Tool Manager API...")
    print(f"Toolmgr path: {TOOLMGR_PATH}")
    print(f"Test tools directory: {DEFAULT_SCAN_DIRS[0]}")
    app.run(debug=True, host='0.0.0.0', port=5000)