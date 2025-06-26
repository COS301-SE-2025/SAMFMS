#!/bin/bash

# SAMFMS Environment Manager
# Simplifies running the application in different environments

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default values
ENVIRONMENT="development"
ACTION="up"
SERVICES=""
DETACHED=false

usage() {
    echo "SAMFMS Environment Manager"
    echo ""
    echo "Usage: $0 [OPTIONS] [ACTION] [SERVICES...]"
    echo ""
    echo "Environments:"
    echo "  dev, development    - Development environment (minimal resources)"
    echo "  prod, production    - Production environment (full stack)"
    echo ""
    echo "Actions:"
    echo "  up                  - Start services (default)"
    echo "  down                - Stop services"
    echo "  restart             - Restart services"
    echo "  build               - Build services"
    echo "  logs                - Show logs"
    echo "  ps                  - Show running services"
    echo "  validate            - Validate configuration"
    echo ""
    echo "Options:"
    echo "  -e, --env ENV       - Environment (development|production)"
    echo "  -d, --detach        - Run in detached mode"
    echo "  -h, --help          - Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 -e development up -d"
    echo "  $0 -e production build"
    echo "  $0 logs core security"
    echo "  $0 validate"
}

validate_config() {
    local env=$1
    echo "🔍 Validating configuration for $env environment..."
    
    if [ -f "validate-config.py" ]; then
        python validate-config.py --env "$env"
    else
        echo "⚠️  Configuration validator not found. Skipping validation."
    fi
}

setup_environment() {
    local env=$1
    
    # Copy appropriate environment file
    if [ "$env" = "development" ] || [ "$env" = "dev" ]; then
        if [ -f ".env.development" ]; then
            echo "📋 Using development configuration..."
            cp .env.development .env
        else
            echo "⚠️  .env.development not found, using .env.example"
            cp .env.example .env
        fi
        COMPOSE_FILE="docker-compose.dev.yml"
        ENVIRONMENT="development"
    elif [ "$env" = "production" ] || [ "$env" = "prod" ]; then
        if [ -f ".env.production" ]; then
            echo "📋 Using production configuration..."
            cp .env.production .env
            echo "⚠️  Please review and update .env with your production values!"
        else
            echo "⚠️  .env.production not found, using .env.example"
            cp .env.example .env
        fi
        COMPOSE_FILE="docker-compose.new.yml"
        ENVIRONMENT="production"
    else
        echo "❌ Invalid environment: $env"
        echo "Valid environments: development, production"
        exit 1
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -d|--detach)
            DETACHED=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        up|down|restart|build|logs|ps|validate)
            ACTION="$1"
            shift
            break
            ;;
        *)
            echo "❌ Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Remaining arguments are services
SERVICES="$@"

# Handle validate action specially
if [ "$ACTION" = "validate" ]; then
    validate_config "$ENVIRONMENT"
    exit 0
fi

# Setup environment
setup_environment "$ENVIRONMENT"

# Validate configuration before starting
if [ "$ACTION" = "up" ] || [ "$ACTION" = "restart" ]; then
    validate_config "$ENVIRONMENT"
    if [ $? -ne 0 ]; then
        echo "❌ Configuration validation failed. Please fix the issues before proceeding."
        exit 1
    fi
fi

# Build Docker Compose command
COMPOSE_CMD="docker-compose -f $COMPOSE_FILE"

# Add detached flag if requested
DETACH_FLAG=""
if [ "$DETACHED" = true ] && [ "$ACTION" = "up" ]; then
    DETACH_FLAG="-d"
fi

# Execute the action
case $ACTION in
    up)
        echo "🚀 Starting SAMFMS in $ENVIRONMENT mode..."
        $COMPOSE_CMD up $DETACH_FLAG $SERVICES
        ;;
    down)
        echo "🛑 Stopping SAMFMS..."
        $COMPOSE_CMD down --volumes --remove-orphans
        ;;
    restart)
        echo "🔄 Restarting SAMFMS..."
        $COMPOSE_CMD restart $SERVICES
        ;;
    build)
        echo "🏗️ Building SAMFMS services..."
        $COMPOSE_CMD build $SERVICES
        ;;
    logs)
        echo "📋 Showing logs..."
        $COMPOSE_CMD logs -f $SERVICES
        ;;
    ps)
        echo "📊 Service status:"
        $COMPOSE_CMD ps
        ;;
    *)
        echo "❌ Unknown action: $ACTION"
        usage
        exit 1
        ;;
esac
