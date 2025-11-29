#!/bin/bash

# Configuration Service Test Script
# Run this on the remote server (192.168.88.120) to test the config service

set -e

echo "🧪 Testing AI Stack Configuration Service..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

BASE_URL="http://localhost:8083"

# Test 1: Check if service is running
print_test "Checking if config service is accessible..."
if curl -s --max-time 5 "$BASE_URL" > /dev/null; then
    print_success "Config service is accessible"
else
    print_fail "Config service is not accessible at $BASE_URL"
    echo "Make sure the service is running: docker-compose ps config-service"
    exit 1
fi

# Test 2: Check API services endpoint
print_test "Testing /api/services endpoint..."
if curl -s --max-time 5 "$BASE_URL/api/services" | grep -q "error"; then
    print_fail "Services API returned an error"
    curl -s "$BASE_URL/api/services"
else
    print_success "Services API is working"
fi

# Test 3: Check config files endpoint
print_test "Testing /api/config/files endpoint..."
response=$(curl -s --max-time 5 "$BASE_URL/api/config/files")
if echo "$response" | grep -q "nginx.conf\|docker-compose.yml"; then
    print_success "Config files API is working"
else
    print_fail "Config files API returned unexpected response:"
    echo "$response"
fi

# Test 4: Check web interface content
print_test "Testing web interface content..."
web_content=$(curl -s --max-time 5 "$BASE_URL")
if echo "$web_content" | grep -q "AI Stack Configuration Manager"; then
    print_success "Web interface is loading correctly"
else
    print_fail "Web interface is not loading expected content"
fi

# Test 5: Check Docker socket access (for service management)
print_test "Testing Docker socket access..."
if docker ps > /dev/null 2>&1; then
    print_success "Docker socket is accessible"
else
    print_fail "Docker socket is not accessible"
    echo "This may affect service restart functionality"
fi

# Test 6: Check database connectivity (if available)
print_test "Testing database connectivity..."
if curl -s --max-time 5 -X POST "$BASE_URL/api/database/query" \
    -H "Content-Type: application/json" \
    -d '{"query":"SELECT 1"}' | grep -q "results"; then
    print_success "Database connectivity is working"
else
    print_warning "Database connectivity test failed (may be expected if DB is not running)"
fi

echo
print_status "🎉 All tests completed!"
print_status ""
print_status "Service URLs:"
print_status "  • Web Interface: http://192.168.88.120:8083"
print_status "  • API Docs: Check the web interface for available endpoints"
print_status ""
print_status "To run tests again: ./test-config-service.sh"
print_status "To view logs: docker-compose logs -f config-service"