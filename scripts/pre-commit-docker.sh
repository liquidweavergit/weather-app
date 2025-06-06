#!/bin/bash
# Temperature Display App - Docker Pre-commit Wrapper Script
# Runs pre-commit hooks inside Docker development environment
# Usage: ./scripts/pre-commit-docker.sh [pre-commit args...]

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"
SERVICE_NAME="app"

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

# Function to check if Docker and docker-compose are available
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose is not installed or not in PATH"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        exit 1
    fi
}

# Function to check if development environment is running
check_dev_environment() {
    cd "$PROJECT_ROOT"
    
    if ! docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "$SERVICE_NAME.*Up"; then
        print_warning "Development environment is not running"
        print_status "Starting development environment..."
        
        # Start the development environment
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d --build
        
        # Wait for the service to be healthy
        print_status "Waiting for service to be ready..."
        local timeout=60
        local count=0
        
        while [ $count -lt $timeout ]; do
            if docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "$SERVICE_NAME.*Up.*healthy"; then
                print_success "Development environment is ready"
                break
            fi
            
            if [ $count -eq $((timeout - 1)) ]; then
                print_error "Timeout waiting for development environment to be ready"
                exit 1
            fi
            
            sleep 1
            count=$((count + 1))
        done
    else
        print_status "Development environment is already running"
    fi
}

# Function to install pre-commit hooks if not already installed
install_precommit_hooks() {
    print_status "Installing pre-commit hooks in Docker environment..."
    
    cd "$PROJECT_ROOT"
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T "$SERVICE_NAME" pre-commit install
    
    if [ $? -eq 0 ]; then
        print_success "Pre-commit hooks installed successfully"
    else
        print_error "Failed to install pre-commit hooks"
        exit 1
    fi
}

# Function to run pre-commit in Docker environment
run_precommit() {
    local args=("$@")
    
    print_status "Running pre-commit in Docker development environment..."
    print_status "Command: pre-commit ${args[*]}"
    
    cd "$PROJECT_ROOT"
    
    # Run pre-commit with provided arguments
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T "$SERVICE_NAME" pre-commit "${args[@]}"
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        print_success "Pre-commit completed successfully"
    else
        print_error "Pre-commit failed with exit code $exit_code"
    fi
    
    return $exit_code
}

# Function to display usage information
show_usage() {
    cat << EOF
Docker Pre-commit Wrapper Script

USAGE:
    $0 [pre-commit-args...]

DESCRIPTION:
    Runs pre-commit hooks inside the Docker development environment.
    Ensures consistent code quality checks across all development environments.

EXAMPLES:
    $0 run --all-files                 # Run all hooks on all files
    $0 run --files app/main.py         # Run hooks on specific files
    $0 install                         # Install pre-commit hooks
    $0 autoupdate                      # Update hook versions
    $0 run mypy                        # Run specific hook

ENVIRONMENT:
    The script automatically starts the development environment if not running.
    Uses docker-compose.yml configuration from the project root.

REQUIREMENTS:
    - Docker and docker-compose installed
    - Docker daemon running
    - Valid docker-compose.yml in project root

For more pre-commit options, see: pre-commit --help
EOF
}

# Main execution
main() {
    # Change to project root directory
    cd "$PROJECT_ROOT"
    
    # Handle help flag
    if [ $# -eq 1 ] && [[ "$1" == "--help" || "$1" == "-h" ]]; then
        show_usage
        exit 0
    fi
    
    print_status "Temperature Display App - Docker Pre-commit Runner"
    print_status "Project root: $PROJECT_ROOT"
    
    # Check prerequisites
    check_docker
    check_dev_environment
    
    # If no arguments provided, show usage and run with --help
    if [ $# -eq 0 ]; then
        print_warning "No arguments provided"
        show_usage
        echo ""
        print_status "Running pre-commit --help:"
        run_precommit --help
        exit 0
    fi
    
    # Special handling for install command
    if [ "$1" == "install" ]; then
        install_precommit_hooks
        exit $?
    fi
    
    # Run pre-commit with provided arguments
    run_precommit "$@"
    exit $?
}

# Execute main function with all arguments
main "$@" 