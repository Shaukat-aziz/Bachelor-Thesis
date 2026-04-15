#!/bin/bash
# Quick Start Script for Pentagon Photonic Crystal Simulator
# Usage: bash launch.sh [OPTIONS]

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON=${PYTHON:-python3}

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_banner() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════╗"
    echo "║  Pentagon Photonic Crystal Simulator               ║"
    echo "║  Version 1.0.0                                     ║"
    echo "╚════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_python() {
    if ! command -v $PYTHON &> /dev/null; then
        echo -e "${RED}✗ Python not found. Please install Python 3.9+${NC}"
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}"
}

check_dependencies() {
    echo -e "\n${BLUE}Checking dependencies...${NC}"
    
    MISSING=0
    
    for package in numpy matplotlib scipy; do
        if $PYTHON -c "import $package" 2>/dev/null; then
            echo -e "${GREEN}✓ $package${NC}"
        else
            echo -e "${YELLOW}✗ $package (not installed)${NC}"
            MISSING=$((MISSING + 1))
        fi
    done
    
    # Check optional packages
    for package in meep cupy torch jax; do
        if $PYTHON -c "import $package" 2>/dev/null; then
            echo -e "${GREEN}✓ $package (optional)${NC}"
        else
            echo -e "${YELLOW}◌ $package (optional, not installed)${NC}"
        fi
    done
    
    if [ $MISSING -gt 0 ]; then
        echo -e "\n${YELLOW}Missing $MISSING required package(s)${NC}"
        echo -e "Install with: pip install -r requirements.txt"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

check_gpu() {
    echo -e "\n${BLUE}Checking GPU availability...${NC}"
    
    # Check NVIDIA GPU via nvidia-smi
    if command -v nvidia-smi &> /dev/null; then
        GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
        if [ ! -z "$GPU_NAME" ]; then
            echo -e "${GREEN}✓ NVIDIA GPU detected: $GPU_NAME${NC}"
        else
            echo -e "${YELLOW}⚠ No NVIDIA GPU detected${NC}"
        fi
    fi
    
    # Check CuPy
    if $PYTHON -c "import cupy; print(cupy.cuda.Device().get_device_name().decode())" 2>/dev/null; then
        echo -e "${GREEN}✓ CuPy GPU support available${NC}"
    else
        echo -e "${YELLOW}⚠ CuPy not available (GPU acceleration disabled)${NC}"
    fi
}

show_help() {
    cat << EOF

Usage: bash launch.sh [OPTIONS]

OPTIONS:
    --help, -h       Show this help message
    --check         Check dependencies only
    --gpu           Show GPU information
    --verbose, -v   Verbose output during launch
    --debug         Run in debug mode (foreground)
    --clean         Remove temporary files before launch
    --install       Install dependencies
    --version       Show version

EXAMPLES:
    bash launch.sh                  # Launch application
    bash launch.sh --check          # Check dependencies
    bash launch.sh --gpu            # Check GPU
    bash launch.sh --debug          # Debug mode
    bash launch.sh --install        # Install dependencies

KEYBOARD SHORTCUTS IN APP:
    Ctrl+C          Quit application
    
EOF
}

install_dependencies() {
    echo -e "\n${BLUE}Installing dependencies...${NC}"
    
    if [ -f "$APP_DIR/requirements.txt" ]; then
        pip install -r "$APP_DIR/requirements.txt"
        echo -e "${GREEN}✓ Dependencies installed${NC}"
    else
        echo -e "${RED}✗ requirements.txt not found${NC}"
        exit 1
    fi
}

clean_temp_files() {
    echo -e "${BLUE}Cleaning temporary files...${NC}"
    
    find "$APP_DIR" -name "*.pyc" -delete
    find "$APP_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
    find "$APP_DIR" -name "*.pyo" -delete
    
    echo -e "${GREEN}✓ Cleanup complete${NC}"
}

launch_app() {
    echo -e "\n${BLUE}Launching Pentagon Photonic Crystal Simulator...${NC}"
    
    cd "$APP_DIR"
    
    if [ "$DEBUG" = true ]; then
        echo -e "${YELLOW}Debug mode: running in foreground${NC}"
        $PYTHON app.py
    else
        # Run in background
        nohup $PYTHON app.py > /dev/null 2>&1 &
        APP_PID=$!
        echo -e "${GREEN}✓ Application launched (PID: $APP_PID)${NC}"
        echo -e "   Check your desktop for the window"
    fi
}

# Main script
main() {
    print_banner
    
    case "${1:-launch}" in
        --help|-h)
            show_help
            ;;
        --check)
            check_python
            check_dependencies
            ;;
        --gpu)
            check_python
            check_gpu
            ;;
        --install)
            check_python
            install_dependencies
            ;;
        --clean)
            clean_temp_files
            ;;
        --version)
            echo "Pentagon Photonic Crystal Simulator v1.0.0"
            ;;
        --debug)
            DEBUG=true
            check_python
            check_dependencies
            launch_app
            ;;
        --verbose|-v)
            VERBOSE=true
            check_python
            check_dependencies
            check_gpu
            launch_app
            ;;
        launch|"")
            check_python
            check_dependencies
            launch_app
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
