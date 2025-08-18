#!/bin/bash

# SAMFMS HTTPS Test Script
# This script tests if HTTPS is working correctly

DOMAIN=${DOMAIN:-capstone-samfms.dns.net.za}

echo "🧪 Testing HTTPS setup for $DOMAIN..."
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
if curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://localhost:80 | grep -q "200\|301\|302"; then
    echo "✅ Port 80 is accessible"
else
    echo "❌ Port 80 is not accessible"
fi

if curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 -k https://localhost:443 | grep -q "200\|301\|302"; then
    echo "✅ Port 443 is accessible"
else
    echo "❌ Port 443 is not accessible"
fi

# Test 3: Check HTTP to HTTPS redirect
echo ""
echo "3️⃣ Testing HTTP to HTTPS redirect..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 http://$DOMAIN 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "✅ HTTP redirects to HTTPS (Status: $HTTP_CODE)"
elif [ "$HTTP_CODE" = "200" ]; then
    echo "⚠️  HTTP returns 200 (should redirect to HTTPS)"
else
    echo "❌ HTTP request failed (Status: $HTTP_CODE)"
    echo "   This might be normal if DNS is not configured yet"
fi

# Test 4: Check HTTPS response
echo ""
echo "4️⃣ Testing HTTPS response..."
HTTPS_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 -k https://$DOMAIN 2>/dev/null || echo "000")
if [ "$HTTPS_CODE" = "200" ]; then
    echo "✅ HTTPS is working (Status: $HTTPS_CODE)"
elif [ "$HTTPS_CODE" = "000" ]; then
    echo "❌ HTTPS connection failed"
    echo "   Check if DNS points to this server"
else
    echo "⚠️  HTTPS returned status: $HTTPS_CODE"
fi

# Test 5: Check SSL certificate
echo ""
echo "5️⃣ Checking SSL certificate..."
if command -v openssl &> /dev/null; then
    CERT_INFO=$(echo | timeout 10 openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -issuer 2>/dev/null || echo "")
    if echo "$CERT_INFO" | grep -q "Let's Encrypt"; then
        echo "✅ Let's Encrypt SSL certificate is active"
    elif echo "$CERT_INFO" | grep -q "issuer"; then
        echo "⚠️  SSL certificate found, but not from Let's Encrypt:"
        echo "   $CERT_INFO"
    else
        echo "❌ No SSL certificate found or connection failed"
    fi
else
    echo "⚠️  OpenSSL not available - cannot check certificate"
fi

# Test 6: Check Core API endpoint directly (not proxied)
echo ""
echo "6️⃣ Testing Core API endpoint (direct access)..."
API_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 -k https://$DOMAIN:21004/health 2>/dev/null || echo "000")
if [ "$API_CODE" = "200" ]; then
    echo "✅ Core API endpoint is accessible directly on port 21004"
else
    echo "❌ Core API endpoint test failed (Status: $API_CODE)"
fi

echo ""
echo "📋 Test Summary:"
echo "   Domain: $DOMAIN"
echo "   Local HTTP (port 80): $(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://localhost:80 2>/dev/null || echo "failed")"
echo "   Local HTTPS (port 443): $(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 -k https://localhost:443 2>/dev/null || echo "failed")"
echo "   Remote HTTP: $HTTP_CODE"
echo "   Remote HTTPS: $HTTPS_CODE"
echo ""
echo "💡 To view logs: docker compose logs caddy"
echo "💡 To restart: docker compose restart caddy"
