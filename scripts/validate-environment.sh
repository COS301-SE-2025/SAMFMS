#!/bin/bash
# Environment Validation Script for SAMFMS
# Validates configuration before starting services

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ SUCCESS: $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  INFO: $1${NC}"
}

print_section() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

# Function to check if required environment variables are set
check_required_vars() {
    local error_count=0
    local required_vars=(
        "JWT_SECRET_KEY"
        "MONGODB_USERNAME"
        "MONGODB_PASSWORD"
        "REACT_APP_DOMAIN"
    )
    
    print_section "Required Environment Variables"
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            print_error "Required variable $var is not set"
            ((error_count++))
        else
            # Check for default/insecure values
            case $var in
                "JWT_SECRET_KEY")
                    local var_value="${!var}"
                    if [[ "$var_value" =~ ^(your-secret-key|change|test|dev) ]] || [ ${#var_value} -lt 32 ]; then
                        print_warning "$var appears to be using a default or weak value"
                    else
                        print_success "$var is properly configured"
                    fi
                    ;;
                "MONGODB_PASSWORD")
                    if [[ "${!var}" =~ ^(change_this|password|admin|test) ]]; then
                        print_warning "$var appears to be using a default password"
                    else
                        print_success "$var is configured"
                    fi
                    ;;
                *)
                    print_success "$var is set"
                    ;;
            esac
        fi
    done
    
    return $error_count
}

# Function to validate email configuration
check_email_config() {
    print_section "Email Configuration"
    
    if [ -z "$SMTP_SERVER" ] || [ -z "$SMTP_USERNAME" ] || [ -z "$SMTP_PASSWORD" ]; then
        print_warning "Email configuration is incomplete. Email features may not work."
        return 1
    else
        print_success "Email configuration appears complete"
        
        # Check for common email providers
        case "$SMTP_SERVER" in
            *gmail*)
                if [ "$SMTP_PORT" != "587" ]; then
                    print_warning "Gmail typically uses port 587 for SMTP"
                fi
                ;;
            *outlook*|*hotmail*)
                if [ "$SMTP_PORT" != "587" ]; then
                    print_warning "Outlook/Hotmail typically uses port 587 for SMTP"
                fi
                ;;
        esac
        
        return 0
    fi
}

# Function to check database configuration
check_database_config() {
    print_section "Database Configuration"
    
    # Check MongoDB URL format
    if [[ ! "$MONGODB_URL" =~ ^mongodb:// ]]; then
        print_error "MONGODB_URL should start with 'mongodb://'"
        return 1
    fi
    
    # Check if using single instance (recommended)
    if [ "$MONGODB_URL" = "mongodb://mongodb:27017" ]; then
        print_success "Using single MongoDB instance (recommended)"
    else
        print_warning "Custom MongoDB URL detected. Ensure it's properly configured."
    fi
    
    # Check database names
    local db_vars=(
        "DATABASE_CORE"
        "DATABASE_GPS" 
        "DATABASE_SECURITY"
        "DATABASE_USERS"
        "DATABASE_VEHICLES"
    )
    
    for db_var in "${db_vars[@]}"; do
        if [ -n "${!db_var}" ]; then
            print_success "$db_var: ${!db_var}"
        else
            print_warning "$db_var is not set, will use default"
        fi
    done
    
    return 0
}

# Function to check service URLs
check_service_urls() {
    print_section "Service URLs"
    
    if [[ "$REACT_APP_API_BASE_URL" =~ ^https:// ]]; then
        print_success "API base URL uses HTTPS"
    else
        print_warning "API base URL should use HTTPS in production"
    fi
    
    # Extract port from URL
    if [[ "$REACT_APP_API_BASE_URL" =~ :([0-9]+) ]]; then
        local api_port="${BASH_REMATCH[1]}"
        if [ "$api_port" = "$NGINX_HTTPS_PORT" ]; then
            print_success "API URL port matches nginx HTTPS port"
        else
            print_warning "API URL port ($api_port) doesn't match nginx HTTPS port ($NGINX_HTTPS_PORT)"
        fi
    fi
    
    return 0
}

# Function to check for security issues
check_security() {
    print_section "Security Configuration"
    
    local security_issues=0
    
    # Check for default passwords
    if [ "$RABBITMQ_PASSWORD" = "guest" ]; then
        print_warning "RabbitMQ is using default password 'guest'"
        ((security_issues++))
    fi
    
    if [ "$MONGODB_PASSWORD" = "change_this_password_in_production" ]; then
        print_error "MongoDB is using the default placeholder password"
        ((security_issues++))
    fi
    
    # Check JWT secret strength
    if [ ${#JWT_SECRET_KEY} -lt 32 ]; then
        print_error "JWT secret key should be at least 32 characters long"
        ((security_issues++))
    else
        print_success "JWT secret key length is adequate"
    fi
    
    # Check environment
    if [ "$ENVIRONMENT" = "production" ] && [ "$DEBUG" = "true" ]; then
        print_warning "Debug mode is enabled in production environment"
        ((security_issues++))
    fi
    
    return $security_issues
}

# Function to validate directory structure
check_directories() {
    print_section "Directory Structure"
    
    local required_dirs=(
        "./Core"
        "./Sblocks/security"
        "./Sblocks/vehicle_maintenance"
        "./Dblocks/users"
        "./Frontend/samfms"
        "./scripts"
        "./ssl-certs"
        "./certbot"
    )
    
    local missing_dirs=0
    
    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            print_success "Directory $dir exists"
        else
            print_error "Missing directory: $dir"
            ((missing_dirs++))
        fi
    done
    
    return $missing_dirs
}

# Function to check Docker requirements
check_docker() {
    print_section "Docker Requirements"
    
    if command -v docker >/dev/null 2>&1; then
        print_success "Docker is installed"
        local docker_version=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
        print_info "Docker version: $docker_version"
    else
        print_error "Docker is not installed or not in PATH"
        return 1
    fi
    
    if command -v docker-compose >/dev/null 2>&1; then
        print_success "Docker Compose is installed"
        local compose_version=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
        print_info "Docker Compose version: $compose_version"
    else
        print_error "Docker Compose is not installed or not in PATH"
        return 1
    fi
    
    return 0
}

# Main validation function
main() {
    print_info "Starting SAMFMS Environment Validation..."
    echo ""
    
    # Load environment file
    if [ -f ".env" ]; then
        print_info "Loading environment from .env file"
        source .env
    else
        print_error "No .env file found. Please create one based on .env.example"
        exit 1
    fi
    
    local total_errors=0
    local total_warnings=0
    
    # Run all checks
    check_docker || ((total_errors++))
    check_directories || ((total_errors++))
    check_required_vars || ((total_errors++))
    check_database_config || ((total_errors++))
    check_service_urls || ((total_warnings++))
    check_email_config || ((total_warnings++))
    check_security || ((total_errors++))
    
    # Run port validation if script exists
    if [ -f "./scripts/validate-ports.sh" ]; then
        print_section "Port Validation"
        if ./scripts/validate-ports.sh; then
            print_success "Port validation passed"
        else
            print_error "Port validation failed"
            ((total_errors++))
        fi
    fi
    
    # Final summary
    print_section "Validation Summary"
    
    if [ $total_errors -eq 0 ]; then
        print_success "✅ Environment validation passed!"
        if [ $total_warnings -gt 0 ]; then
            print_warning "⚠️  $total_warnings warning(s) found - review recommended"
        fi
        print_info "You can now start the services with: docker-compose up -d"
        exit 0
    else
        print_error "❌ Environment validation failed with $total_errors error(s)"
        if [ $total_warnings -gt 0 ]; then
            print_warning "⚠️  $total_warnings warning(s) also found"
        fi
        print_info "Please fix the errors above before starting the services."
        exit 1
    fi
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
