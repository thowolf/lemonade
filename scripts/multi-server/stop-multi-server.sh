#!/bin/bash

# stop-multi-server.sh
# Stop all running Lemonade Server instances

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$SCRIPT_DIR/pids"
FORCE_KILL=false
TARGET_PORT=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE_KILL=true
            shift
            ;;
        --port)
            TARGET_PORT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--force] [--port PORT]"
            exit 1
            ;;
    esac
done

# Helper functions
print_color() {
    local color=$1
    shift
    echo -e "${color}$@${NC}"
}

stop_server() {
    local pid_file=$1
    local server_port=$2
    
    if [[ ! -f "$pid_file" ]]; then
        print_color "$YELLOW" "⚠️  No PID file found for port $server_port"
        return 1
    fi
    
    local pid=$(cat "$pid_file")
    
    if ! kill -0 "$pid" 2>/dev/null; then
        print_color "$YELLOW" "⚠️  Server on port $server_port not running (PID: $pid)"
        rm -f "$pid_file"
        return 1
    fi
    
    print_color "$BLUE" "Stopping server on port $server_port (PID: $pid)..."
    
    # Try graceful shutdown first
    kill -TERM "$pid" 2>/dev/null
    
    # Wait up to 5 seconds for graceful shutdown
    local waited=0
    while kill -0 "$pid" 2>/dev/null && [[ $waited -lt 50 ]]; do
        sleep 0.1
        waited=$((waited + 1))
    done
    
    # Force kill if still running
    if kill -0 "$pid" 2>/dev/null; then
        if [[ "$FORCE_KILL" == true ]]; then
            print_color "$YELLOW" "  Force killing process..."
            kill -9 "$pid" 2>/dev/null
            sleep 0.2
        else
            print_color "$YELLOW" "  ⚠️  Process still running after graceful shutdown. Use --force to kill."
            return 1
        fi
    fi
    
    # Verify process is dead
    if kill -0 "$pid" 2>/dev/null; then
        print_color "$RED" "  ❌ Failed to stop process"
        return 1
    fi
    
    # Remove PID file
    rm -f "$pid_file"
    print_color "$GREEN" "  ✓ Stopped successfully"
    return 0
}

# Main execution
print_color "$BLUE" "=== Lemonade Multi-Server Stopper ==="
echo

if [[ ! -d "$PID_DIR" ]]; then
    print_color "$YELLOW" "No PID directory found. No servers to stop."
    exit 0
fi

# Get all PID files
if [[ -n "$TARGET_PORT" ]]; then
    PID_FILES=("$PID_DIR/server-$TARGET_PORT.pid")
    if [[ ! -f "${PID_FILES[0]}" ]]; then
        print_color "$YELLOW" "No server found on port $TARGET_PORT"
        exit 0
    fi
else
    mapfile -t PID_FILES < <(find "$PID_DIR" -name "server-*.pid" 2>/dev/null)
fi

if [[ ${#PID_FILES[@]} -eq 0 ]]; then
    print_color "$YELLOW" "No running servers found."
    exit 0
fi

print_color "$BLUE" "Found ${#PID_FILES[@]} server(s) to stop"
echo

# Stop each server
STOPPED_COUNT=0
for pid_file in "${PID_FILES[@]}"; do
    if [[ ! -f "$pid_file" ]]; then
        continue
    fi
    
    server_port=$(basename "$pid_file" | sed 's/server-\(.*\)\.pid/\1/')
    
    if stop_server "$pid_file" "$server_port"; then
        STOPPED_COUNT=$((STOPPED_COUNT + 1))
    fi
    echo
done

# Summary
print_color "$BLUE" "=== Summary ==="
print_color "$GREEN" "Stopped $STOPPED_COUNT of ${#PID_FILES[@]} server(s)"
