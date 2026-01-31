#!/bin/bash

# Interview Agent API Server Management Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/server.pid"
PYTHON_SCRIPT="interview_agent_api_test_version.py"

# Function to stop the server
stop_server() {
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if ps -p $OLD_PID > /dev/null 2>&1; then
            echo "Stopping server (PID: $OLD_PID)..."
            kill $OLD_PID
            sleep 1
            # Force kill if still running
            if ps -p $OLD_PID > /dev/null 2>&1; then
                kill -9 $OLD_PID
            fi
            echo "✓ Server stopped"
        else
            echo "Server process not found"
        fi
        rm -f "$PID_FILE"
    else
        # Try to find and kill by process name
        PIDS=$(pgrep -f "$PYTHON_SCRIPT")
        if [ ! -z "$PIDS" ]; then
            echo "Stopping server processes..."
            pkill -f "$PYTHON_SCRIPT"
            sleep 1
            echo "✓ Server stopped"
        else
            echo "No server process found"
        fi
    fi
}

# Function to start the server
start_server() {
    # Stop any existing server first
    stop_server
    
    echo "Starting server..."
    cd "$SCRIPT_DIR"
    python "$PYTHON_SCRIPT" &
    SERVER_PID=$!
    echo $SERVER_PID > "$PID_FILE"
    echo "✓ Server started (PID: $SERVER_PID)"
    echo "Server is running on http://localhost:8000"
    echo "Press Ctrl+C to stop"
    
    # Wait for the process
    wait $SERVER_PID
    rm -f "$PID_FILE"
}

# Function to restart the server
restart_server() {
    echo "Restarting server..."
    stop_server
    sleep 1
    start_server
}

# Main script logic
case "$1" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        if [ -f "$PID_FILE" ]; then
            OLD_PID=$(cat "$PID_FILE")
            if ps -p $OLD_PID > /dev/null 2>&1; then
                echo "Server is running (PID: $OLD_PID)"
            else
                echo "Server is not running (stale PID file)"
                rm -f "$PID_FILE"
            fi
        else
            PIDS=$(pgrep -f "$PYTHON_SCRIPT")
            if [ ! -z "$PIDS" ]; then
                echo "Server is running (PID: $PIDS)"
            else
                echo "Server is not running"
            fi
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the server"
        echo "  stop    - Stop the server"
        echo "  restart - Restart the server"
        echo "  status  - Check server status"
        exit 1
        ;;
esac
