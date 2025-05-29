#!/bin/bash
# Docker entrypoint script for Agentic RAG System
# Developed by Atlas University, Istanbul, Türkiye

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Function to wait for MongoDB
wait_for_mongodb() {
    log "Waiting for MongoDB to be ready..."

    # Extract MongoDB host from MONGODB_URL or use default
    MONGO_HOST=${MONGODB_URL:-"mongodb://mongodb:27017/"}
    MONGO_HOST=$(echo $MONGO_HOST | sed 's|mongodb://||' | sed 's|/.*||' | sed 's|:.*||')
    MONGO_PORT=$(echo $MONGODB_URL | sed 's|.*:||' | sed 's|/.*||')

    if [ -z "$MONGO_PORT" ]; then
        MONGO_PORT=27017
    fi

    # netcat should be available from Dockerfile

    # Wait for MongoDB to be available
    for i in {1..30}; do
        if nc -z $MONGO_HOST $MONGO_PORT 2>/dev/null; then
            log "MongoDB is ready!"
            return 0
        fi
        warn "MongoDB not ready yet, waiting... (attempt $i/30)"
        sleep 2
    done

    error "MongoDB failed to become ready within 60 seconds"
    exit 1
}

# Function to check required environment variables
check_env_vars() {
    log "Checking required environment variables..."

    required_vars=("OPENAI_API_KEY" "TAVILY_API_KEY")
    missing_vars=()

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -ne 0 ]; then
        error "Missing required environment variables: ${missing_vars[*]}"
        error "Please set these variables in your .env file or docker-compose.yml"
        exit 1
    fi

    log "All required environment variables are set"
}

# Function to create necessary directories
create_directories() {
    log "Creating necessary directories..."

    directories=(
        "/app/data/raw"
        "/app/data/processed"
        "/app/data/chroma_stores"
        "/app/logs"
    )

    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log "Created directory: $dir"
        fi
    done
}

# Function to validate configuration files
validate_configs() {
    log "Validating configuration files..."

    config_dir="/app/configs"
    if [ ! -d "$config_dir" ]; then
        error "Configuration directory not found: $config_dir"
        exit 1
    fi

    # Check if there are any YAML config files
    if ! ls $config_dir/*.yaml >/dev/null 2>&1; then
        warn "No YAML configuration files found in $config_dir"
    else
        log "Configuration files found in $config_dir"
    fi

    # Check prompts directory
    prompts_dir="/app/prompts"
    if [ ! -d "$prompts_dir" ]; then
        warn "Prompts directory not found: $prompts_dir"
    else
        log "Prompts directory found: $prompts_dir"
    fi
}

# Function to run database migrations or setup
setup_database() {
    log "Setting up database connections..."

    # Test MongoDB connection
    if [ ! -z "$MONGODB_URL" ]; then
        log "Testing MongoDB connection..."
        python -c "
import pymongo
import sys
try:
    client = pymongo.MongoClient('$MONGODB_URL', serverSelectionTimeoutMS=5000)
    client.server_info()
    print('MongoDB connection successful')
except Exception as e:
    print(f'MongoDB connection failed: {e}')
    sys.exit(1)
" || exit 1
    fi
}

# Function to perform health checks
health_check() {
    log "Performing application health checks..."

    # Check if the application can import successfully
    python -c "
import sys
sys.path.append('/app')
try:
    from app.main import app
    print('Application imports successful')
except Exception as e:
    print(f'Application import failed: {e}')
    sys.exit(1)
" || exit 1
}

# Main execution
main() {
    log "Starting Agentic RAG System..."
    log "Developed by Atlas University, Istanbul, Türkiye"

    # Run all checks and setup
    check_env_vars
    create_directories
    validate_configs

    # Wait for external services if needed
    if [ ! -z "$MONGODB_URL" ]; then
        wait_for_mongodb
        setup_database
    fi

    # Perform health checks
    health_check

    log "All checks passed. Starting application..."
    log "Command: $@"

    # Execute the main command
    exec "$@"
}

# Handle signals gracefully
trap 'log "Received shutdown signal, stopping application..."; exit 0' SIGTERM SIGINT

# Run main function
main "$@"
