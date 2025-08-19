#!/bin/bash

# SAMFMS HTTPS Launch Script
# This script launches SAMFMS with automatic HTTPS using Caddy

set -e

echo "🚀 Starting SAMFMS with automatic HTTPS..."

# Check if domain is configured
if [ -z "$DOMAIN" ]; then
    echo "⚠️  Warning: DOMAIN environment variable not set. Using default: capstone-samfms.dns.net.za"
    export DOMAIN="capstone-samfms.dns.net.za"
fi

# Check if email is configured  
if [ -z "$EMAIL" ]; then
    echo "⚠️  Warning: EMAIL environment variable not set. Using default: admin@${DOMAIN}"
    export EMAIL="admin@${DOMAIN}"
fi

echo "📡 Domain: $DOMAIN"
echo "📧 Email: $EMAIL"

# Update Caddyfile with the correct domain
echo "🔧 Updating Caddyfile with domain: $DOMAIN"
sed -i "s/capstone-samfms\.dns\.net\.za/$DOMAIN/g" Caddyfile
sed -i "s/admin@capstone-samfms\.dns\.net\.za/$EMAIL/g" Caddyfile

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker compose down

# Build and start services
echo "🏗️  Building and starting services..."
docker compose --env-file .env.https up --build -d

echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo "🔍 Checking service status..."
docker compose ps

echo ""
echo "✅ SAMFMS is starting up with automatic HTTPS!"
echo ""
echo "🌐 Your application will be available at:"
echo "   HTTP:  http://$DOMAIN (redirects to HTTPS)"
echo "   HTTPS: https://$DOMAIN"
echo ""
echo "📝 Logs:"
echo "   docker compose logs caddy     - Caddy (reverse proxy + SSL)"
echo "   docker compose logs frontend  - Frontend service"
echo "   docker compose logs core      - Core API service"
echo ""
echo "⚠️  Note: SSL certificates may take a few minutes to obtain on first run."
echo "   Check 'docker compose logs caddy' if you experience issues."
echo ""
echo "🔧 To customize the domain, edit the DOMAIN variable in .env.https"
echo ""

# Show Caddy logs
echo "📋 Recent Caddy logs:"
docker compose logs caddy --tail=10
