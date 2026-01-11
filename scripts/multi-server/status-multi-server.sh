#!/bin/bash

# status-multi-server.sh
# Check health status of all running Lemonade Server instances

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$SCRIPT_DIR/pids"
LOG_DIR="$SCRIPT_DIR/logs"
TARGET_PORT=""
VERBOSE=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            TARGET_PORT="$2"
            shift 2
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--port PORT] [--verbose]"
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

check_server_health() {
    local port=$1
    
    if command -v curl >/dev/null 2>&1; then
        response=$(curl -s -f "http://localhost:$port/api/v1/health" 2>/dev/null)
        if [[ $? -eq 0 ]]; then
            echo "$response"
            return 0
        fi
    elif command -v wget >/dev/null 2>&1; then
        response=$(wget -qO- "http://localhost:$port/api/v1/health" 2>/dev/null)
        if [[ $? -eq 0 ]]; then
            echo "$response"
            return 0
        fi
    fi
    
    return 1
}

get_process_uptime() {
    local pid=$1
    
    if [[ -f "/proc/$pid/stat" ]]; then
        # Linux
        local starttime=$(awk '{print $22}' /proc/$pid/stat)
        local uptime_seconds=$(awk '{print $1}' /proc/uptime)
        local hz=$(getconf CLK_TCK)
        local seconds=$(awk "BEGIN {print int($uptime_seconds - ($starttime / $hz))}")
        
        local days=$((seconds / 86400))
        local hours=$(((seconds % 86400) / 3600))
        local minutes=$(((seconds % 3600) / 60))
        local secs=$((seconds % 60))
        
        if [[ $days -gt 0 ]]; then
            echo "${days}d ${hours}h"
        elif [[ $hours -gt 0 ]]; then
            echo "${hours}h ${minutes}m"
        elif [[ $minutes -gt 0 ]]; then
            echo "${minutes}m ${secs}s"
        else
            echo "${secs}s"
        fi
    else
        echo "unknown"
    fi
}

get_process_memory() {
    local pid=$1
    
    if [[ -f "/proc/$pid/status" ]]; then
        # Linux - get VmRSS in MB
        local mem_kb=$(grep VmRSS /proc/$pid/status | awk '{print $2}')
        local mem_mb=$((mem_kb / 1024))
        echo "${mem_mb} MB"
    else
        echo "unknown"
    fi
}

# Main execution
print_color "$BLUE" "=== Lemonade Multi-Server Status ==="
echo

if [[ ! -d "$PID_DIR" ]]; then
    print_color "$YELLOW" "No PID directory found. No servers configured."
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
    print_color "$YELLOW" "No servers found."
    exit 0
fi

print_color "$BLUE" "Checking ${#PID_FILES[@]} server(s)..."
echo

# Check each server
RUNNING_COUNT=0
HEALTHY_COUNT=0

for pid_file in "${PID_FILES[@]}"; do
    if [[ ! -f "$pid_file" ]]; then
        continue
    fi
    
    server_port=$(basename "$pid_file" | sed 's/server-\(.*\)\.pid/\1/')
    
    print_color "$CYAN" "━━━ Server on Port $server_port ━━━"
    
    pid=$(cat "$pid_file")
    
    if ! kill -0 "$pid" 2>/dev/null; then
        print_color "$RED" "  Status: ❌ Not running (PID: $pid)"
        print_color "$YELLOW" "  Hint: Process may have crashed. Check logs:"
        
        log_file="$LOG_DIR/server-$server_port.log"
        if [[ -f "$log_file" ]]; then
            print_color "$YELLOW" "        $log_file"
        fi
        
        echo
        continue
    fi
    
    RUNNING_COUNT=$((RUNNING_COUNT + 1))
    
    # Process info
    uptime=$(get_process_uptime "$pid")
    memory=$(get_process_memory "$pid")
    
    print_color "$GREEN" "  Status: ✓ Running"
    print_color "$BLUE" "  PID: $pid"
    print_color "$BLUE" "  Uptime: $uptime"
    print_color "$BLUE" "  Memory: $memory"
    
    # Check health endpoint
    echo -n "  Health Check: "
    health_response=$(check_server_health "$server_port")
    
    if [[ $? -eq 0 ]]; then
        status=$(echo "$health_response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        print_color "$GREEN" "✓ Healthy ($status)"
        HEALTHY_COUNT=$((HEALTHY_COUNT + 1))
        
        if [[ "$VERBOSE" == true ]] && command -v jq >/dev/null 2>&1; then
            echo
            print_color "$CYAN" "  Loaded Models:"
            
            models=$(echo "$health_response" | jq -r '.loaded_models[]?' 2>/dev/null)
            if [[ -n "$models" ]]; then
                echo "$models" | while read -r model; do
                    print_color "$BLUE" "    • $model"
                done
            else
                print_color "$YELLOW" "    (none)"
            fi
        fi
    else
        print_color "$RED" "❌ Unhealthy"
        print_color "$RED" "  Error: Cannot reach health endpoint"
    fi
    
    echo
done

# Summary
print_color "$BLUE" "=== Summary ==="
print_color "$BLUE" "Total servers: ${#PID_FILES[@]}"

if [[ $RUNNING_COUNT -eq ${#PID_FILES[@]} ]]; then
    print_color "$GREEN" "Running: $RUNNING_COUNT"
else
    print_color "$YELLOW" "Running: $RUNNING_COUNT"
fi

if [[ $HEALTHY_COUNT -eq $RUNNING_COUNT ]]; then
    print_color "$GREEN" "Healthy: $HEALTHY_COUNT"
else
    print_color "$YELLOW" "Healthy: $HEALTHY_COUNT"
fi

if [[ $HEALTHY_COUNT -lt ${#PID_FILES[@]} ]]; then
    echo
    print_color "$YELLOW" "Use './restart-multi-server.sh' to restart failed servers"
    print_color "$YELLOW" "Use './stop-multi-server.sh' and './start-multi-server.sh' for full restart"
fi
