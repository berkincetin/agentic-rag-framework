# Docker Guide for Agentic RAG System

This guide provides comprehensive instructions for running the Agentic RAG system using Docker.

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (version 20.10 or higher)
- [Docker Compose](https://docs.docker.com/compose/install/) (version 2.0 or higher)
- At least 4GB of available RAM
- 10GB of free disk space

### 1. Environment Setup

Create a `.env` file in the project root:

```bash
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO
```

### 2. Start the Application

```bash
# Production environment
docker-compose up -d

# Development environment (with hot reload)
docker-compose -f docker-compose.dev.yml up -d
```

### 3. Access Services

- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Gradio UI**: http://localhost:7860
- **MongoDB Express**: http://localhost:8081 (admin/admin123)

## Docker Architecture

### Services Overview

#### Production (`docker-compose.yml`)

| Service | Port | Description |
|---------|------|-------------|
| agentic-rag | 8000 | Main FastAPI application |
| mongodb | 27017 | MongoDB database |
| mongo-express | 8081 | MongoDB web interface |
| gradio-ui | 7860 | Gradio web interface |

#### Development (`docker-compose.dev.yml`)

| Service | Port | Description |
|---------|------|-------------|
| agentic-rag-dev | 8000 | Development app with hot reload |
| mongodb-dev | 27018 | Development MongoDB |
| mongo-express-dev | 8082 | Development MongoDB interface |
| gradio-ui-dev | 7861 | Development Gradio interface |
| redis-dev | 6379 | Redis for caching (optional) |

### Docker Images

The system uses multi-stage Docker builds:

1. **Builder stage**: Installs dependencies and builds the application
2. **Production stage**: Optimized runtime image with minimal footprint

## Management Scripts

### Windows (PowerShell)

```powershell
# Build images
.\scripts\docker-build.ps1 -Action build

# Start production
.\scripts\docker-build.ps1 -Action start

# Start development
.\scripts\docker-build.ps1 -Action dev

# View logs
.\scripts\docker-build.ps1 -Action logs

# Stop services
.\scripts\docker-build.ps1 -Action stop

# Clean up
.\scripts\docker-build.ps1 -Action clean -Force
```

### Linux/Mac (Bash)

```bash
# Make script executable (Linux/Mac only)
chmod +x scripts/docker-build.sh

# Build images
./scripts/docker-build.sh build

# Start production
./scripts/docker-build.sh start

# Start development
./scripts/docker-build.sh dev

# View logs
./scripts/docker-build.sh logs

# Stop services
./scripts/docker-build.sh stop

# Clean up
./scripts/docker-build.sh clean --force
```

## Manual Docker Commands

### Basic Operations

```bash
# Build images
docker-compose build

# Start services (detached)
docker-compose up -d

# View logs
docker-compose logs -f agentic-rag

# Stop services
docker-compose down

# Restart a service
docker-compose restart agentic-rag
```

### Development Operations

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# View development logs
docker-compose -f docker-compose.dev.yml logs -f agentic-rag-dev

# Stop development environment
docker-compose -f docker-compose.dev.yml down
```

### Maintenance Operations

```bash
# Update images
docker-compose pull
docker-compose up -d

# Rebuild with no cache
docker-compose build --no-cache

# Clean up everything (including volumes)
docker-compose down -v
docker system prune -f

# View resource usage
docker stats
```

## Data Management

### Volumes

The system uses Docker volumes for data persistence:

- `mongodb_data`: MongoDB database files
- `./data`: Document storage and processing
- `./configs`: Bot configurations
- `./prompts`: Prompt templates

### Backup and Restore

```bash
# Backup MongoDB data
docker-compose exec mongodb mongodump --out /data/backup

# Restore MongoDB data
docker-compose exec mongodb mongorestore /data/backup

# Backup application data
docker run --rm -v agentic-rag_mongodb_data:/data -v $(pwd):/backup alpine tar czf /backup/mongodb-backup.tar.gz /data
```

## Troubleshooting

### Common Issues

#### Port Conflicts

If ports are already in use, modify the port mappings in `docker-compose.yml`:

```yaml
ports:
  - "8001:8000"  # Change host port
```

#### Memory Issues

Increase Docker memory allocation:
- Docker Desktop: Settings → Resources → Memory (minimum 4GB)

#### Permission Issues

On Linux/Mac, ensure proper permissions:

```bash
sudo chown -R $USER:$USER data/
```

### Debugging

#### Access Container Shell

```bash
# Access main application container
docker-compose exec agentic-rag bash

# Access MongoDB container
docker-compose exec mongodb bash
```

#### Check Service Health

```bash
# Check all services status
docker-compose ps

# Check specific service logs
docker-compose logs agentic-rag

# Test API health
curl http://localhost:8000/
```

#### MongoDB Debugging

```bash
# Access MongoDB shell
docker-compose exec mongodb mongosh

# Check database status
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"

# View collections
docker-compose exec mongodb mongosh --eval "show dbs; use agentic_rag; show collections;"
```

### Performance Optimization

#### Resource Limits

Add resource limits to `docker-compose.yml`:

```yaml
services:
  agentic-rag:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
```

#### Caching

Enable Docker BuildKit for faster builds:

```bash
export DOCKER_BUILDKIT=1
docker-compose build
```

## Security Considerations

### Environment Variables

- Never commit `.env` files to version control
- Use Docker secrets for production deployments
- Rotate API keys regularly

### Network Security

- The default setup uses bridge networks for isolation
- For production, consider using custom networks with specific IP ranges
- Enable TLS/SSL for external access

### Container Security

- Containers run as non-root users
- Minimal base images reduce attack surface
- Regular security updates through image rebuilds

## Production Deployment

### Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml agentic-rag
```

### Kubernetes

Convert Docker Compose to Kubernetes manifests:

```bash
# Using kompose
kompose convert -f docker-compose.yml
kubectl apply -f .
```

### Monitoring

Add monitoring services to `docker-compose.yml`:

```yaml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

## Support

For Docker-related issues:

1. Check the [Docker documentation](https://docs.docker.com/)
2. Review container logs: `docker-compose logs`
3. Check system resources: `docker stats`
4. Verify network connectivity: `docker network ls`

For application-specific issues, refer to the main README.md file.
