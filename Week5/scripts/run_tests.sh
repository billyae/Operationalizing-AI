#!/bin/bash

# Test runner script for Bedrock Chatbot Application
# This script runs all tests with proper configuration and generates reports

set -e  # Exit on any error

echo "🧪 Bedrock Chatbot - Test Runner"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python3 is not installed or not in PATH"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "pytest.ini" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Install test dependencies
print_status "Installing test dependencies..."
pip install -r tests/requirements.txt

# Install project dependencies
if [ -f "backend/requirements.txt" ]; then
    print_status "Installing backend dependencies..."
    pip install -r backend/requirements.txt
fi

if [ -f "frontend/requirements.txt" ]; then
    print_status "Installing frontend dependencies..."
    pip install -r frontend/requirements.txt
fi

# Create necessary directories
mkdir -p tests/coverage_html
mkdir -p tests/data

# Function to run specific test categories
run_unit_tests() {
    print_status "Running unit tests..."
    pytest -m "unit" --tb=short
}

run_integration_tests() {
    print_status "Running integration tests..."
    pytest -m "integration" --tb=short
}

run_backend_tests() {
    print_status "Running backend tests..."
    pytest tests/backend/ --tb=short
}

run_frontend_tests() {
    print_status "Running frontend tests..."
    pytest tests/frontend/ --tb=short
}

run_auth_tests() {
    print_status "Running authentication tests..."
    pytest -m "auth" --tb=short
}

# Parse command line arguments
case "${1:-all}" in
    "unit")
        run_unit_tests
        ;;
    "integration")
        run_integration_tests
        ;;
    "backend")
        run_backend_tests
        ;;
    "frontend")
        run_frontend_tests
        ;;
    "auth")
        run_auth_tests
        ;;
    "coverage")
        print_status "Running tests with detailed coverage..."
        pytest --cov-report=html --cov-report=term-missing --cov-fail-under=80
        print_success "Coverage report generated in tests/coverage_html/"
        ;;
    "quick")
        print_status "Running quick test suite (no coverage)..."
        pytest --no-cov -q
        ;;
    "verbose"|"debug")
        print_status "Running tests in verbose mode..."
        pytest -v -s --tb=long
        ;;
    "all"|*)
        print_status "Running all tests..."
        
        # Clean previous reports
        rm -rf tests/coverage_html/*
        rm -f tests/report.html tests/report.json tests/coverage.xml
        
        # Run all tests
        pytest
        
        print_success "All tests completed!"
        
        # Check if coverage reports were generated
        if [ -f "tests/coverage.xml" ]; then
            print_success "Coverage report: tests/coverage_html/index.html"
        fi
        
        if [ -f "tests/report.html" ]; then
            print_success "Test report: tests/report.html"
        fi
        
        if [ -f "tests/report.json" ]; then
            print_success "JSON report: tests/report.json"
        fi
        ;;
esac

# Check test results
if [ $? -eq 0 ]; then
    print_success "All tests passed! ✅"
    
    # Display coverage summary if available
    if command -v coverage &> /dev/null; then
        echo ""
        print_status "Coverage Summary:"
        coverage report --show-missing
    fi
    
else
    print_error "Some tests failed! ❌"
    echo ""
    print_warning "Check the test output above for details."
    print_warning "You can run specific test categories:"
    echo "  ./run_tests.sh unit       - Run only unit tests"
    echo "  ./run_tests.sh backend    - Run only backend tests"
    echo "  ./run_tests.sh frontend   - Run only frontend tests"
    echo "  ./run_tests.sh auth       - Run only auth tests"
    echo "  ./run_tests.sh verbose    - Run with detailed output"
    exit 1
fi

echo ""
print_status "Test run completed at $(date)"

# Optional: Open coverage report in browser (uncomment if desired)
# if [ -f "tests/coverage_html/index.html" ] && command -v open &> /dev/null; then
#     print_status "Opening coverage report in browser..."
#     open tests/coverage_html/index.html
# fi 