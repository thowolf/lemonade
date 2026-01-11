#!/bin/bash

# start-multi-server.sh
# Start multiple Lemonade Server instances based on JSON configuration

set -e

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
PID_DIR="$SCRIPT_DIR/pids"
CONFIG_FILE="${1:-$SCRIPT_DIR/config/example-config.json}"
FORCE_START=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE_START=true
            shift
            ;;
        *)
            CONFIG_FILE="$1"
            shift
            ;;
    esac
done

# Helper functions
print_color() {
    local color=$1
    shift
    echo -e "${color}$@${NC}"
}

check_port_available() {
    local port=$1
    if command -v nc >/dev/null 2>&1; then
        ! nc -z localhost "$port" 2>/dev/null
    elif command -v lsof >/dev/null 2>&1; then
        ! lsof -Pi ":$port" -sTCP:LISTEN -t >/dev/null 2>&1
    else
        # Fallback: try to bind
        (echo >/dev/tcp/localhost/$port) 2>/dev/null && return 1 || return 0
    fi
}

find_lemonade_server() {
    # Check common installation paths
    local paths=(
        "$HOME/.local/bin/lemonade-router"
        "/usr/local/bin/lemonade-router"
        "/usr/bin/lemonade-router"
    )
    
    for path in "${paths[@]}"; do
        if [[ -x "$path" ]]; then
            echo "$path"
            return 0
        fi
    done
    
    # Check PATH
    if command -v lemonade-router >/dev/null 2>&1; then
        command -v lemonade-router
        return 0
    fi
    
    print_color "$RED" "Error: lemonade-router not found"
    exit 1
}

# Main execution
print_color "$BLUE" "=== Lemonade Multi-Server Starter ==="
echo

# Validate config file
if [[ ! -f "$CONFIG_FILE" ]]; then
    print_color "$RED" "Error: Configuration file not found: $CONFIG_FILE"
    exit 1
fi

print_color "$BLUE" "Loading configuration: $CONFIG_FILE"

# Ensure jq is available
if ! command -v jq >/dev/null 2>&1; then
    print_color "$RED" "Error: jq is required but not installed"
    print_color "$YELLOW" "Install with: sudo apt-get install jq (Ubuntu/Debian)"
    exit 1
fi

# Parse configuration
SERVER_COUNT=$(jq '.servers | length' "$CONFIG_FILE")
if [[ $SERVER_COUNT -eq 0 ]]; then
    print_color "$RED" "Error: No servers defined in configuration"
    exit 1
fi

print_color "$BLUE" "Found $SERVER_COUNT server(s) to start"
echo

# Find lemonade-server executable
LEMONADE_EXE=$(find_lemonade_server)
print_color "$BLUE" "Using: $LEMONADE_EXE"
echo

# Ensure directories exist
mkdir -p "$LOG_DIR" "$PID_DIR"

# Check for port conflicts
declare -a PORT_CONFLICTS=()
for i in $(seq 0 $((SERVER_COUNT - 1))); do
    SERVER_NAME=$(jq -r ".servers[$i].name" "$CONFIG_FILE")
    SERVER_PORT=$(jq -r ".servers[$i].port" "$CONFIG_FILE")
    PID_FILE="$PID_DIR/server-$SERVER_PORT.pid"
    
    # Check if already running
    if [[ -f "$PID_FILE" ]]; then
        EXISTING_PID=$(cat "$PID_FILE")
        if kill -0 "$EXISTING_PID" 2>/dev/null; then
            print_color "$YELLOW" "⚠️  Server '$SERVER_NAME' already running (PID: $EXISTING_PID, Port: $SERVER_PORT)"
            PORT_CONFLICTS+=("$i")
            continue
        fi
    fi
    
    # Check port availability
    if [[ "$FORCE_START" != true ]] && ! check_port_available "$SERVER_PORT"; then
        print_color "$RED" "❌ Port $SERVER_PORT is already in use (server: $SERVER_NAME)"
        PORT_CONFLICTS+=("$i")
    fi
done

if [[ ${#PORT_CONFLICTS[@]} -gt 0 ]] && [[ "$FORCE_START" != true ]]; then
    echo
    print_color "$RED" "❌ Cannot start servers due to port conflicts or already running instances."
    print_color "$YELLOW" "   Use --force to skip checks, or stop conflicting servers first."
    exit 1
fi

# Start each server
declare -a STARTED_SERVERS=()
for i in $(seq 0 $((SERVER_COUNT - 1))); do
    # Skip if in conflict list
    if [[ " ${PORT_CONFLICTS[@]} " =~ " $i " ]]; then
        continue
    fi
    
    SERVER_NAME=$(jq -r ".servers[$i].name" "$CONFIG_FILE")
    SERVER_PORT=$(jq -r ".servers[$i].port" "$CONFIG_FILE")
    SERVER_MODEL=$(jq -r ".servers[$i].model" "$CONFIG_FILE")
    SERVER_HOST=$(jq -r ".servers[$i].host // \"localhost\"" "$CONFIG_FILE")
    SERVER_BACKEND=$(jq -r ".servers[$i].llamacpp_backend // \"vulkan\"" "$CONFIG_FILE")
    SERVER_LOG_LEVEL=$(jq -r ".servers[$i].log_level // \"info\"" "$CONFIG_FILE")
    SERVER_MAX_MODELS=$(jq -r ".servers[$i].max_loaded_models // \"1 1 1 1\"" "$CONFIG_FILE")
    SERVER_EXTRA_ARGS=$(jq -r ".servers[$i].extra_args // \"\"" "$CONFIG_FILE")
    
    print_color "$GREEN" "Starting '$SERVER_NAME' on port $SERVER_PORT..."
    
    # Prepare log file
    LOG_FILE="$LOG_DIR/server-$SERVER_PORT.log"
    PID_FILE="$PID_DIR/server-$SERVER_PORT.pid"
    
    {
        echo "=== Server started at $(date '+%Y-%m-%d %H:%M:%S') ==="
        echo "Model: $SERVER_MODEL"
        echo "Port: $SERVER_PORT"
        echo "Backend: $SERVER_BACKEND"
        echo
    } >> "$LOG_FILE"
    
    # Build command
    CMD="$LEMONADE_EXE serve --host $SERVER_HOST --port $SERVER_PORT --log-level $SERVER_LOG_LEVEL --max-loaded-models $SERVER_MAX_MODELS"
    
    if [[ -n "$SERVER_BACKEND" ]]; then
        CMD="$CMD --llamacpp-backend $SERVER_BACKEND"
    fi
    
    if [[ -n "$SERVER_EXTRA_ARGS" ]]; then
        CMD="$CMD $SERVER_EXTRA_ARGS"
    fi
    
    # Start the process with nohup
    nohup $CMD >> "$LOG_FILE" 2>&1 &
    SERVER_PID=$!
    
    # Save PID
    echo "$SERVER_PID" > "$PID_FILE"
    
    print_color "$GREEN" "  ✓ Started with PID $SERVER_PID"
    print_color "$BLUE" "  ✓ Log: $LOG_FILE"
    print_color "$BLUE" "  ✓ Endpoint: http://$SERVER_HOST:$SERVER_PORT"
    echo
    
    STARTED_SERVERS+=("$SERVER_NAME|$SERVER_PORT|$SERVER_PID|$SERVER_MODEL")
    
    # Small delay between starts
    sleep 0.5
done

# Summary
print_color "$BLUE" "=== Summary ==="
print_color "$GREEN" "Started ${#STARTED_SERVERS[@]} server(s) successfully"
echo

for server in "${STARTED_SERVERS[@]}"; do
    IFS='|' read -r name port pid model <<< "$server"
    print_color "$GREEN" "• $name - Port $port - PID $pid"
done

if [[ ${#PORT_CONFLICTS[@]} -gt 0 ]]; then
    echo
    print_color "$YELLOW" "Skipped ${#PORT_CONFLICTS[@]} server(s) due to conflicts:"
    for idx in "${PORT_CONFLICTS[@]}"; do
        name=$(jq -r ".servers[$idx].name" "$CONFIG_FILE")
        port=$(jq -r ".servers[$idx].port" "$CONFIG_FILE")
        print_color "$YELLOW" "• $name - Port $port"
    done
fi

echo
print_color "$BLUE" "Use './stop-multi-server.sh' to stop all servers"
print_color "$BLUE" "Use './status-multi-server.sh' to check server status"
