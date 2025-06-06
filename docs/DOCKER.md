# Docker Setup - Temperature Display App

This document explains the Docker configuration and build options for the Temperature Display App.

## 📋 Table of Contents

- [Docker Images Overview](#docker-images-overview)
- [Quick Start](#quick-start)
- [Build Options](#build-options)
- [Development Workflow](#development-workflow)
- [Production Deployment](#production-deployment)
- [Performance Comparison](#performance-comparison)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)

## 🐳 Docker Images Overview

We provide multiple Docker image variants optimized for different use cases:

| Image | Purpose | Size | Security | Performance |
|-------|---------|------|----------|-------------|
| `temperature-app:dev` | Development with debugging tools | ~800MB | Medium | Medium |
| `temperature-app:prod` | Production multi-stage build | ~200MB | High | High |
| `temperature-app:prod-optimized` | Ultra-optimized production | ~150MB | Very High | Very High |
| `temperature-app:distroless` | Minimal distroless production | ~120MB | Maximum | Maximum |
| `temperature-app:test` | CI/CD testing | ~300MB | Medium | Medium |

## 🚀 Quick Start

### Development
```bash
# Build development image
./docker-build.sh dev

# Run with hot reload and volume mounting
docker run -p 8000:8000 -v $(pwd):/app temperature-app:dev
```

### Production
```bash
# Build production image
./docker-build.sh prod

# Run production container
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:pass@db:5432/temperature" \
  -e REDIS_URL="redis://redis:6379" \
  temperature-app:prod
```

## 🔧 Build Options

### Using the Build Script (Recommended)

```bash
# Build specific variant
./docker-build.sh dev              # Development image
./docker-build.sh prod             # Production image
./docker-build.sh prod-optimized   # Ultra-optimized production
./docker-build.sh distroless       # Minimal distroless
./docker-build.sh test             # Testing image
./docker-build.sh all              # Build all variants

# Utilities
./docker-build.sh sizes            # Show image sizes
./docker-build.sh scan             # Security scan
./docker-build.sh cleanup          # Clean up resources
```

### Manual Docker Commands

#### Development Image
```bash
docker build -f Dockerfile.dev -t temperature-app:dev .
```

#### Production Image (Multi-stage)
```bash
docker build -f Dockerfile --target production -t temperature-app:prod .
```

#### Ultra-Optimized Production
```bash
docker build -f Dockerfile.prod --target production -t temperature-app:prod-optimized .
```

#### Distroless Production
```bash
docker build -f Dockerfile.prod --target distroless -t temperature-app:distroless .
```

#### Testing Image
```bash
docker build -f Dockerfile --target testing -t temperature-app:test .
```

## 💻 Development Workflow

### Development Container Features

- **Hot Reload**: Code changes trigger automatic server restart
- **Debugging Tools**: ipdb, ipython, py-spy for debugging and profiling
- **Code Quality**: black, mypy, flake8, pylint pre-installed
- **Database Tools**: PostgreSQL client, Alembic for migrations
- **Volume Mounting**: Live code editing without rebuilds

### Development Commands

```bash
# Start development environment
docker run -p 8000:8000 -v $(pwd):/app temperature-app:dev

# Run with environment variables
docker run -p 8000:8000 \
  -v $(pwd):/app \
  -e DATABASE_URL="postgresql://user:pass@localhost:5432/temperature_dev" \
  -e REDIS_URL="redis://localhost:6379" \
  -e DEBUG=true \
  temperature-app:dev

# Interactive shell for debugging
docker run -it --rm -v $(pwd):/app temperature-app:dev bash

# Run tests in container
docker run --rm -v $(pwd):/app temperature-app:test

# Run specific test file
docker run --rm -v $(pwd):/app temperature-app:test pytest tests/test_specific.py -v
```

### Development with Docker Compose

```bash
# Start full development stack (when docker-compose.yml is created)
docker-compose up --build

# Run tests against development stack
docker-compose run --rm app pytest

# Access development shell
docker-compose exec app bash
```

## 🏭 Production Deployment

### Production Image Features

- **Multi-stage builds** for minimal size
- **Non-root user** for security
- **Optimized Gunicorn** configuration
- **Health checks** for orchestration
- **Compiled Python** files for faster startup
- **Minimal dependencies** (runtime only)

### Production Deployment Examples

#### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: temperature-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: temperature-app
  template:
    metadata:
      labels:
        app: temperature-app
    spec:
      containers:
      - name: app
        image: temperature-app:prod-optimized
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### Docker Swarm
```bash
docker service create \
  --name temperature-app \
  --replicas 3 \
  --publish 8000:8000 \
  --env DATABASE_URL="postgresql://user:pass@db:5432/temperature" \
  --env REDIS_URL="redis://redis:6379" \
  --constraint 'node.role == worker' \
  temperature-app:prod-optimized
```

#### Simple Production Run
```bash
docker run -d \
  --name temperature-app \
  --restart unless-stopped \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:pass@db:5432/temperature" \
  -e REDIS_URL="redis://redis:6379" \
  -e ENVIRONMENT=production \
  --memory="512m" \
  --cpus="0.5" \
  temperature-app:prod
```

## 📊 Performance Comparison

### Image Sizes
```bash
# View all image sizes
./docker-build.sh sizes

# Expected sizes:
# temperature-app:dev              ~800MB
# temperature-app:prod             ~200MB  
# temperature-app:prod-optimized   ~150MB
# temperature-app:distroless       ~120MB
```

### Startup Performance
| Image | Cold Start | Memory Usage | Security Score |
|-------|------------|--------------|----------------|
| Development | ~5-8 seconds | ~300MB | Medium |
| Production | ~2-3 seconds | ~150MB | High |
| Optimized | ~1-2 seconds | ~120MB | Very High |
| Distroless | ~1-2 seconds | ~100MB | Maximum |

### Security Scanning
```bash
# Run security scan (requires Trivy)
./docker-build.sh scan

# Manual scanning
trivy image temperature-app:prod-optimized
```

## 🔒 Security Considerations

### Security Features

1. **Non-root user**: All images run as non-root user (appuser/nonroot)
2. **Minimal attack surface**: Production images contain only runtime dependencies
3. **No shell access**: Distroless images have no shell or package manager
4. **Read-only filesystem**: Application code is read-only
5. **Health checks**: Built-in health monitoring
6. **Security labels**: OCI standard labels for identification

### Security Best Practices

```bash
# Run with read-only root filesystem
docker run --read-only --tmpfs /tmp -p 8000:8000 temperature-app:prod

# Run with specific user ID
docker run --user 1000:1000 -p 8000:8000 temperature-app:prod

# Limit resources
docker run \
  --memory="256m" \
  --cpus="0.5" \
  --pids-limit 100 \
  -p 8000:8000 \
  temperature-app:prod

# Use secrets for sensitive data
docker run -p 8000:8000 \
  --env DATABASE_URL_FILE=/run/secrets/db_url \
  --secret db_url \
  temperature-app:prod
```

## 🔍 Troubleshooting

### Common Issues

#### Build Failures
```bash
# Clean Docker cache
docker builder prune -f

# Remove all unused resources
docker system prune -a

# Build with no cache
docker build --no-cache -f Dockerfile.prod .
```

#### Container Won't Start
```bash
# Check logs
docker logs container_name

# Run with interactive shell (development only)
docker run -it --rm temperature-app:dev bash

# Check health status
docker inspect container_name | grep Health -A 10
```

#### Permission Issues
```bash
# Fix file ownership (development)
docker run --rm -v $(pwd):/app alpine chown -R 1000:1000 /app

# Run as current user
docker run --user $(id -u):$(id -g) -v $(pwd):/app temperature-app:dev
```

#### Performance Issues
```bash
# Monitor container resources
docker stats container_name

# Profile application (development)
docker run -v $(pwd):/app temperature-app:dev py-spy top --pid 1

# Check health endpoint
curl http://localhost:8000/health
```

### Debugging Tips

1. **Use development image** for debugging production issues
2. **Mount volumes** to inspect logs and data
3. **Use health checks** to monitor container state
4. **Check Docker logs** for startup issues
5. **Verify environment variables** are correctly set

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | Yes | PostgreSQL connection string | `postgresql://user:pass@db:5432/temperature` |
| `REDIS_URL` | Yes | Redis connection string | `redis://redis:6379` |
| `WEATHER_API_KEY` | Yes | Weather service API key | `abc123...` |
| `SECRET_KEY` | Yes | Application secret key | `super-secret-key-32-chars` |
| `ENVIRONMENT` | No | Environment name | `production` (default: `development`) |
| `DEBUG` | No | Enable debug mode | `false` (default: `true` in dev) |

### Health Check Endpoints

- **`/health`**: Basic health check (returns 200 if app is running)
- **`/ready`**: Readiness check (returns 200 if app can serve requests)
- **`/metrics`**: Application metrics (if enabled)

For more detailed information, see the main [README.md](README.md) file. 