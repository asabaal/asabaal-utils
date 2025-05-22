#!/bin/bash
# install-toolmgr.sh - One-time installer for the tool manager
# Just run this once: ./install-toolmgr.sh

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_info() { echo -e "${BLUE}ℹ${NC} $1"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }

echo "🔧 Tool Manager Installer"
echo "========================"
echo ""

# Check if toolmgr file exists in current directory
if [ ! -f "toolmgr" ]; then
    print_error "toolmgr file not found in current directory"
    echo ""
    echo "Please make sure you have the 'toolmgr' script in the same directory as this installer."
    exit 1
fi

# Choose installation directory
INSTALL_DIR=""

# Check for ~/.local/bin (preferred)
if [ -d "$HOME/.local/bin" ] || mkdir -p "$HOME/.local/bin" 2>/dev/null; then
    INSTALL_DIR="$HOME/.local/bin"
    print_info "Using user directory: $INSTALL_DIR"
# Check for system directories
elif [ -w "/usr/local/bin" ] 2>/dev/null; then
    INSTALL_DIR="/usr/local/bin"
    print_info "Using system directory: $INSTALL_DIR"
else
    # Try to create ~/.local/bin
    mkdir -p "$HOME/.local/bin"
    INSTALL_DIR="$HOME/.local/bin"
    print_info "Created and using: $INSTALL_DIR"
fi

# Install toolmgr
print_info "Installing toolmgr to $INSTALL_DIR..."
cp toolmgr "$INSTALL_DIR/toolmgr"
chmod +x "$INSTALL_DIR/toolmgr"
print_success "toolmgr installed successfully!"

# Check if directory is in PATH
if [[ ":$PATH:" == *":$INSTALL_DIR:"* ]]; then
    print_success "Installation directory is already in PATH"
    PATH_UPDATED=false
else
    print_warning "Installation directory is not in PATH"
    
    # Offer to add to PATH
    echo ""
    echo "I can add $INSTALL_DIR to your PATH automatically."
    read -p "Add to PATH? (y/n): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Detect shell config file
        SHELL_CONFIG=""
        case "$SHELL" in
            */bash) SHELL_CONFIG="$HOME/.bashrc" ;;
            */zsh) SHELL_CONFIG="$HOME/.zshrc" ;;
            */fish) SHELL_CONFIG="$HOME/.config/fish/config.fish" ;;
            *) SHELL_CONFIG="$HOME/.profile" ;;
        esac
        
        if [ -f "$SHELL_CONFIG" ]; then
            echo "" >> "$SHELL_CONFIG"
            echo "# Tool manager PATH (added by install-toolmgr.sh)" >> "$SHELL_CONFIG"
            echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> "$SHELL_CONFIG"
            print_success "Added to $SHELL_CONFIG"
            PATH_UPDATED=true
        else
            print_error "Could not detect shell config file"
            print_info "Please add this line to your shell config manually:"
            echo "  export PATH=\"$INSTALL_DIR:\$PATH\""
            PATH_UPDATED=false
        fi
    else
        print_info "You can add this to your shell config manually:"
        echo "  export PATH=\"$INSTALL_DIR:\$PATH\""
        PATH_UPDATED=false
    fi
fi

# Run initial setup
print_info "Running initial setup..."
if [[ ":$PATH:" == *":$INSTALL_DIR:"* ]] || [ "$PATH_UPDATED" = true ]; then
    # PATH is ready, can run toolmgr directly
    if [ "$PATH_UPDATED" = true ]; then
        # Need to update current session PATH
        export PATH="$INSTALL_DIR:$PATH"
    fi
    toolmgr setup
else
    # PATH not updated, run with full path
    "$INSTALL_DIR/toolmgr" setup
fi

echo ""
echo "🎉 Installation Complete!"
echo "========================"
echo ""

if [ "$PATH_UPDATED" = true ]; then
    print_success "toolmgr is ready to use!"
    print_info "Restart your terminal or run: source $SHELL_CONFIG"
    echo ""
    echo "Next steps:"
    echo "  toolmgr scan .              # See what tools are in current directory"
    echo "  toolmgr install-dir .       # Install all tools from current directory"
    echo "  toolmgr list                # List installed tools"
elif [[ ":$PATH:" == *":$INSTALL_DIR:"* ]]; then
    print_success "toolmgr is ready to use!"
    echo ""
    echo "Next steps:"
    echo "  toolmgr scan .              # See what tools are in current directory"
    echo "  toolmgr install-dir .       # Install all tools from current directory"
    echo "  toolmgr list                # List installed tools"
else
    print_warning "Manual step required:"
    echo "  Add to PATH: export PATH=\"$INSTALL_DIR:\$PATH\""
    echo "  Then run: toolmgr scan ."
fi

echo ""
print_info "Tool manager installed at: $INSTALL_DIR/toolmgr"