#!/bin/bash
# Docker Build Script for Temperature Display App
# Usage: ./docker-build.sh [dev|prod|test|all]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project configuration
PROJECT_NAME="temperature-app"
VERSION="1.0.0"

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

# Function to build development image
build_dev() {
    print_status "Building development image..."
    docker build \
        -f Dockerfile.dev \
        -t ${PROJECT_NAME}:dev \
        -t ${PROJECT_NAME}:dev-${VERSION} \
        --target development \
        .
    print_success "Development image built: ${PROJECT_NAME}:dev"
}

# Function to build production image (multi-stage)
build_prod() {
    print_status "Building production image (multi-stage)..."
    docker build \
        -f Dockerfile \
        -t ${PROJECT_NAME}:prod \
        -t ${PROJECT_NAME}:prod-${VERSION} \
        -t ${PROJECT_NAME}:latest \
        --target production \
        .
    print_success "Production image built: ${PROJECT_NAME}:prod"
}

# Function to build ultra-optimized production image
build_prod_optimized() {
    print_status "Building ultra-optimized production image..."
    docker build \
        -f Dockerfile.prod \
        -t ${PROJECT_NAME}:prod-optimized \
        -t ${PROJECT_NAME}:prod-optimized-${VERSION} \
        --target production \
        .
    print_success "Optimized production image built: ${PROJECT_NAME}:prod-optimized"
}

# Function to build distroless image
build_distroless() {
    print_status "Building distroless image..."
    docker build \
        -f Dockerfile.prod \
        -t ${PROJECT_NAME}:distroless \
        -t ${PROJECT_NAME}:distroless-${VERSION} \
        --target distroless \
        .
    print_success "Distroless image built: ${PROJECT_NAME}:distroless"
}

# Function to build testing image
build_test() {
    print_status "Building testing image..."
    docker build \
        -f Dockerfile \
        -t ${PROJECT_NAME}:test \
        -t ${PROJECT_NAME}:test-${VERSION} \
        --target testing \
        .
    print_success "Testing image built: ${PROJECT_NAME}:test"
}

# Function to show image sizes
show_sizes() {
    print_status "Docker image sizes:"
    echo
    docker images ${PROJECT_NAME} --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" | head -20
}

# Function to run security scan (if trivy is available)
security_scan() {
    if command -v trivy &> /dev/null; then
        print_status "Running security scan with Trivy..."
        trivy image ${PROJECT_NAME}:prod-optimized
    else
        print_warning "Trivy not available. Install it for security scanning: https://aquasecurity.github.io/trivy/"
    fi
}

# Function to test images
test_images() {
    print_status "Testing built images..."
    
    # Test development image
    if docker image inspect ${PROJECT_NAME}:dev &> /dev/null; then
        print_status "Testing development image..."
        docker run --rm ${PROJECT_NAME}:dev python --version
        print_success "Development image test passed"
    fi
    
    # Test production image
    if docker image inspect ${PROJECT_NAME}:prod &> /dev/null; then
        print_status "Testing production image..."
        docker run --rm ${PROJECT_NAME}:prod python --version
        print_success "Production image test passed"
    fi
}

# Function to clean up Docker resources
cleanup() {
    print_status "Cleaning up Docker resources..."
    
    # Remove dangling images
    docker image prune -f
    
    # Remove unused build cache
    docker builder prune -f
    
    print_success "Cleanup completed"
}

# Main build function
build_all() {
    print_status "Building all Docker images for ${PROJECT_NAME}..."
    echo
    
    build_dev
    echo
    
    build_prod
    echo
    
    build_prod_optimized
    echo
    
    build_distroless
    echo
    
    build_test
    echo
    
    show_sizes
    echo
    
    test_images
    echo
    
    security_scan
    
    print_success "All builds completed successfully!"
}

# Help function
show_help() {
    echo "Docker Build Script for Temperature Display App"
    echo
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  dev              Build development image with debugging tools"
    echo "  prod             Build production image (multi-stage)"
    echo "  prod-optimized   Build ultra-optimized production image"
    echo "  distroless       Build minimal distroless image"
    echo "  test             Build testing image for CI/CD"
    echo "  all              Build all image variants"
    echo "  sizes            Show sizes of built images"
    echo "  scan             Run security scan on production image"
    echo "  test-images      Test built images"
    echo "  cleanup          Clean up Docker resources"
    echo "  help             Show this help message"
    echo
    echo "Examples:"
    echo "  $0 dev           # Build development image"
    echo "  $0 prod          # Build production image"
    echo "  $0 all           # Build all variants"
    echo
    echo "Environment Variables:"
    echo "  PROJECT_NAME     Override project name (default: temperature-app)"
    echo "  VERSION          Override version tag (default: 1.0.0)"
}

# Parse command line arguments
case "${1:-help}" in
    "dev")
        build_dev
        ;;
    "prod")
        build_prod
        ;;
    "prod-optimized")
        build_prod_optimized
        ;;
    "distroless")
        build_distroless
        ;;
    "test")
        build_test
        ;;
    "all")
        build_all
        ;;
    "sizes")
        show_sizes
        ;;
    "scan")
        security_scan
        ;;
    "test-images")
        test_images
        ;;
    "cleanup")
        cleanup
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo
        show_help
        exit 1
        ;;
esac 