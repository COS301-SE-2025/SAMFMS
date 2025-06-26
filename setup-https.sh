#!/bin/bash

# HTTPS Setup Script for SAMFMS
# This script sets up HTTPS with Let's Encrypt SSL certificates using Nginx reverse proxy

set -e

echo "🚀 SAMFMS HTTPS Setup Script"
echo "=============================="

# Configuration
DOMAIN="capstone-samfms.dns.net.za"
EMAIL="admin@capstone-samfms.dns.net.za"  # Change this to your email
STAGING=0  # Set to 1 for testing to avoid rate limits

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker and Docker Compose are installed
check_requirements() {
    print_status "Checking requirements..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_status "✅ Requirements check passed"
}

# Generate DH parameters
generate_dhparam() {
    if [ ! -f "./dhparam/dhparam.pem" ]; then
        print_status "Generating DH parameters... (this may take a while)"
        mkdir -p ./dhparam
        openssl dhparam -out ./dhparam/dhparam.pem 2048
        print_status "✅ DH parameters generated"
    else
        print_status "✅ DH parameters already exist"
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    mkdir -p ./certbot/conf
    mkdir -p ./certbot/www
    mkdir -p ./dhparam
    print_status "✅ Directories created"
}

# Download recommended TLS parameters
download_tls_params() {
    print_status "Downloading recommended TLS parameters..."
    
    if [ ! -e "./certbot/conf/options-ssl-nginx.conf" ] || [ ! -e "./certbot/conf/ssl-dhparams.pem" ]; then
        mkdir -p "./certbot/conf"
        curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "./certbot/conf/options-ssl-nginx.conf"
        curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "./certbot/conf/ssl-dhparams.pem"
        print_status "✅ TLS parameters downloaded"
    else
        print_status "✅ TLS parameters already exist"
    fi
}

# Stop existing services
stop_services() {
    print_status "Stopping existing services..."
    docker-compose down 2>/dev/null || true
    print_status "✅ Services stopped"
}

# Start basic services (without SSL)
start_basic_services() {
    print_status "Starting basic services..."
    docker-compose up -d rabbitmq redis mongodb_core mongodb_gps mongodb_trip_planning mongodb_vehicle_maintenance mongodb_security mongodb_users mongodb_vehicles mongodb_management
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 30
    
    docker-compose up -d security_service management_service gps_service trip_planning_service vehicle_maintenance_service utilities_service users_dblock vehicles_dblock gps_dblock mcore frontend
    
    # Wait for all services
    print_status "Waiting for all services to start..."
    sleep 60
    
    print_status "✅ Basic services started"
}

# Create self-signed SSL certificates
create_ssl_certificates() {
    print_status "Creating SSL certificates..."
    
    if [ ! -f "./ssl-certs/samfms-selfsigned.crt" ] || [ ! -f "./ssl-private/samfms-selfsigned.key" ]; then
        mkdir -p ./ssl-certs ./ssl-private
        
        print_status "Generating self-signed SSL certificate..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
          -keyout ssl-private/samfms-selfsigned.key \
          -out ssl-certs/samfms-selfsigned.crt \
          -subj "/C=ZA/ST=Gauteng/L=Pretoria/O=SAMFMS/CN=capstone-samfms.dns.net.za"
        
        print_status "✅ SSL certificates created"
    else
        print_status "✅ SSL certificates already exist"
    fi
}

# Start HTTPS services
start_https_services() {
    print_status "Starting HTTPS services..."
    docker-compose -f docker-compose.yml -f docker-compose.ssl.yml up -d nginx
    
    # Wait for nginx to start
    sleep 10
    print_status "✅ HTTPS services started"
}

# Test HTTPS
test_https() {
    print_status "Testing HTTPS connection..."
    
    # Wait a moment for services to settle
    sleep 10
    
    # Test HTTPS endpoint locally
    if curl -k -s -o /dev/null -w "%{http_code}" https://localhost:21024 | grep -q "200\|301\|302"; then
        print_status "✅ HTTPS is working!"
        print_status "🎉 Your site is now available at: https://localhost:21024"
    else
        print_warning "HTTPS test failed. Please check the logs."
        print_status "You can check logs with: docker-compose -f docker-compose.yml -f docker-compose.ssl.yml logs nginx"
    fi
}

# Main execution
main() {
    echo "Starting HTTPS setup for $DOMAIN..."
    echo "Mode: Self-signed certificates (for custom ports)"
    echo ""
    
    read -p "Continue with HTTPS setup? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Setup cancelled."
        exit 0
    fi
    
    check_requirements
    create_directories
    generate_dhparam
    stop_services
    start_basic_services
    create_ssl_certificates
    start_https_services
    test_https
    
    echo ""
    print_status "🎉 HTTPS setup completed successfully!"
    print_status "Your SAMFMS application is now available at: https://$DOMAIN:21024"
    print_status ""
    print_status "Access URLs:"
    print_status "- Frontend: https://$DOMAIN:21024"
    print_status "- API: https://$DOMAIN:21024/api"
    print_status "- Local Frontend: https://localhost:21024"
    print_status "- Local API: https://localhost:21024/api"
    print_status ""
    print_status "Note: Self-signed certificates will show browser warnings"
    print_status "To avoid warnings, add certificate to browser's trusted certificates"
    print_status ""
    print_status "To manage the services:"
    print_status "- View logs: docker-compose -f docker-compose.yml -f docker-compose.ssl.yml logs"
    print_status "- Stop services: docker-compose -f docker-compose.yml -f docker-compose.ssl.yml down"
    print_status "- Restart services: docker-compose -f docker-compose.yml -f docker-compose.ssl.yml up -d"
}

# Run main function
main "$@"
