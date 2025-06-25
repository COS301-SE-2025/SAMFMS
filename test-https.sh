#!/bin/bash

# Quick HTTPS Test Script
# This script helps test the HTTPS setup step by step

echo "🔧 SAMFMS HTTPS Test Script"
echo "=========================="

# Test 1: Check if domain resolves
echo "1. Testing domain resolution..."
if nslookup capstone-samfms.dns.net.za > /dev/null 2>&1; then
    echo "✅ Domain resolves correctly"
else
    echo "❌ Domain resolution failed"
fi

# Test 2: Check if HTTP redirects to HTTPS
echo "2. Testing HTTP to HTTPS redirect..."
if curl -s -I http://capstone-samfms.dns.net.za | grep -q "301\|302"; then
    echo "✅ HTTP redirects to HTTPS"
else
    echo "❌ HTTP redirect not working"
fi

# Test 3: Check HTTPS certificate
echo "3. Testing HTTPS certificate..."
if curl -s -I https://capstone-samfms.dns.net.za > /dev/null 2>&1; then
    echo "✅ HTTPS certificate is working"
else
    echo "❌ HTTPS certificate has issues"
fi

# Test 4: Check if frontend loads
echo "4. Testing frontend availability..."
response=$(curl -s -o /dev/null -w "%{http_code}" https://capstone-samfms.dns.net.za)
if [ "$response" = "200" ]; then
    echo "✅ Frontend loads successfully"
else
    echo "❌ Frontend not accessible (HTTP $response)"
fi

# Test 5: Check if API is accessible
echo "5. Testing API accessibility..."
api_response=$(curl -s -o /dev/null -w "%{http_code}" https://capstone-samfms.dns.net.za/api/health)
if [ "$api_response" = "200" ]; then
    echo "✅ API is accessible"
else
    echo "❌ API not accessible (HTTP $api_response)"
fi

echo ""
echo "Test completed. If any tests failed, check the logs:"
echo "docker-compose -f docker-compose.yml -f docker-compose.ssl.yml logs nginx"
echo "docker-compose -f docker-compose.yml -f docker-compose.ssl.yml logs mcore"
