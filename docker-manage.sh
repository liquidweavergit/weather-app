#!/bin/bash

# Temperature Display App - Docker Compose Management Script
# Comprehensive utility for managing Docker environments (dev, prod, test)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="temperature-app"
DEV_COMPOSE_FILE="docker-compose.yml"
PROD_COMPOSE_FILE="docker-compose.prod.yml"
TEST_COMPOSE_FILE="docker-compose.test.yml"

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# Check dependencies
check_dependencies() {
    log_step "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    log_success "Dependencies check passed"
}

# Environment validation
validate_environment() {
    local env=$1
    log_step "Validating $env environment..."
    
    case $env in
        dev|development)
            if [[ ! -f $DEV_COMPOSE_FILE ]]; then
                log_error "$DEV_COMPOSE_FILE not found"
                exit 1
            fi
            ;;
        prod|production)
            if [[ ! -f $PROD_COMPOSE_FILE ]]; then
                log_error "$PROD_COMPOSE_FILE not found"
                exit 1
            fi
            if [[ ! -f .env.prod ]]; then
                log_warning ".env.prod not found - production may fail"
            fi
            ;;
        test|testing)
            if [[ ! -f $TEST_COMPOSE_FILE ]]; then
                log_error "$TEST_COMPOSE_FILE not found"
                exit 1
            fi
            ;;
        *)
            log_error "Invalid environment: $env"
            log_info "Valid environments: dev, prod, test"
            exit 1
            ;;
    esac
    
    log_success "$env environment validated"
}

# Setup data directories
setup_directories() {
    log_step "Setting up data directories..."
    
    mkdir -p data/postgres data/redis
    mkdir -p logs test_logs
    mkdir -p backups
    mkdir -p test_results coverage_reports integration_test_results
    mkdir -p uploads
    mkdir -p letsencrypt
    
    # Set proper permissions
    chmod 755 data/postgres data/redis
    chmod 755 logs test_logs
    chmod 755 backups
    
    log_success "Data directories created"
}

# Start environment
start_environment() {
    local env=$1
    validate_environment $env
    setup_directories
    
    log_step "Starting $env environment..."
    
    case $env in
        dev|development)
            docker-compose -f $DEV_COMPOSE_FILE up --build -d
            ;;
        prod|production)
            docker-compose -f $PROD_COMPOSE_FILE up --build -d
            ;;
        test|testing)
            docker-compose -f $DEV_COMPOSE_FILE -f $TEST_COMPOSE_FILE up --build -d
            ;;
    esac
    
    log_success "$env environment started"
    show_status $env
}

# Stop environment
stop_environment() {
    local env=$1
    validate_environment $env
    
    log_step "Stopping $env environment..."
    
    case $env in
        dev|development)
            docker-compose -f $DEV_COMPOSE_FILE down
            ;;
        prod|production)
            docker-compose -f $PROD_COMPOSE_FILE down
            ;;
        test|testing)
            docker-compose -f $DEV_COMPOSE_FILE -f $TEST_COMPOSE_FILE down
            ;;
    esac
    
    log_success "$env environment stopped"
}

# Show status
show_status() {
    local env=${1:-"all"}
    
    log_step "Showing container status..."
    
    if [[ $env == "all" ]]; then
        docker ps -a --filter "label=project=$PROJECT_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    else
        case $env in
            dev|development)
                docker-compose -f $DEV_COMPOSE_FILE ps
                ;;
            prod|production)
                docker-compose -f $PROD_COMPOSE_FILE ps
                ;;
            test|testing)
                docker-compose -f $DEV_COMPOSE_FILE -f $TEST_COMPOSE_FILE ps
                ;;
        esac
    fi
}

# View logs
view_logs() {
    local env=$1
    local service=${2:-""}
    
    validate_environment $env
    
    log_step "Viewing $env logs for ${service:-all services}..."
    
    case $env in
        dev|development)
            if [[ -n $service ]]; then
                docker-compose -f $DEV_COMPOSE_FILE logs -f $service
            else
                docker-compose -f $DEV_COMPOSE_FILE logs -f
            fi
            ;;
        prod|production)
            if [[ -n $service ]]; then
                docker-compose -f $PROD_COMPOSE_FILE logs -f $service
            else
                docker-compose -f $PROD_COMPOSE_FILE logs -f
            fi
            ;;
        test|testing)
            if [[ -n $service ]]; then
                docker-compose -f $DEV_COMPOSE_FILE -f $TEST_COMPOSE_FILE logs -f $service
            else
                docker-compose -f $DEV_COMPOSE_FILE -f $TEST_COMPOSE_FILE logs -f
            fi
            ;;
    esac
}

# Run tests
run_tests() {
    local test_type=${1:-"unit"}
    
    log_step "Running $test_type tests..."
    
    case $test_type in
        unit)
            docker-compose -f $DEV_COMPOSE_FILE -f $TEST_COMPOSE_FILE run --rm test_runner
            ;;
        integration)
            docker-compose -f $DEV_COMPOSE_FILE -f $TEST_COMPOSE_FILE run --rm integration_test
            ;;
        all)
            docker-compose -f $DEV_COMPOSE_FILE -f $TEST_COMPOSE_FILE run --rm test_runner
            docker-compose -f $DEV_COMPOSE_FILE -f $TEST_COMPOSE_FILE run --rm integration_test
            ;;
        *)
            log_error "Invalid test type: $test_type"
            log_info "Valid test types: unit, integration, all"
            exit 1
            ;;
    esac
    
    log_success "$test_type tests completed"
}

# Database operations
database_backup() {
    local env=$1
    local backup_name="backup_$(date +%Y%m%d_%H%M%S).sql"
    
    validate_environment $env
    
    log_step "Creating database backup for $env environment..."
    
    case $env in
        dev|development)
            docker-compose -f $DEV_COMPOSE_FILE exec db pg_dump -U postgres temperature_app > "backups/$backup_name"
            ;;
        prod|production)
            docker-compose -f $PROD_COMPOSE_FILE exec db pg_dump -U postgres temperature_app > "backups/$backup_name"
            ;;
    esac
    
    log_success "Database backup created: backups/$backup_name"
}

database_restore() {
    local env=$1
    local backup_file=$2
    
    validate_environment $env
    
    if [[ ! -f "backups/$backup_file" ]]; then
        log_error "Backup file not found: backups/$backup_file"
        exit 1
    fi
    
    log_step "Restoring database from backup for $env environment..."
    log_warning "This will overwrite the current database!"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Database restore cancelled"
        exit 0
    fi
    
    case $env in
        dev|development)
            docker-compose -f $DEV_COMPOSE_FILE exec -T db psql -U postgres temperature_app < "backups/$backup_file"
            ;;
        prod|production)
            docker-compose -f $PROD_COMPOSE_FILE exec -T db psql -U postgres temperature_app < "backups/$backup_file"
            ;;
    esac
    
    log_success "Database restored from: backups/$backup_file"
}

# Health check
health_check() {
    local env=$1
    
    validate_environment $env
    
    log_step "Performing health check for $env environment..."
    
    # Check application health
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_success "Application health check passed"
    else
        log_error "Application health check failed"
    fi
    
    # Check database connectivity
    case $env in
        dev|development)
            if docker-compose -f $DEV_COMPOSE_FILE exec db pg_isready -U postgres > /dev/null 2>&1; then
                log_success "Database health check passed"
            else
                log_error "Database health check failed"
            fi
            ;;
        prod|production)
            if docker-compose -f $PROD_COMPOSE_FILE exec db pg_isready -U postgres > /dev/null 2>&1; then
                log_success "Database health check passed"
            else
                log_error "Database health check failed"
            fi
            ;;
    esac
    
    # Check Redis connectivity
    case $env in
        dev|development)
            if docker-compose -f $DEV_COMPOSE_FILE exec redis redis-cli ping > /dev/null 2>&1; then
                log_success "Redis health check passed"
            else
                log_error "Redis health check failed"
            fi
            ;;
        prod|production)
            if docker-compose -f $PROD_COMPOSE_FILE exec redis redis-cli ping > /dev/null 2>&1; then
                log_success "Redis health check passed"
            else
                log_error "Redis health check failed"
            fi
            ;;
    esac
}

# Clean up
cleanup() {
    local env=${1:-"all"}
    
    log_step "Cleaning up $env environment..."
    
    if [[ $env == "all" ]]; then
        docker-compose -f $DEV_COMPOSE_FILE down --volumes --remove-orphans
        docker-compose -f $PROD_COMPOSE_FILE down --volumes --remove-orphans
        docker-compose -f $DEV_COMPOSE_FILE -f $TEST_COMPOSE_FILE down --volumes --remove-orphans
        docker system prune -f
    else
        validate_environment $env
        case $env in
            dev|development)
                docker-compose -f $DEV_COMPOSE_FILE down --volumes --remove-orphans
                ;;
            prod|production)
                docker-compose -f $PROD_COMPOSE_FILE down --volumes --remove-orphans
                ;;
            test|testing)
                docker-compose -f $DEV_COMPOSE_FILE -f $TEST_COMPOSE_FILE down --volumes --remove-orphans
                ;;
        esac
    fi
    
    log_success "Cleanup completed"
}

# Show help
show_help() {
    cat << EOF
Temperature Display App - Docker Management Script

USAGE:
    $0 <command> [arguments]

COMMANDS:
    start <env>                 Start environment (dev, prod, test)
    stop <env>                  Stop environment (dev, prod, test)
    restart <env>               Restart environment (dev, prod, test)
    status [env]                Show container status (default: all)
    logs <env> [service]        View logs for environment and optional service
    test [type]                 Run tests (unit, integration, all)
    backup <env>                Create database backup
    restore <env> <file>        Restore database from backup
    health <env>                Perform health check
    cleanup [env]               Clean up environment (default: all)
    help                        Show this help message

EXAMPLES:
    $0 start dev                Start development environment
    $0 logs prod app            View production app logs
    $0 test all                 Run all tests
    $0 backup dev               Backup development database
    $0 health prod              Check production environment health
    $0 cleanup test             Clean up test environment

ENVIRONMENTS:
    dev, development            Development environment with hot reload
    prod, production            Production environment with optimizations
    test, testing              Testing environment with isolated databases

EOF
}

# Main script logic
main() {
    check_dependencies
    
    if [[ $# -eq 0 ]]; then
        show_help
        exit 0
    fi
    
    case $1 in
        start)
            if [[ $# -lt 2 ]]; then
                log_error "Environment required for start command"
                show_help
                exit 1
            fi
            start_environment $2
            ;;
        stop)
            if [[ $# -lt 2 ]]; then
                log_error "Environment required for stop command"
                show_help
                exit 1
            fi
            stop_environment $2
            ;;
        restart)
            if [[ $# -lt 2 ]]; then
                log_error "Environment required for restart command"
                show_help
                exit 1
            fi
            stop_environment $2
            start_environment $2
            ;;
        status)
            show_status ${2:-"all"}
            ;;
        logs)
            if [[ $# -lt 2 ]]; then
                log_error "Environment required for logs command"
                show_help
                exit 1
            fi
            view_logs $2 ${3:-""}
            ;;
        test)
            run_tests ${2:-"unit"}
            ;;
        backup)
            if [[ $# -lt 2 ]]; then
                log_error "Environment required for backup command"
                show_help
                exit 1
            fi
            database_backup $2
            ;;
        restore)
            if [[ $# -lt 3 ]]; then
                log_error "Environment and backup file required for restore command"
                show_help
                exit 1
            fi
            database_restore $2 $3
            ;;
        health)
            if [[ $# -lt 2 ]]; then
                log_error "Environment required for health command"
                show_help
                exit 1
            fi
            health_check $2
            ;;
        cleanup)
            cleanup ${2:-"all"}
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@" 