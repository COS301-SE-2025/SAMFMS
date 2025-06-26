#!/bin/bash
# Port Validation Script for SAMFMS
# Validates that all ports are within the allocated range 21000-21050

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Port range limits
MIN_PORT=21000
MAX_PORT=21050

# Function to print colored output
print_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}WARNING: $1${NC}"
}

print_success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

print_info() {
    echo -e "INFO: $1"
}

# Function to validate a single port
validate_port() {
    local port_name=$1
    local port_value=$2
    
    if [[ ! "$port_value" =~ ^[0-9]+$ ]]; then
        print_error "$port_name has invalid value: $port_value (must be numeric)"
        return 1
    fi
    
    if [ "$port_value" -lt "$MIN_PORT" ] || [ "$port_value" -gt "$MAX_PORT" ]; then
        print_error "$port_name port $port_value is outside allocated range ($MIN_PORT-$MAX_PORT)"
        return 1
    fi
    
    print_success "$port_name: $port_value ✓"
    return 0
}

# Function to check for port conflicts
check_port_conflicts() {
    local ports=("$@")
    local unique_ports=($(printf '%s\n' "${ports[@]}" | sort -nu))
    
    if [ ${#ports[@]} -ne ${#unique_ports[@]} ]; then
        print_error "Port conflicts detected! Some ports are used multiple times."
        
        # Find duplicates
        local temp_file=$(mktemp)
        printf '%s\n' "${ports[@]}" | sort | uniq -d > "$temp_file"
        
        while read -r duplicate_port; do
            print_error "Port $duplicate_port is used multiple times"
        done < "$temp_file"
        
        rm "$temp_file"
        return 1
    fi
    
    print_success "No port conflicts detected ✓"
    return 0
}

# Main validation function
main() {
    print_info "Starting SAMFMS Port Validation..."
    print_info "Allocated port range: $MIN_PORT-$MAX_PORT"
    echo ""
    
    # Load environment file
    if [ -f ".env" ]; then
        print_info "Loading environment from .env file"
        source .env
    elif [ -f ".env.example" ]; then
        print_warning ".env file not found, using .env.example for validation"
        source .env.example
    else
        print_error "No environment file found (.env or .env.example)"
        exit 1
    fi
    
    echo ""
    print_info "Validating individual ports..."
    
    # List of all ports to validate
    local error_count=0
    local all_ports=()
    
    # Infrastructure services
    validate_port "RABBITMQ_PORT" "${RABBITMQ_PORT:-21000}" || ((error_count++))
    all_ports+=("${RABBITMQ_PORT:-21000}")
    
    validate_port "RABBITMQ_MANAGEMENT_PORT" "${RABBITMQ_MANAGEMENT_PORT:-21001}" || ((error_count++))
    all_ports+=("${RABBITMQ_MANAGEMENT_PORT:-21001}")
    
    validate_port "REDIS_EXTERNAL_PORT" "${REDIS_EXTERNAL_PORT:-21002}" || ((error_count++))
    all_ports+=("${REDIS_EXTERNAL_PORT:-21002}")
    
    validate_port "MONGODB_PORT" "${MONGODB_PORT:-21003}" || ((error_count++))
    all_ports+=("${MONGODB_PORT:-21003}")
    
    # Application services
    validate_port "CORE_PORT" "${CORE_PORT:-21004}" || ((error_count++))
    all_ports+=("${CORE_PORT:-21004}")
    
    validate_port "GPS_SERVICE_PORT" "${GPS_SERVICE_PORT:-21005}" || ((error_count++))
    all_ports+=("${GPS_SERVICE_PORT:-21005}")
    
    validate_port "TRIP_PLANNING_SERVICE_PORT" "${TRIP_PLANNING_SERVICE_PORT:-21006}" || ((error_count++))
    all_ports+=("${TRIP_PLANNING_SERVICE_PORT:-21006}")
    
    validate_port "VEHICLE_MAINTENANCE_SERVICE_PORT" "${VEHICLE_MAINTENANCE_SERVICE_PORT:-21007}" || ((error_count++))
    all_ports+=("${VEHICLE_MAINTENANCE_SERVICE_PORT:-21007}")
    
    validate_port "UTILITIES_SERVICE_PORT" "${UTILITIES_SERVICE_PORT:-21008}" || ((error_count++))
    all_ports+=("${UTILITIES_SERVICE_PORT:-21008}")
    
    validate_port "SECURITY_SERVICE_PORT" "${SECURITY_SERVICE_PORT:-21009}" || ((error_count++))
    all_ports+=("${SECURITY_SERVICE_PORT:-21009}")
    
    validate_port "MANAGEMENT_SERVICE_PORT" "${MANAGEMENT_SERVICE_PORT:-21010}" || ((error_count++))
    all_ports+=("${MANAGEMENT_SERVICE_PORT:-21010}")
    
    validate_port "MICRO_FRONTEND_SERVICE_PORT" "${MICRO_FRONTEND_SERVICE_PORT:-21011}" || ((error_count++))
    all_ports+=("${MICRO_FRONTEND_SERVICE_PORT:-21011}")
    
    # Data blocks
    validate_port "USERS_DBLOCK_PORT" "${USERS_DBLOCK_PORT:-21012}" || ((error_count++))
    all_ports+=("${USERS_DBLOCK_PORT:-21012}")
    
    validate_port "VEHICLES_DBLOCK_PORT" "${VEHICLES_DBLOCK_PORT:-21013}" || ((error_count++))
    all_ports+=("${VEHICLES_DBLOCK_PORT:-21013}")
    
    validate_port "GPS_DBLOCK_PORT" "${GPS_DBLOCK_PORT:-21014}" || ((error_count++))
    all_ports+=("${GPS_DBLOCK_PORT:-21014}")
    
    # Frontend and Nginx
    validate_port "FRONTEND_PORT" "${FRONTEND_PORT:-21015}" || ((error_count++))
    all_ports+=("${FRONTEND_PORT:-21015}")
    
    validate_port "NGINX_HTTP_PORT" "${NGINX_HTTP_PORT:-21016}" || ((error_count++))
    all_ports+=("${NGINX_HTTP_PORT:-21016}")
    
    validate_port "NGINX_HTTPS_PORT" "${NGINX_HTTPS_PORT:-21017}" || ((error_count++))
    all_ports+=("${NGINX_HTTPS_PORT:-21017}")
    
    echo ""
    print_info "Checking for port conflicts..."
    check_port_conflicts "${all_ports[@]}" || ((error_count++))
    
    echo ""
    print_info "Checking if ports are available on the system..."
    for port in "${all_ports[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            print_warning "Port $port appears to be in use on the system"
        fi
    done
    
    echo ""
    if [ $error_count -eq 0 ]; then
        print_success "✓ All port validations passed! Total ports used: ${#all_ports[@]}"
        print_info "Port range utilization: ${#all_ports[@]}/51 ports ($(( ${#all_ports[@]} * 100 / 51 ))%)"
    else
        print_error "✗ Port validation failed with $error_count error(s)"
        echo ""
        print_info "Please fix the issues above and run this script again."
        exit 1
    fi
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
