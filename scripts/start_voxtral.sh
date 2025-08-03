#!/bin/bash
set -e

echo "🧠 Starting Voxtral Agentic Voice Platform"
echo "=========================================="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}[INFO]${NC} Project root: $PROJECT_ROOT"

# Check if virtual environment exists
if [[ ! -d "venv" ]]; then
    echo -e "${YELLOW}[WARNING]${NC} Virtual environment not found. Please run ./scripts/install.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if any VLLM server is already running
if curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
    echo -e "${GREEN}[SUCCESS]${NC} VLLM server is already running"
else
    echo -e "${BLUE}[INFO]${NC} No VLLM server detected, starting one..."
    
    # Try to start real VLLM server first
    echo -e "${BLUE}[INFO]${NC} Attempting to start VLLM server (CPU-compatible)..."
    python scripts/start_vllm_cpu.py &
    VLLM_SERVER_PID=$!
    
    # Wait for server to start
    echo -e "${BLUE}[INFO]${NC} Waiting for VLLM server to start..."
    VLLM_STARTED=false
    for i in {1..30}; do
        if curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
            echo -e "${GREEN}[SUCCESS]${NC} VLLM server started successfully (PID: $VLLM_SERVER_PID)"
            VLLM_STARTED=true
            break
        fi
        sleep 2
    done
    
    # If VLLM failed, fall back to mock server
    if [[ "$VLLM_STARTED" == "false" ]]; then
        echo -e "${YELLOW}[WARNING]${NC} VLLM server failed to start, falling back to mock server..."
        kill $VLLM_SERVER_PID 2>/dev/null || true
        
        python scripts/mock_vllm_server.py &
        MOCK_SERVER_PID=$!
        
        # Wait for mock server
        for i in {1..10}; do
            if curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
                echo -e "${GREEN}[SUCCESS]${NC} Mock VLLM server started (PID: $MOCK_SERVER_PID)"
                break
            fi
            sleep 1
        done
    fi
fi

# Function to cleanup on exit
cleanup() {
    echo -e "\n${BLUE}[INFO]${NC} Shutting down Voxtral platform..."
    if [[ -n "$VLLM_SERVER_PID" ]]; then
        kill $VLLM_SERVER_PID 2>/dev/null || true
    fi
    if [[ -n "$MOCK_SERVER_PID" ]]; then
        kill $MOCK_SERVER_PID 2>/dev/null || true
    fi
    # Kill any remaining processes
    pkill -f "start_vllm_cpu.py" 2>/dev/null || true
    pkill -f "mock_vllm_server.py" 2>/dev/null || true
    pkill -f "agent_main.py" 2>/dev/null || true
    pkill -f "tray_icon.py" 2>/dev/null || true
    echo -e "${GREEN}[SUCCESS]${NC} Cleanup complete"
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Check what to start
case "${1:-tray}" in
    "agent")
        echo -e "${BLUE}[INFO]${NC} Starting Voxtral agent directly..."
        python agent/agent_main.py
        ;;
    "tray")
        echo -e "${BLUE}[INFO]${NC} Starting system tray interface..."
        echo -e "${BLUE}[INFO]${NC} Right-click the tray icon to control the agent"
        
        # Try GTK tray first (better for GNOME), fallback to PyQt5
        if python -c "import gi; gi.require_version('AyatanaAppIndicator3', '0.1')" 2>/dev/null; then
            echo -e "${GREEN}[SUCCESS]${NC} Using GTK system tray (better for GNOME)"
            python scripts/voxtral_tray_gtk.py
        else
            echo -e "${YELLOW}[WARNING]${NC} GTK tray not available, using PyQt5 fallback"
            python scripts/tray_icon.py
        fi
        ;;
    "test")
        echo -e "${BLUE}[INFO]${NC} Running system tests..."
        python scripts/test_system.py
        ;;
    *)
        echo "Usage: $0 [agent|tray|test]"
        echo "  agent - Start the voice agent directly"
        echo "  tray  - Start the system tray interface (default)"
        echo "  test  - Run system tests"
        exit 1
        ;;
esac