#!/bin/bash

# SAMFMS HTTPS Test Script
# This script tests if HTTPS is working correctly with Caddy

echo "🧪 Testing HTTPS setup for SAMFMS..."
echo ""

# Test 1: Check if Caddy is running
echo "1️⃣ Checking if Caddy container is running..."
if docker compose ps caddy | grep -q "Up"; then
    echo "✅ Caddy container is running"
else
    echo "❌ Caddy container is not running"
    echo "   Run: docker compose up -d caddy"
    exit 1
fi

# Test 2: Check if ports 80 and 443 are accessible
echo ""
echo "2️⃣ Checking port accessibility..."
if curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://localhost:80 | grep -q "301\|302"; then
    echo "✅ Port 80 is accessible and redirecting to HTTPS"
else
    echo "❌ Port 80 is not accessible or not redirecting"
fi

if curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 -k https://localhost:443 | grep -q "200"; then
    echo "✅ Port 443 (HTTPS) is accessible"
else
    echo "❌ Port 443 (HTTPS) is not accessible"
fi

# Test 3: Test frontend access
echo ""
echo "3️⃣ Testing frontend access..."
FRONTEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 -k https://localhost/ 2>/dev/null || echo "000")
if [ "$FRONTEND_CODE" = "200" ]; then
    echo "✅ Frontend is accessible via HTTPS (Status: $FRONTEND_CODE)"
else
    echo "❌ Frontend access failed (Status: $FRONTEND_CODE)"
fi

# Test 4: Test API endpoints
echo ""
echo "4️⃣ Testing API endpoints..."
API_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 -k https://localhost/api/health 2>/dev/null || echo "000")
if [ "$API_CODE" = "200" ]; then
    echo "✅ API endpoint is accessible via HTTPS (Status: $API_CODE)"
else
    echo "❌ API endpoint test failed (Status: $API_CODE)"
fi

# Test 5: Test HTTP to HTTPS redirect
echo ""
echo "5️⃣ Testing HTTP to HTTPS redirect..."
REDIRECT_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 http://localhost 2>/dev/null || echo "000")
if [ "$REDIRECT_CODE" = "301" ] || [ "$REDIRECT_CODE" = "302" ]; then
    echo "✅ HTTP redirects to HTTPS (Status: $REDIRECT_CODE)"
else
    echo "❌ HTTP redirect test failed (Status: $REDIRECT_CODE)"
fi

# Test 6: Check SSL certificate type
echo ""
echo "6️⃣ Checking SSL certificate..."
if command -v openssl &> /dev/null; then
    CERT_INFO=$(echo | timeout 10 openssl s_client -connect localhost:443 2>/dev/null | openssl x509 -noout -issuer 2>/dev/null || echo "")
    if echo "$CERT_INFO" | grep -q "Caddy Local CA"; then
        echo "✅ Caddy self-signed certificate is active"
    elif echo "$CERT_INFO" | grep -q "issuer"; then
        echo "⚠️  SSL certificate found:"
        echo "   $CERT_INFO"
    else
        echo "❌ No SSL certificate found or connection failed"
    fi
else
    echo "⚠️  OpenSSL not available - cannot check certificate details"
fi

echo ""
echo "📋 Test Summary:"
echo "   Frontend (HTTPS): https://localhost/"
echo "   API (HTTPS): https://localhost/api/"
echo "   HTTP redirect: http://localhost → https://localhost"
echo ""
echo "📊 Status Codes:"
echo "   Frontend: $FRONTEND_CODE"
echo "   API: $API_CODE"
echo "   HTTP Redirect: $REDIRECT_CODE"
echo ""
echo "� Useful commands:"
echo "   View Caddy logs: docker compose logs caddy"
echo "   View all logs: docker compose logs"
echo "   Restart Caddy: docker compose restart caddy"
echo ""
echo "� Note: Browsers will show security warnings for self-signed certificates."
echo "   This is normal. Click 'Advanced' → 'Proceed to localhost (unsafe)'"
