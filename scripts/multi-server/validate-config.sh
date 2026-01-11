#!/bin/bash

# validate-config.sh
# Validate configuration file and check port availability

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config/example-config.json"
SKIP_PORT_CHECK=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-port-check)
            SKIP_PORT_CHECK=true
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
        (echo >/dev/tcp/localhost/$port) 2>/dev/null && return 1 || return 0
    fi
}

# Main execution
print_color "$BLUE" "=== Configuration Validator ==="
echo

print_color "$BLUE" "Validating: $CONFIG_FILE"
echo

# Check if file exists
if [[ ! -f "$CONFIG_FILE" ]]; then
    print_color "$RED" "Error: Configuration file not found: $CONFIG_FILE"
    exit 1
fi

print_color "$GREEN" "✓ File exists"

# Check if jq is available
if ! command -v jq >/dev/null 2>&1; then
    print_color "$RED" "Error: jq is required but not installed"
    print_color "$YELLOW" "Install with: sudo apt-get install jq (Ubuntu/Debian)"
    exit 1
fi

# Parse JSON
if ! jq empty "$CONFIG_FILE" 2>/dev/null; then
    print_color "$RED" "Error: Invalid JSON format"
    exit 1
fi

print_color "$GREEN" "✓ Valid JSON format"

# Validate required fields
if ! jq -e '.servers' "$CONFIG_FILE" >/dev/null 2>&1; then
    print_color "$RED" "Error: Missing required field: 'servers'"
    exit 1
fi

SERVER_COUNT=$(jq '.servers | length' "$CONFIG_FILE")
if [[ $SERVER_COUNT -eq 0 ]]; then
    print_color "$RED" "Error: No servers defined in 'servers' array"
    exit 1
fi

print_color "$GREEN" "✓ Required fields present"
echo

# Validate each server
print_color "$BLUE" "Validating $SERVER_COUNT server(s)..."
echo

declare -a ERRORS=()
declare -a WARNINGS=()
declare -A PORTS_SEEN=()
declare -A NAMES_SEEN=()

for i in $(seq 0 $((SERVER_COUNT - 1))); do
    SERVER_NUM=$((i + 1))
    
    print_color "$BLUE" "Server $SERVER_NUM:"
    
    # Get server fields
    SERVER_NAME=$(jq -r ".servers[$i].name // empty" "$CONFIG_FILE")
    SERVER_PORT=$(jq -r ".servers[$i].port // empty" "$CONFIG_FILE")
    SERVER_MODEL=$(jq -r ".servers[$i].model // empty" "$CONFIG_FILE")
    SERVER_BACKEND=$(jq -r ".servers[$i].llamacpp_backend // empty" "$CONFIG_FILE")
    SERVER_LOG_LEVEL=$(jq -r ".servers[$i].log_level // empty" "$CONFIG_FILE")
    SERVER_CTX_SIZE=$(jq -r ".servers[$i].ctx_size // empty" "$CONFIG_FILE")
    
    # Validate required fields
    if [[ -z "$SERVER_NAME" ]]; then
        ERRORS+=("Server $SERVER_NUM: Missing required field 'name'")
    else
        print_color "$BLUE" "  Name: $SERVER_NAME"
        
        # Check for duplicate names
        if [[ -n "${NAMES_SEEN[$SERVER_NAME]}" ]]; then
            ERRORS+=("Server $SERVER_NUM: Duplicate server name '$SERVER_NAME' (also used by server ${NAMES_SEEN[$SERVER_NAME]})")
        else
            NAMES_SEEN[$SERVER_NAME]=$SERVER_NUM
        fi
    fi
    
    if [[ -z "$SERVER_PORT" ]]; then
        ERRORS+=("Server $SERVER_NUM: Missing required field 'port'")
    else
        print_color "$BLUE" "  Port: $SERVER_PORT"
        
        # Validate port range
        if [[ $SERVER_PORT -lt 1024 ]] || [[ $SERVER_PORT -gt 65535 ]]; then
            ERRORS+=("Server $SERVER_NUM: Port $SERVER_PORT out of valid range (1024-65535)")
        fi
        
        # Check for duplicate ports
        if [[ -n "${PORTS_SEEN[$SERVER_PORT]}" ]]; then
            ERRORS+=("Server $SERVER_NUM: Duplicate port $SERVER_PORT (also used by server ${PORTS_SEEN[$SERVER_PORT]})")
        else
            PORTS_SEEN[$SERVER_PORT]=$SERVER_NUM
        fi
        
        # Check port availability
        if [[ "$SKIP_PORT_CHECK" != true ]]; then
            if check_port_available "$SERVER_PORT"; then
                print_color "$GREEN" "  Port Status: ✓ Available"
            else
                print_color "$YELLOW" "  Port Status: ⚠️  In use"
                WARNINGS+=("Server $SERVER_NUM: Port $SERVER_PORT is currently in use")
            fi
        fi
    fi
    
    if [[ -z "$SERVER_MODEL" ]]; then
        ERRORS+=("Server $SERVER_NUM: Missing required field 'model'")
    else
        print_color "$BLUE" "  Model: $SERVER_MODEL"
    fi
    
    # Validate optional fields
    if [[ -n "$SERVER_BACKEND" ]] && [[ ! "$SERVER_BACKEND" =~ ^(vulkan|rocm|cpu)$ ]]; then
        WARNINGS+=("Server $SERVER_NUM: Unknown llamacpp_backend '$SERVER_BACKEND' (expected: vulkan, rocm, cpu)")
    fi
    
    if [[ -n "$SERVER_LOG_LEVEL" ]] && [[ ! "$SERVER_LOG_LEVEL" =~ ^(debug|info|warning|error)$ ]]; then
        WARNINGS+=("Server $SERVER_NUM: Unknown log_level '$SERVER_LOG_LEVEL' (expected: debug, info, warning, error)")
    fi
    
    if [[ -n "$SERVER_CTX_SIZE" ]]; then
        if [[ $SERVER_CTX_SIZE -lt 512 ]]; then
            WARNINGS+=("Server $SERVER_NUM: ctx_size $SERVER_CTX_SIZE is very small (minimum recommended: 512)")
        fi
        if [[ $SERVER_CTX_SIZE -gt 32768 ]]; then
            WARNINGS+=("Server $SERVER_NUM: ctx_size $SERVER_CTX_SIZE is very large (may cause memory issues)")
        fi
    fi
    
    echo
done

# Summary
print_color "$BLUE" "=== Validation Summary ==="
echo

if [[ ${#ERRORS[@]} -eq 0 ]] && [[ ${#WARNINGS[@]} -eq 0 ]]; then
    print_color "$GREEN" "✓ Configuration is valid!"
    print_color "$BLUE" "  $SERVER_COUNT server(s) defined"
    print_color "$BLUE" "  All ports available"
    exit 0
fi

if [[ ${#ERRORS[@]} -gt 0 ]]; then
    print_color "$RED" "❌ Found ${#ERRORS[@]} error(s):"
    for error in "${ERRORS[@]}"; do
        print_color "$RED" "  • $error"
    done
    echo
fi

if [[ ${#WARNINGS[@]} -gt 0 ]]; then
    print_color "$YELLOW" "⚠️  Found ${#WARNINGS[@]} warning(s):"
    for warning in "${WARNINGS[@]}"; do
        print_color "$YELLOW" "  • $warning"
    done
    echo
fi

if [[ ${#ERRORS[@]} -gt 0 ]]; then
    print_color "$RED" "Fix errors before starting servers."
    exit 1
else
    print_color "$YELLOW" "Configuration has warnings but is valid. Proceed with caution."
    exit 0
fi
