#!/bin/bash
# pyenv-activator - Smart Python environment activator that preserves custom tools
# description: Activate Python environments while preserving custom tools in PATH
# version: 1.1.0
# category: development

# This script should be sourced, not executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "⚠️  Error: This script needs to be sourced, not executed."
    echo "Please use: source $(basename ${BASH_SOURCE[0]}) /path/to/env"
    echo "Or add it to your .bashrc/.zshrc and use the function: pyenv-activate /path/to/env"
    exit 1
fi

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

print_info() { echo -e "${BLUE}ℹ${NC} $1"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_debug() { [[ "${PYACT_DEBUG:-}" == "1" ]] && echo -e "${CYAN}[DEBUG]${NC} $1"; }

# Configuration
CUSTOM_TOOLS_DIRS=(
    "$HOME/.local/bin"
    "/usr/local/bin"
    "$HOME/bin"
)

# Store original PATH before any modifications
if [ -z "$PYACT_ORIGINAL_PATH" ]; then
    export PYACT_ORIGINAL_PATH="$PATH"
fi

# Function to preserve custom tools in PATH
preserve_custom_tools() {
    local new_path="$PATH"
    
    # Add each custom tools directory to the front of PATH if not already there
    for tools_dir in "${CUSTOM_TOOLS_DIRS[@]}"; do
        if [ -d "$tools_dir" ] && [[ ":$new_path:" != *":$tools_dir:"* ]]; then
            new_path="$tools_dir:$new_path"
            print_debug "Added $tools_dir to PATH"
        fi
    done
    
    export PATH="$new_path"
}

# Function to detect Python environment type
detect_env_type() {
    local env_path="$1"
    
    # Check for various environment indicators
    if [ -f "$env_path/pyvenv.cfg" ]; then
        echo "venv"
    elif [ -f "$env_path/conda-meta/history" ]; then
        echo "conda"
    elif [ -d "$env_path/.venv" ]; then
        echo "poetry"
    elif [ -f "$env_path/Pipfile" ]; then
        echo "pipenv"
    elif [ -f "$env_path/bin/activate" ]; then
        echo "virtualenv"
    else
        echo "unknown"
    fi
}

# Function to activate different environment types
activate_environment() {
    local env_path="$1"
    local env_type="$2"
    
    case "$env_type" in
        venv|virtualenv)
            if [ -f "$env_path/bin/activate" ]; then
                print_info "Activating Python virtual environment..."
                source "$env_path/bin/activate"
                return 0
            fi
            ;;
        conda)
            if command -v conda >/dev/null 2>&1; then
                print_info "Activating Conda environment..."
                conda activate "$(basename "$env_path")"
                return 0
            fi
            ;;
        poetry)
            if command -v poetry >/dev/null 2>&1; then
                print_info "Activating Poetry environment..."
                cd "$env_path"
                poetry shell
                return 0
            fi
            ;;
        pipenv)
            if command -v pipenv >/dev/null 2>&1; then
                print_info "Activating Pipenv environment..."
                cd "$env_path"
                pipenv shell
                return 0
            fi
            ;;
    esac
    
    return 1
}

# Function to auto-detect environment in current directory
auto_detect_env() {
    local current_dir="$(pwd)"
    
    # Check for common environment files/directories
    if [ -f "pyproject.toml" ] && command -v poetry >/dev/null 2>&1; then
        echo "poetry|$current_dir"
        return 0
    elif [ -f "Pipfile" ] && command -v pipenv >/dev/null 2>&1; then
        echo "pipenv|$current_dir"
        return 0
    elif [ -d "venv" ]; then
        echo "venv|$current_dir/venv"
        return 0
    elif [ -d ".venv" ]; then
        echo "venv|$current_dir/.venv"
        return 0
    elif [ -d "env" ]; then
        echo "venv|$current_dir/env"
        return 0
    fi
    
    return 1
}

# Function to show current environment status
pyenv_status() {
    echo "🐍 Python Environment Status"
    echo "=============================="
    
    if [ -n "${VIRTUAL_ENV:-}" ]; then
        echo "Active Environment: $(basename "$VIRTUAL_ENV")"
        echo "Environment Path: $VIRTUAL_ENV"
        echo "Python Version: $(python --version 2>&1)"
    elif [ -n "${CONDA_DEFAULT_ENV:-}" ]; then
        echo "Active Environment: $CONDA_DEFAULT_ENV (Conda)"
        echo "Python Version: $(python --version 2>&1)"
    else
        echo "No Python environment active"
        if command -v python >/dev/null 2>&1; then
            echo "System Python: $(which python)"
            echo "Python Version: $(python --version 2>&1)"
        else
            echo "Python not found in PATH"
        fi
    fi
    
    echo ""
    echo "🔧 Custom Tools Status"
    echo "======================"
    
    for tools_dir in "${CUSTOM_TOOLS_DIRS[@]}"; do
        if [ -d "$tools_dir" ]; then
            local in_path="NO"
            [[ ":$PATH:" == *":$tools_dir:"* ]] && in_path="YES"
            echo "  $tools_dir: $in_path"
            
            # Check for toolmgr specifically
            if [ -x "$tools_dir/toolmgr" ]; then
                echo "    └─ toolmgr: $([ "$in_path" = "YES" ] && echo "✅ Available" || echo "❌ Not in PATH")"
            fi
        fi
    done
    
    echo ""
    echo "Current PATH:"
    echo "$PATH" | tr ':' '\n' | nl
}

# Function to fix PATH (restore custom tools)
pyenv_fix_path() {
    print_info "Restoring custom tools to PATH..."
    preserve_custom_tools
    
    # Verify tools are available
    local tools_found=0
    for tools_dir in "${CUSTOM_TOOLS_DIRS[@]}"; do
        if [ -d "$tools_dir" ] && [[ ":$PATH:" == *":$tools_dir:"* ]]; then
            ((tools_found++))
            print_success "✓ $tools_dir is in PATH"
            
            # Check for toolmgr specifically
            if [ -x "$tools_dir/toolmgr" ]; then
                print_success "  └─ toolmgr is available"
            fi
        fi
    done
    
    if [ $tools_found -eq 0 ]; then
        print_warning "No custom tools directories found in PATH"
    fi
}

# Function to deactivate environment
pyenv_deactivate() {
    if [ -n "${VIRTUAL_ENV:-}" ] && command -v deactivate >/dev/null 2>&1; then
        print_info "Deactivating Python environment..."
        deactivate
    elif [ -n "${CONDA_DEFAULT_ENV:-}" ] && command -v conda >/dev/null 2>&1; then
        print_info "Deactivating Conda environment..."
        conda deactivate
    else
        print_warning "No active Python environment to deactivate"
    fi
    
    # Restore original PATH
    if [ -n "$PYACT_ORIGINAL_PATH" ]; then
        export PATH="$PYACT_ORIGINAL_PATH"
        print_success "Restored original PATH"
    fi
}

# Function to list available environments
pyenv_list() {
    echo "🐍 Available Python Environments"
    echo "================================="
    
    # Check for venv/virtualenv directories
    echo ""
    echo "Virtual Environments:"
    local found_venv=false
    
    for venv_dir in venv .venv env; do
        if [ -d "$venv_dir" ]; then
            echo "  📁 ./$venv_dir ($(detect_env_type "$venv_dir"))"
            found_venv=true
        fi
    done
    
    # Check common virtualenv locations
    for common_dir in "$HOME/.virtualenvs" "$HOME/envs" "$HOME/.local/share/virtualenvs" "$HOME/python_env"; do
        if [ -d "$common_dir" ]; then
            for env_dir in "$common_dir"/*; do
                if [ -d "$env_dir" ] && [ -f "$env_dir/bin/activate" ]; then
                    echo "  📁 $env_dir ($(detect_env_type "$env_dir"))"
                    found_venv=true
                fi
            done
        fi
    done
    
    if [ "$found_venv" = false ]; then
        echo "  (No virtual environments found)"
    fi
    
    # Check for Conda environments
    if command -v conda >/dev/null 2>&1; then
        echo ""
        echo "Conda Environments:"
        conda env list 2>/dev/null | grep -v "^#" | while read -r name path; do
            if [ -n "$name" ] && [ "$name" != "base" ]; then
                echo "  🐍 $name"
            fi
        done
    fi
    
    # Check for Poetry/Pipenv in current directory
    echo ""
    echo "Project-based Environments:"
    if [ -f "pyproject.toml" ]; then
        echo "  📦 Poetry project detected"
    fi
    if [ -f "Pipfile" ]; then
        echo "  📦 Pipenv project detected"
    fi
    if [ ! -f "pyproject.toml" ] && [ ! -f "Pipfile" ]; then
        echo "  (No project-based environments detected)"
    fi
}

# Main activation function
pyenv_activate() {
    local env_path="$1"
    
    # Store current state
    print_debug "Original PATH: $PATH"
    
    # Auto-detect if no path provided
    if [ -z "$env_path" ]; then
        local detected=$(auto_detect_env)
        if [ $? -eq 0 ]; then
            local env_type=$(echo "$detected" | cut -d'|' -f1)
            env_path=$(echo "$detected" | cut -d'|' -f2)
            print_info "Auto-detected $env_type environment: $env_path"
        else
            print_error "No environment specified and none auto-detected"
            echo ""
            echo "Usage: pyenv-activate <environment-path>"
            echo "   or: pyenv-activate auto (to auto-detect)"
            echo "   or: pyenv-activate list (to see available environments)"
            return 1
        fi
    fi
    
    # Handle special keywords
    case "$env_path" in
        auto)
            pyenv_activate ""  # Recursive call with empty path for auto-detection
            return $?
            ;;
        list)
            pyenv_list
            return 0
            ;;
        status)
            pyenv_status
            return 0
            ;;
        fix)
            pyenv_fix_path
            return 0
            ;;
        deactivate|off)
            pyenv_deactivate
            return 0
            ;;
        help|--help|-h)
            pyenv_help
            return 0
            ;;
    esac
    
    # Detect environment type
    local env_type=$(detect_env_type "$env_path")
    print_debug "Detected environment type: $env_type"
    
    # Activate the environment
    if activate_environment "$env_path" "$env_type"; then
        print_success "Environment activated: $env_path"
        
        # Preserve custom tools
        preserve_custom_tools
        print_success "Custom tools preserved in PATH"
        
        # Verify toolmgr is available
        if command -v toolmgr >/dev/null 2>&1; then
            print_success "✓ toolmgr is available"
        else
            print_warning "⚠ toolmgr not found - run 'pyenv-activate fix' to restore"
        fi
        
        print_debug "Final PATH: $PATH"
        return 0
    else
        print_error "Failed to activate environment: $env_path"
        return 1
    fi
}

# Show usage help
pyenv_help() {
    cat << 'EOF'
🐍 Smart Python Environment Activator

USAGE:
    pyenv-activate [COMMAND|PATH]

COMMANDS:
    auto                Auto-detect and activate environment in current directory
    list                List available Python environments
    status              Show current environment and tools status
    fix                 Fix PATH to restore custom tools
    deactivate|off      Deactivate current environment and restore PATH
    help                Show this help

EXAMPLES:
    pyenv-activate ./venv             # Activate specific virtual environment
    pyenv-activate auto               # Auto-detect and activate
    pyenv-activate list               # See available environments
    pyenv-activate status             # Check current status
    pyenv-activate fix                # Fix PATH if tools are missing
    pyenv-activate off                # Deactivate environment

FEATURES:
    • Auto-detects venv, conda, poetry, pipenv environments
    • Preserves custom tools (toolmgr, etc.) in PATH
    • Smart environment detection
    • Easy activation and deactivation
    • Status monitoring

The function automatically preserves your custom tools directory in PATH
when activating Python environments, preventing tools like 'toolmgr'
from becoming unavailable.
EOF
}

# Check if command was provided when sourcing
if [ "$#" -gt 0 ]; then
    pyenv_activate "$@"
fi

# Main function that can be used directly after sourcing
pyenv-activate() {
    pyenv_activate "$@"
}

# Alias for ease of use
alias pyact="pyenv-activate"

echo "📋 Python environment activator loaded. Use 'pyenv-activate' or 'pyact' to activate environments."
echo "Example: pyenv-activate /path/to/env"