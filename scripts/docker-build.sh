#!/bin/bash
# Docker build and deployment script for Agentic RAG System
# Developed by Atlas University, Istanbul, Türkiye
# Bash script for Linux/Mac environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ACTION="build"
FORCE=false
VERBOSE=false

# Functions for colored output
log_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

log_error() {
    echo -e "${RED}✗ $1${NC}"
}

log_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [ACTION] [OPTIONS]"
    echo ""
    echo "Actions:"
    echo "  build     Build Docker images"
    echo "  start     Start production environment"
    echo "  dev       Start development environment"
    echo "  stop      Stop all services"
    echo "  restart   Restart production environment"
    echo "  logs      Show application logs"
    echo "  clean     Clean up Docker resources"
    echo "  test      Test application health"
    echo ""
    echo "Options:"
    echo "  -f, --force     Force rebuild/cleanup"
    echo "  -v, --verbose   Verbose output"
    echo "  -h, --help      Show this help"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        build|start|dev|stop|restart|logs|clean|test)
            ACTION="$1"
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Function to check Docker installation
check_docker() {
    log_info "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        log_info "Please install Docker from: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        log_info "Please install Docker Compose from: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    log_success "Docker and Docker Compose are installed"
}

# Function to check environment file
check_env_file() {
    log_info "Checking environment configuration..."
    
    if [ ! -f ".env" ]; then
        log_warning ".env file not found"
        log_info "Creating sample .env file..."
        
        cat > .env << EOF
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO
EOF
        log_warning "Please edit .env file with your actual API keys before starting the application"
        return 1
    else
        log_success ".env file found"
        
        # Check for required keys
        if ! grep -q "OPENAI_API_KEY=sk-" .env; then
            log_warning "OPENAI_API_KEY not properly set in .env file"
        fi
        if ! grep -q "TAVILY_API_KEY=tvly-" .env; then
            log_warning "TAVILY_API_KEY not properly set in .env file"
        fi
        
        return 0
    fi
}

# Function to build application
build_application() {
    log_info "Building Agentic RAG Docker images..."
    
    build_args="docker-compose build"
    if [ "$VERBOSE" = true ]; then
        build_args="$build_args --verbose"
    fi
    if [ "$FORCE" = true ]; then
        build_args="$build_args --no-cache"
    fi
    
    eval $build_args
    
    log_success "Docker images built successfully"
}

# Function to start application
start_application() {
    local environment=${1:-prod}
    
    log_info "Starting Agentic RAG application ($environment environment)..."
    
    if [ "$environment" = "dev" ]; then
        docker-compose -f docker-compose.dev.yml up -d
    else
        docker-compose up -d
    fi
    
    log_success "Application started successfully"
    log_info "Services available at:"
    log_info "  • API: http://localhost:8000"
    log_info "  • API Docs: http://localhost:8000/docs"
    log_info "  • Gradio UI: http://localhost:7860"
    log_info "  • MongoDB Express: http://localhost:8081"
    
    if [ "$environment" = "dev" ]; then
        log_info "Development mode: Hot reload enabled"
    fi
}

# Function to stop application
stop_application() {
    log_info "Stopping Agentic RAG application..."
    
    docker-compose down 2>/dev/null || true
    docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
    
    log_success "Application stopped"
}

# Function to show logs
show_logs() {
    log_info "Showing application logs..."
    docker-compose logs -f agentic-rag
}

# Function to clean up
clean_application() {
    log_info "Cleaning up Docker resources..."
    
    if [ "$FORCE" = true ]; then
        log_warning "Force cleanup: This will remove all data!"
        docker-compose down -v --remove-orphans 2>/dev/null || true
        docker-compose -f docker-compose.dev.yml down -v --remove-orphans 2>/dev/null || true
        docker system prune -f
    else
        docker-compose down --remove-orphans 2>/dev/null || true
        docker-compose -f docker-compose.dev.yml down --remove-orphans 2>/dev/null || true
    fi
    
    log_success "Cleanup completed"
}

# Function to test application
test_application() {
    log_info "Testing application health..."
    
    # Wait for application to be ready
    max_attempts=30
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        attempt=$((attempt + 1))
        
        if curl -f http://localhost:8000/ >/dev/null 2>&1; then
            log_success "Application is healthy"
            return 0
        fi
        
        log_info "Waiting for application... (attempt $attempt/$max_attempts)"
        sleep 2
    done
    
    log_error "Application health check failed"
    exit 1
}

# Main execution
log_info "Agentic RAG Docker Management Script"
log_info "Developed by Atlas University, Istanbul, Türkiye"
echo ""

check_docker

case $ACTION in
    build)
        check_env_file || true
        build_application
        ;;
    start)
        if ! check_env_file; then
            log_error "Please configure .env file before starting"
            exit 1
        fi
        start_application "prod"
        ;;
    dev)
        if ! check_env_file; then
            log_error "Please configure .env file before starting"
            exit 1
        fi
        start_application "dev"
        ;;
    stop)
        stop_application
        ;;
    restart)
        stop_application
        sleep 2
        start_application "prod"
        ;;
    logs)
        show_logs
        ;;
    clean)
        clean_application
        ;;
    test)
        test_application
        ;;
    *)
        log_error "Unknown action: $ACTION"
        show_usage
        exit 1
        ;;
esac
