#!/bin/bash
# Installation script for Pass CLI with Keyboard Total Control
# This script installs Pass CLI with Keyboard Total Control system-wide or for current user

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${BLUE}ℹ ${NC}$1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    print_success "Python 3 found: $(python3 --version)"
    
    # Check pip
    if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
        print_error "pip is not installed"
        exit 1
    fi
    print_success "pip found"
    
    # Check pass
    if ! command -v pass &> /dev/null; then
        print_warning "pass (password-store) is not installed"
        print_info "Install it with: sudo pacman -S pass"
    else
        print_success "pass found: $(pass --version | head -n1)"
    fi
}

# Install system-wide (requires sudo)
install_system() {
    print_info "Installing Pass CLI with Keyboard Total Control system-wide..."
    
    # Install Python package
    print_info "Installing Python package..."
    sudo pip install --upgrade .
    
    # Install desktop entry
    print_info "Installing desktop entry..."
    sudo install -Dm644 pass-kb.desktop /usr/share/applications/pass-kb.desktop
    
    # Update desktop database
    if command -v update-desktop-database &> /dev/null; then
        sudo update-desktop-database /usr/share/applications
        print_success "Desktop database updated"
    fi
    
    print_success "System-wide installation completed!"
    print_info "You can now launch 'Pass Keyboard Control' from your application launcher (rofi/walker)"
}

# Install for current user only
install_user() {
    print_info "Installing Pass CLI with Keyboard Total Control for current user..."
    
    # Install Python package
    print_info "Installing Python package..."
    pip install --user --upgrade .
    
    # Create user applications directory if it doesn't exist
    mkdir -p ~/.local/share/applications
    
    # Install desktop entry for user
    print_info "Installing desktop entry..."
    install -Dm644 pass-kb.desktop ~/.local/share/applications/pass-kb.desktop
    
    # Update desktop database for user
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database ~/.local/share/applications
        print_success "Desktop database updated"
    fi
    
    # Check if ~/.local/bin is in PATH
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        print_warning "~/.local/bin is not in your PATH"
        print_info "Add this to your ~/.bashrc or ~/.zshrc:"
        echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
    
    print_success "User installation completed!"
    print_info "You can now launch 'Pass Keyboard Control' from your application launcher (rofi/walker)"
}

# Uninstall
uninstall() {
    print_info "Uninstalling Pass CLI with Keyboard Total Control..."
    
    read -p "Remove system-wide installation? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo pip uninstall -y pass-cli-with-keyboard-total-control || true
        sudo rm -f /usr/share/applications/pass-kb.desktop
        if command -v update-desktop-database &> /dev/null; then
            sudo update-desktop-database /usr/share/applications
        fi
        print_success "System-wide installation removed"
    fi
    
    read -p "Remove user installation? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pip uninstall -y pass-cli-with-keyboard-total-control || true
        rm -f ~/.local/share/applications/pass-kb.desktop
        if command -v update-desktop-database &> /dev/null; then
            update-desktop-database ~/.local/share/applications 2>/dev/null || true
        fi
        print_success "User installation removed"
    fi
    
    print_success "Uninstall completed!"
}

# Show menu
show_menu() {
    echo ""
    echo "╔═══════════════════════════════════════════╗"
    echo "║  Pass KB Installation Menu (AI-generated)║"
    echo "╚═══════════════════════════════════════════╝"
    echo ""
    echo "1) Install system-wide (requires sudo)"
    echo "2) Install for current user only"
    echo "3) Uninstall"
    echo "4) Check prerequisites"
    echo "5) Exit"
    echo ""
    read -p "Choose an option [1-5]: " choice
    
    case $choice in
        1)
            check_prerequisites
            install_system
            ;;
        2)
            check_prerequisites
            install_user
            ;;
        3)
            uninstall
            ;;
        4)
            check_prerequisites
            ;;
        5)
            print_info "Goodbye!"
            exit 0
            ;;
        *)
            print_error "Invalid option"
            show_menu
            ;;
    esac
}

# Main
main() {
    echo ""
    echo "╔═══════════════════════════════════════════════╗"
    echo "║ Pass KB Installer v1.0.0 (AI-generated code) ║"
    echo "╚═══════════════════════════════════════════════╝"
    echo ""
    
    # If arguments provided, use them
    case "$1" in
        --system)
            check_prerequisites
            install_system
            ;;
        --user)
            check_prerequisites
            install_user
            ;;
        --uninstall)
            uninstall
            ;;
        --check)
            check_prerequisites
            ;;
        --help|-h)
            echo "Usage: $0 [OPTION]"
            echo ""
            echo "Options:"
            echo "  --system      Install system-wide (requires sudo)"
            echo "  --user        Install for current user only"
            echo "  --uninstall   Uninstall Pass Suite"
            echo "  --check       Check prerequisites"
            echo "  --help, -h    Show this help message"
            echo ""
            echo "If no option is provided, an interactive menu will be shown."
            exit 0
            ;;
        "")
            show_menu
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
}

main "$@"
