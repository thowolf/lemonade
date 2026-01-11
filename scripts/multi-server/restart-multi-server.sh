#!/bin/bash

# restart-multi-server.sh
# Restart all or specific Lemonade Server instances

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORCE_KILL=false
TARGET_PORT=""
CONFIG_FILE="$SCRIPT_DIR/config/example-config.json"

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
        --config)
            CONFIG_FILE="$2"
            shift 2
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

# Main execution
print_color "$BLUE" "=== Lemonade Multi-Server Restart ==="
echo

# Step 1: Stop servers
print_color "$BLUE" "Step 1: Stopping servers..."
echo

STOP_ARGS=()
if [[ -n "$TARGET_PORT" ]]; then
    STOP_ARGS+=(--port "$TARGET_PORT")
fi
if [[ "$FORCE_KILL" == true ]]; then
    STOP_ARGS+=(--force)
fi

"$SCRIPT_DIR/stop-multi-server.sh" "${STOP_ARGS[@]}"

if [[ $? -ne 0 ]]; then
    print_color "$RED" "Failed to stop servers"
    exit 1
fi

# Wait a moment for cleanup
sleep 2

# Step 2: Start servers
echo
print_color "$BLUE" "Step 2: Starting servers..."
echo

"$SCRIPT_DIR/start-multi-server.sh" "$CONFIG_FILE"

if [[ $? -ne 0 ]]; then
    print_color "$RED" "Failed to start servers"
    exit 1
fi

echo
print_color "$GREEN" "=== Restart Complete ==="
