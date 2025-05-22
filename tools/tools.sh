#!/bin/bash
# tools - Manage custom command-line tools
# version="1.0.0"

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
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_header() { echo -e "${PURPLE}▶${NC} $1"; }

# Function to show a fancy tool listing
show_tools() {
    local filter_category="$1"
    local search_term="$2"
    
    if [ ! -f "$REGISTRY_FILE" ]; then
        print_warning "No tools registry found. Run 'tools setup' first."
        return 1
    fi
    
    python3 << EOF
import json
import sys
from datetime import datetime, timezone

try:
    with open('$REGISTRY_FILE', 'r') as f:
        registry = json.load(f)
    
    tools = registry.get('tools', [])
    
    # Apply filters
    if '$filter_category':
        tools = [t for t in tools if t.get('category', '').lower() == '$filter_category'.lower()]
    
    if '$search_term':
        search = '$search_term'.lower()
        tools = [t for t in tools if search in t.get('name', '').lower() or search in t.get('description', '').lower()]
    
    if not tools:
        if '$filter_category' or '$search_term':
            print("No tools found matching your criteria.")
        else:
            print("No tools installed yet.")
        sys.exit(0)
    
    # Group by category
    categories = {}
    for tool in tools:
        cat = tool.get('category', 'utility')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(tool)
    
    # Display
    print(f"📦 Custom Tools Registry ({len(tools)} tools)")
    print("=" * 50)
    
    for category, cat_tools in sorted(categories.items()):
        print(f"\n🏷️  {category.upper()}")
        print("-" * 30)
        
        for tool in sorted(cat_tools, key=lambda x: x['name']):
            name = tool['name']
            desc = tool.get('description', 'No description')
            version = tool.get('version', '?')
            
            # Check if tool exists and is executable
            import os
            exists = os.path.isfile(tool.get('path', '')) and os.access(tool.get('path', ''), os.X_OK)
            status = "✓" if exists else "✗"
            
            print(f"  {status} {name:<18} v{version:<8} {desc}")
    
    print(f"\n📊 Total: {len(tools)} tools across {len(categories)} categories")
    
except Exception as e:
    print(f"Error reading registry: {e}")
    sys.exit(1)
EOF
}

# Function to show detailed tool info
show_tool_info() {
    local tool_name="$1"
    
    python3 << EOF
import json
import sys
import os
from datetime import datetime

try:
    with open('$REGISTRY_FILE', 'r') as f:
        registry = json.load(f)
    
    tool = next((t for t in registry['tools'] if t['name'] == '$tool_name'), None)
    
    if not tool:
        print(f"❌ Tool '{tool_name}' not found.")
        print("\nAvailable tools:")
        for t in sorted(registry['tools'], key=lambda x: x['name']):
            print(f"  • {t['name']}")
        sys.exit(1)
    
    print(f"🔧 {tool['name']}")
    print("=" * (len(tool['name']) + 3))
    
    print(f"📝 Description: {tool.get('description', 'No description')}")
    print(f"📁 Path: {tool.get('path', 'Unknown')}")
    print(f"🏷️ Category: {tool.get('category', 'utility')}")
    print(f"🔢 Version: {tool.get('version', 'unknown')}")
    
    # Check if file exists and show file info
    path = tool.get('path', '')
    if os.path.isfile(path):
        stat = os.stat(path)
        size = stat.st_size
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        executable = "Yes" if os.access(path, os.X_OK) else "No"
        
        print(f"📊 File size: {size} bytes")
        print(f"⏰ Modified: {mtime}")
        print(f"🔒 Executable: {executable}")
    else:
        print("❌ File not found at registered path!")
    
    install_date = tool.get('installed_date', '')
    if install_date:
        try:
            dt = datetime.fromisoformat(install_date.replace('Z', '+00:00'))
            print(f"📅 Installed: {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        except:
            print(f"📅 Installed: {install_date}")
    
    # Show usage if available in the script
    if os.path.isfile(path):
        print(f"\n📖 Usage Information:")
        print("-" * 20)
        try:
            with open(path, 'r') as f:
                content = f.read()
                
            # Look for usage patterns
            lines = content.split('\n')
            in_usage = False
            usage_lines = []
            
            for line in lines:
                if 'Usage:' in line or 'USAGE:' in line:
                    in_usage = True
                    usage_lines.append(line.strip())
                elif in_usage and (line.strip().startswith('#') or line.strip() == ''):
                    if line.strip().startswith('#'):
                        usage_lines.append(line.strip())
                elif in_usage and line.strip():
                    break
            
            if usage_lines:
                for line in usage_lines[:10]:  # Limit to first 10 lines
                    print(f"  {line}")
            else:
                print("  Run the command with --help for usage information")
                
        except:
            print("  Unable to read usage information")
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
EOF
}

# Function to check tool health
check_tools_health() {
    print_header "Checking tools health..."
    
    python3 << EOF
import json
import os
import sys

try:
    with open('$REGISTRY_FILE', 'r') as f:
        registry = json.load(f)
    
    tools = registry.get('tools', [])
    healthy = 0
    broken = 0
    
    for tool in tools:
        name = tool['name']
        path = tool.get('path', '')
        
        if os.path.isfile(path) and os.access(path, os.X_OK):
            print(f"✅ {name} - OK")
            healthy += 1
        else:
            print(f"❌ {name} - BROKEN (not found or not executable)")
            broken += 1
    
    print(f"\n📊 Health Summary:")
    print(f"  Healthy: {healthy}")
    print(f"  Broken: {broken}")
    print(f"  Total: {len(tools)}")
    
    if broken > 0:
        print(f"\n💡 To fix broken tools, try reinstalling them or run 'tools cleanup'")
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
EOF
}

# Function to clean up broken tools
cleanup_tools() {
    print_header "Cleaning up broken tools..."
    
    python3 << EOF
import json
import os
from datetime import datetime

try:
    with open('$REGISTRY_FILE', 'r') as f:
        registry = json.load(f)
    
    original_count = len(registry.get('tools', []))
    cleaned_tools = []
    removed_tools = []
    
    for tool in registry.get('tools', []):
        path = tool.get('path', '')
        if os.path.isfile(path) and os.access(path, os.X_OK):
            cleaned_tools.append(tool)
        else:
            removed_tools.append(tool['name'])
    
    registry['tools'] = cleaned_tools
    registry['last_updated'] = datetime.utcnow().isoformat() + "Z"
    
    with open('$REGISTRY_FILE', 'w') as f:
        json.dump(registry, f, indent=2)
    
    removed_count = len(removed_tools)
    print(f"🧹 Removed {removed_count} broken tool(s): {', '.join(removed_tools)}")
    print(f"✅ {len(cleaned_tools)} healthy tools remain")
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
EOF
}

# Function to show usage
show_usage() {
    cat << 'EOF'
🔧 Tools Manager - Manage your custom command-line tools

USAGE:
    tools [COMMAND] [OPTIONS]

COMMANDS:
    list [category] [search]    List all tools or filter by category/search
    info <n>                 Show detailed information about a tool
    health                      Check health status of all tools
    cleanup                     Remove broken tools from registry
    registry                    Show registry information
    categories                  List all available categories
    search <term>              Search tools by name or description
    
EXAMPLES:
    tools list                  # List all tools
    tools list development      # List tools in 'development' category
    tools search git            # Search for tools containing 'git'
    tools info repo-analyze     # Show details about specific tool
    tools health                # Check if all tools are working
    tools cleanup               # Remove broken tools

CATEGORIES:
    development, utility, analysis, automation, deployment, monitoring

💡 TIP: Use 'install-tools setup' to set up the tools environment initially
EOF
}

# Ensure registry exists
if [ ! -f "$REGISTRY_FILE" ] && [ "$1" != "setup" ] && [ "$1" != "help" ] && [ "$1" != "--help" ] && [ "$1" != "-h" ]; then
    print_warning "Tools registry not found. Setting up..."
    mkdir -p "$TOOLS_REGISTRY"
    echo '{"tools": [], "version": "1.0.0", "last_updated": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"}' > "$REGISTRY_FILE"
fi

# Main command handling
case "${1:-list}" in
    list|ls)
        show_tools "$2" "$3"
        ;;
    
    info|show)
        if [ -z "$2" ]; then
            print_error "Usage: tools info <tool-name>"
            exit 1
        fi
        show_tool_info "$2"
        ;;
    
    health|check)
        check_tools_health
        ;;
    
    cleanup|clean)
        cleanup_tools
        ;;
    
    registry|reg)
        print_header "Tools Registry Information"
        echo "Registry file: $REGISTRY_FILE"
        echo "Tools directory: $TOOLS_DIR"
        if [ -f "$REGISTRY_FILE" ]; then
            python3 -c "import json; r=json.load(open('$REGISTRY_FILE')); print(f'Last updated: {r.get(\"last_updated\", \"unknown\")}'); print(f'Registry version: {r.get(\"version\", \"unknown\")}'); print(f'Total tools: {len(r.get(\"tools\", []))}')"
        else
            print_error "Registry file not found"
        fi
        ;;
    
    categories|cats)
        print_header "Available Categories"
        if [ -f "$REGISTRY_FILE" ]; then
            python3 -c "import json; r=json.load(open('$REGISTRY_FILE')); cats=set(t.get('category','utility') for t in r.get('tools',[])); [print(f'  • {c}') for c in sorted(cats)] if cats else print('  No categories found')"
        else
            print_error "Registry file not found"
        fi
        ;;
    
    search|find)
        if [ -z "$2" ]; then
            print_error "Usage: tools search <search-term>"
            exit 1
        fi
        show_tools "" "$2"
        ;;
    
    help|--help|-h)
        show_usage
        ;;
    
    *)
        print_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac