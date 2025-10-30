#!/bin/bash

# Chef's Training Kitchen - Docker Setup Verification Script
# This script verifies that the Docker setup is working correctly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${PURPLE}
🧪 Chef's Training Kitchen - Docker Verification
===============================================${NC}"
}

print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} ✅ $1"
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} ❌ $1"
}

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# Test counter
TESTS_RUN=0
TESTS_PASSED=0

run_test() {
    local test_name="$1"
    local test_command="$2"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    print_test "$test_name"
    
    if eval "$test_command" &> /dev/null; then
        print_pass "$test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        print_fail "$test_name"
        return 1
    fi
}

# Verification tests
verify_docker_setup() {
    print_header
    
    print_info "Starting Docker setup verification..."
    echo ""
    
    # Test 1: Docker services are running
    run_test "Docker services are running" \
        "docker-compose -f docker-compose.dev.yml ps | grep -q 'Up'"
    
    # Test 2: Database connectivity
    run_test "Database is accessible" \
        "docker-compose -f docker-compose.dev.yml exec -T db pg_isready -U chef_user -d chef_kitchen_dev"
    
    # Test 3: Redis connectivity  
    run_test "Redis is accessible" \
        "docker-compose -f docker-compose.dev.yml exec -T redis redis-cli ping | grep -q PONG"
    
    # Test 4: Web application health check
    run_test "Web application health check" \
        "curl -f http://localhost:8000/health/"
    
    # Test 5: Web application loads
    run_test "Web application homepage loads" \
        "curl -s http://localhost:8000/login/ | grep -q 'Chef'"
    
    # Test 6: Admin login page loads
    run_test "Admin login page loads" \
        "curl -f http://localhost:8000/login/ | grep -q 'login'"
    
    # Test 7: Static files are served
    run_test "Static files are served" \
        "curl -f http://localhost:8000/static/css/restaurant-theme.css | grep -q 'restaurant'"
    
    # Test 8: Database migrations applied
    run_test "Database migrations applied" \
        "docker-compose -f docker-compose.dev.yml exec -T web python manage.py showmigrations | grep -q '\[X\]'"
    
    # Test 9: Admin user exists
    run_test "Admin user exists" \
        "docker-compose -f docker-compose.dev.yml exec -T web python manage.py shell -c \"from django.contrib.auth.models import User; print(User.objects.filter(username='admin').exists())\" | grep -q True"
    
    # Test 10: Sample data exists
    run_test "Sample data exists" \
        "docker-compose -f docker-compose.dev.yml exec -T web python manage.py shell -c \"from training_requests.models import TrainingRequest; print(TrainingRequest.objects.count() > 0)\" | grep -q True"
    
    echo ""
    print_info "Verification completed!"
    echo ""
    
    # Results summary
    if [ $TESTS_PASSED -eq $TESTS_RUN ]; then
        echo -e "${GREEN}🎉 ALL TESTS PASSED! ($TESTS_PASSED/$TESTS_RUN)${NC}"
        echo -e "${GREEN}✅ Your Docker setup is working perfectly!${NC}"
        echo ""
        echo -e "${BLUE}🚀 Ready to test:${NC}"
        echo -e "  • Web App: ${YELLOW}http://localhost:8000${NC}"
        echo -e "  • Admin: ${YELLOW}admin / admin123${NC}"
        echo -e "  • Chef Leader: ${YELLOW}chef_leader / password123${NC}"
        echo ""
        return 0
    else
        echo -e "${RED}❌ SOME TESTS FAILED! ($TESTS_PASSED/$TESTS_RUN passed)${NC}"
        echo ""
        echo -e "${YELLOW}🔧 Troubleshooting steps:${NC}"
        echo "1. Check service logs: ./docker-setup.sh logs"
        echo "2. Restart services: ./docker-setup.sh restart"
        echo "3. Clean restart: ./docker-setup.sh cleanup && ./docker-setup.sh start"
        echo ""
        return 1
    fi
}

# Detailed application test
test_application_features() {
    print_info "Testing application features..."
    echo ""
    
    # Test restaurant theme elements
    print_test "Checking restaurant theme..."
    if curl -s http://localhost:8000/ | grep -q "Chef's Training Kitchen"; then
        print_pass "Restaurant branding present"
    else
        print_fail "Restaurant branding missing"
    fi
    
    if curl -s http://localhost:8000/static/css/restaurant-theme.css | grep -q "chef-red"; then
        print_pass "Restaurant CSS theme loaded"
    else
        print_fail "Restaurant CSS theme not loaded"
    fi
    
    # Test API endpoints
    print_test "Testing API endpoints..."
    
    # Health check with detailed response
    health_response=$(curl -s http://localhost:8000/health/)
    if echo "$health_response" | grep -q '"status":"healthy"'; then
        print_pass "Health check returns healthy status"
    else
        print_fail "Health check not returning healthy status"
        print_info "Health response: $health_response"
    fi
    
    # Test database queries
    print_test "Testing database operations..."
    
    user_count=$(docker-compose -f docker-compose.dev.yml exec -T web python manage.py shell -c "
from django.contrib.auth.models import User
print(User.objects.count())
" 2>/dev/null | tail -1)
    
    if [ "$user_count" -gt 0 ]; then
        print_pass "Database contains users ($user_count users)"
    else
        print_fail "No users found in database"
    fi
    
    request_count=$(docker-compose -f docker-compose.dev.yml exec -T web python manage.py shell -c "
from training_requests.models import TrainingRequest
print(TrainingRequest.objects.count())
" 2>/dev/null | tail -1)
    
    if [ "$request_count" -gt 0 ]; then
        print_pass "Database contains training requests ($request_count requests)"
    else
        print_fail "No training requests found in database"
    fi
}

# Performance test
test_performance() {
    print_info "Running basic performance tests..."
    echo ""
    
    # Test response times
    print_test "Measuring response times..."
    
    response_time=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:8000/)
    response_time_ms=$(echo "$response_time * 1000" | bc -l | cut -d. -f1)
    
    if [ "$response_time_ms" -lt 2000 ]; then
        print_pass "Homepage loads quickly (${response_time_ms}ms)"
    else
        print_fail "Homepage loads slowly (${response_time_ms}ms)"
    fi
    
    # Test concurrent requests
    print_test "Testing concurrent requests..."
    
    # Simple concurrent test
    for i in {1..5}; do
        curl -s http://localhost:8000/health/ &
    done
    wait
    
    if [ $? -eq 0 ]; then
        print_pass "Handles concurrent requests"
    else
        print_fail "Issues with concurrent requests"
    fi
}

# Main execution
main() {
    case "${1:-verify}" in
        "verify")
            verify_docker_setup
            ;;
        "features")
            test_application_features
            ;;
        "performance")
            test_performance
            ;;
        "all")
            verify_docker_setup && test_application_features && test_performance
            ;;
        "help"|"-h"|"--help")
            echo "Chef's Training Kitchen - Docker Verification Script"
            echo ""
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  verify       Run basic verification tests (default)"
            echo "  features     Test application features"
            echo "  performance  Run performance tests"
            echo "  all          Run all tests"
            echo "  help         Show this help"
            ;;
        *)
            echo "Unknown command: $1"
            echo "Use '$0 help' for available commands"
            exit 1
            ;;
    esac
}

# Check if bc is available for calculations
if ! command -v bc &> /dev/null; then
    print_info "Installing bc for calculations..."
    if command -v brew &> /dev/null; then
        brew install bc
    elif command -v apt-get &> /dev/null; then
        sudo apt-get install -y bc
    else
        print_info "Please install 'bc' for performance calculations"
    fi
fi

main "$@"