#!/bin/bash
# install-tools.sh - Install custom tools to your environment

set -e

# Configuration
TOOLS_DIR="$HOME/.local/bin"
TOOLS_REGISTRY="$HOME/.local/share/custom-tools"
REGISTRY_FILE="$TOOLS_REGISTRY/registry.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Function to ensure directories exist
setup_directories() {
    mkdir -p "$TOOLS_DIR"
    mkdir -p "$TOOLS_REGISTRY"
    
    # Initialize registry if it doesn't exist
    if [ ! -f "$REGISTRY_FILE" ]; then
        echo '{"tools": [], "version": "1.0.0", "last_updated": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"}' > "$REGISTRY_FILE"
    fi
}

# Function to check if tools directory is in PATH
check_path() {
    if [[ ":$PATH:" != *":$TOOLS_DIR:"* ]]; then
        print_warning "Tools directory ($TOOLS_DIR) is not in your PATH"
        print_info "Add this line to your ~/.bashrc, ~/.zshrc, or appropriate shell config:"
        echo "export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo ""
        read -p "Would you like me to add it to your shell config automatically? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            add_to_path
        fi
    fi
}

# Function to add tools directory to PATH
add_to_path() {
    local shell_config=""
    
    # Detect shell and config file
    case "$SHELL" in
        */bash) shell_config="$HOME/.bashrc" ;;
        */zsh) shell_config="$HOME/.zshrc" ;;
        */fish) shell_config="$HOME/.config/fish/config.fish" ;;
        *) shell_config="$HOME/.profile" ;;
    esac
    
    if [ -f "$shell_config" ]; then
        echo "" >> "$shell_config"
        echo "# Custom tools directory" >> "$shell_config"
        echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$shell_config"
        print_success "Added to $shell_config"
        print_info "Please restart your terminal or run: source $shell_config"
    else
        print_error "Could not detect shell config file. Please add manually."
    fi
}

# Function to register a tool
register_tool() {
    local tool_name="$1"
    local tool_path="$2"
    local description="$3"
    local version="$4"
    local category="$5"
    
    # Create temporary file with updated registry
    local temp_file=$(mktemp)
    
    # Use Python to update JSON (more reliable than jq for complex operations)
    python3 << EOF > "$temp_file"
import json
import sys
from datetime import datetime

try:
    with open('$REGISTRY_FILE', 'r') as f:
        registry = json.load(f)
except:
    registry = {"tools": [], "version": "1.0.0", "last_updated": ""}

# Remove existing entry if it exists
registry['tools'] = [tool for tool in registry['tools'] if tool['name'] != '$tool_name']

# Add new entry
new_tool = {
    "name": "$tool_name",
    "path": "$tool_path",
    "description": "$description",
    "version": "$version",
    "category": "$category",
    "installed_date": datetime.utcnow().isoformat() + "Z"
}

registry['tools'].append(new_tool)
registry['last_updated'] = datetime.utcnow().isoformat() + "Z"

print(json.dumps(registry, indent=2))
EOF
    
    if [ $? -eq 0 ]; then
        mv "$temp_file" "$REGISTRY_FILE"
        print_success "Registered tool: $tool_name"
    else
        rm -f "$temp_file"
        print_error "Failed to register tool: $tool_name"
    fi
}

# Function to install a tool
install_tool() {
    local source_file="$1"
    local tool_name="$2"
    local description="$3"
    local category="${4:-utility}"
    
    if [ ! -f "$source_file" ]; then
        print_error "Source file not found: $source_file"
        return 1
    fi
    
    local target_path="$TOOLS_DIR/$tool_name"
    
    # Copy and make executable
    cp "$source_file" "$target_path"
    chmod +x "$target_path"
    
    # Extract version from script if available
    local version=$(grep -o 'version="[^"]*"' "$source_file" | cut -d'"' -f2 || echo "1.0.0")
    
    # Register the tool
    register_tool "$tool_name" "$target_path" "$description" "$version" "$category"
    
    print_success "Installed: $tool_name -> $target_path"
}

# Function to uninstall a tool
uninstall_tool() {
    local tool_name="$1"
    local tool_path="$TOOLS_DIR/$tool_name"
    
    if [ -f "$tool_path" ]; then
        rm "$tool_path"
        print_success "Removed: $tool_path"
    fi
    
    # Remove from registry
    local temp_file=$(mktemp)
    python3 << EOF > "$temp_file"
import json
from datetime import datetime

try:
    with open('$REGISTRY_FILE', 'r') as f:
        registry = json.load(f)
    
    registry['tools'] = [tool for tool in registry['tools'] if tool['name'] != '$tool_name']
    registry['last_updated'] = datetime.utcnow().isoformat() + "Z"
    
    print(json.dumps(registry, indent=2))
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
EOF
    
    if [ $? -eq 0 ]; then
        mv "$temp_file" "$REGISTRY_FILE"
        print_success "Unregistered tool: $tool_name"
    else
        rm -f "$temp_file"
        print_error "Failed to unregister tool: $tool_name"
    fi
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [COMMAND] [OPTIONS]

COMMANDS:
    install <script> <name> <description> [category]
                        Install a script as a command-line tool
    uninstall <name>    Uninstall a tool
    setup               Set up the tools environment
    list                List all installed tools
    info <name>         Show information about a specific tool
    update-registry     Update the tools registry
    
EXAMPLES:
    $0 setup
    $0 install ./repo-full-code.sh repo-analyze "Analyze repository code" development
    $0 install ./repo-diff-analysis.sh repo-diff "Analyze git diffs" development
    $0 list
    $0 info repo-analyze
    $0 uninstall repo-analyze

CATEGORIES:
    development, utility, analysis, automation, deployment, monitoring
EOF
}

# Main script logic
case "${1:-}" in
    setup)
        print_info "Setting up custom tools environment..."
        setup_directories
        check_path
        print_success "Setup complete!"
        ;;
    
    install)
        if [ $# -lt 4 ]; then
            print_error "Usage: $0 install <script> <name> <description> [category]"
            exit 1
        fi
        setup_directories
        install_tool "$2" "$3" "$4" "${5:-utility}"
        ;;
    
    uninstall)
        if [ $# -lt 2 ]; then
            print_error "Usage: $0 uninstall <name>"
            exit 1
        fi
        uninstall_tool "$2"
        ;;
    
    list)
        setup_directories
        print_info "Installed custom tools:"
        python3 << 'EOF'
import json
import sys
from datetime import datetime

try:
    with open("$TOOLS_REGISTRY/registry.json".replace("$TOOLS_REGISTRY", "$TOOLS_REGISTRY"), 'r') as f:
        registry = json.load(f)
    
    if not registry['tools']:
        print("No tools installed.")
        sys.exit(0)
    
    # Group by category
    categories = {}
    for tool in registry['tools']:
        cat = tool.get('category', 'utility')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(tool)
    
    for category, tools in sorted(categories.items()):
        print(f"\n{category.upper()}:")
        for tool in sorted(tools, key=lambda x: x['name']):
            print(f"  {tool['name']:<20} - {tool['description']}")
            
except Exception as e:
    print(f"Error reading registry: {e}")
    sys.exit(1)
EOF
        ;;
    
    info)
        if [ $# -lt 2 ]; then
            print_error "Usage: $0 info <name>"
            exit 1
        fi
        python3 << EOF
import json
import sys

try:
    with open('$REGISTRY_FILE', 'r') as f:
        registry = json.load(f)
    
    tool_name = '$2'
    tool = next((t for t in registry['tools'] if t['name'] == tool_name), None)
    
    if not tool:
        print(f"Tool '{tool_name}' not found.")
        sys.exit(1)
    
    print(f"Name: {tool['name']}")
    print(f"Description: {tool['description']}")
    print(f"Path: {tool['path']}")
    print(f"Version: {tool.get('version', 'unknown')}")
    print(f"Category: {tool.get('category', 'utility')}")
    print(f"Installed: {tool.get('installed_date', 'unknown')}")
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
EOF
        ;;
    
    update-registry)
        setup_directories
        print_info "Registry location: $REGISTRY_FILE"
        print_info "Tools directory: $TOOLS_DIR"
        print_success "Registry is up to date"
        ;;
    
    help|--help|-h|"")
        show_usage
        ;;
    
    *)
        print_error "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac