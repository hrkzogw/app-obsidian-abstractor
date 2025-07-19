#!/usr/bin/env bash
# Obsidian Abstractor - Run Script for Mac/Linux
# This script sets up the environment and runs the application

# Enable strict error handling
set -euo pipefail

# Get the absolute path of this script (works even when called from other directories)
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
cd "$SCRIPT_DIR"

# Virtual environment path
VENV_PATH="$SCRIPT_DIR/venv"

# Function to print colored output
print_info() {
    echo -e "\033[0;36m$1\033[0m"
}

print_success() {
    echo -e "\033[0;32m$1\033[0m"
}

print_warning() {
    echo -e "\033[0;33m$1\033[0m"
}

print_error() {
    echo -e "\033[0;31m$1\033[0m"
}

# Function to check Python version
check_python_version() {
    local python_cmd="$1"
    local version=$("$python_cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    local major=$(echo "$version" | cut -d. -f1)
    local minor=$(echo "$version" | cut -d. -f2)
    
    # Check minimum version (3.9)
    if [ "$major" -lt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -lt 9 ]); then
        return 1
    fi
    
    # Warn if less than 3.11
    if [ "$major" -eq 3 ] && [ "$minor" -lt 11 ]; then
        print_warning "Warning: Python $version detected. Python 3.11+ recommended for better performance."
    else
        print_success "Python $version ✓"
    fi
    
    return 0
}

# Function to find suitable Python command
find_python() {
    # Try Python commands in order of preference (newer versions first)
    for cmd in python3.12 python3.11 python3.10 python3.9 python3 python; do
        if command -v "$cmd" &> /dev/null; then
            if check_python_version "$cmd"; then
                echo "$cmd"
                return 0
            fi
        fi
    done
    
    return 1
}

# Check if virtual environment exists
if [ -d "$VENV_PATH" ]; then
    # Activate existing virtual environment
    source "$VENV_PATH/bin/activate"
    print_info "Using existing virtual environment"
else
    # Find suitable Python
    print_info "Searching for Python 3.9+..."
    PYTHON=$(find_python)
    
    if [ -z "$PYTHON" ]; then
        print_error "Error: Python 3.9 or later is required."
        print_error "Please install Python from: https://www.python.org/downloads/"
        exit 1
    fi
    
    # Create virtual environment
    print_info "Creating virtual environment..."
    "$PYTHON" -m venv "$VENV_PATH"
    
    if [ $? -ne 0 ]; then
        print_error "Error: Failed to create virtual environment"
        exit 1
    fi
    
    # Activate virtual environment
    source "$VENV_PATH/bin/activate"
    
    # Upgrade pip
    print_info "Upgrading pip..."
    python -m pip install --upgrade pip --quiet
    
    # Install dependencies
    print_info "Installing dependencies..."
    if [ -f "pyproject.toml" ]; then
        pip install -e . --quiet
        if [ $? -ne 0 ]; then
            print_error "Error: Failed to install dependencies"
            print_error "Please check pyproject.toml and try again"
            exit 1
        fi
    else
        print_error "Error: pyproject.toml not found"
        print_error "This may indicate an incomplete installation"
        exit 1
    fi
    
    print_success "Setup complete!"
fi

# Check if config exists
if [ ! -f "config/config.yaml" ]; then
    if [ -f "config/config.yaml.example" ]; then
        print_warning ""
        print_warning "No configuration file found."
        print_warning "Please copy config/config.yaml.example to config/config.yaml"
        print_warning "and configure your Google AI API key."
        print_warning ""
        print_warning "To get an API key, visit:"
        print_warning "https://makersuite.google.com/app/apikey"
        exit 1
    fi
fi

# Set PYTHONPATH to include current directory
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}${SCRIPT_DIR}"

# Check if src directory exists
if [ ! -d "${SCRIPT_DIR}/src" ]; then
    print_error "Error: src directory not found at ${SCRIPT_DIR}/src"
    print_error "This may indicate an incomplete installation."
    print_error "Please run the installer again."
    exit 1
fi

# Check if src/main.py exists
if [ ! -f "${SCRIPT_DIR}/src/main.py" ]; then
    print_error "Error: src/main.py not found"
    print_error "This may indicate an incomplete installation."
    exit 1
fi

# Run the main application
# Pass all arguments to the script
exec python -m src.main "$@"