# Docker Compose Setup Guide

## Temperature Display App - Containerized Development and Deployment

This guide covers the complete Docker Compose setup for the Temperature Display App, including development, production, and testing environments.

## Table of Contents

- [Quick Start](#quick-start)
- [Environment Overview](#environment-overview)
- [Service Architecture](#service-architecture)
- [Environment Configuration](#environment-configuration)
- [Management Scripts](#management-scripts)
- [Development Workflow](#development-workflow)
- [Production Deployment](#production-deployment)
- [Testing Setup](#testing-setup)
- [Monitoring & Observability](#monitoring--observability)
- [Database Management](#database-management)
- [Troubleshooting](#troubleshooting)
- [Performance Optimization](#performance-optimization)

## Quick Start

### Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- Git (for version control)
- 8GB+ RAM recommended for full stack

### Development Environment

```bash
# 1. Clone and setup
git clone <repository-url>
cd temperature-app

# 2. Copy environment file
cp env.example .env

# 3. Start development stack
./docker-manage.sh start dev

# 4. Access application
open http://localhost:8000
```

### Production Environment

```bash
# 1. Create production environment file
cp env.example .env.prod
# Edit .env.prod with production values

# 2. Start production stack
./docker-manage.sh start prod

# 3. Verify deployment
./docker-manage.sh health prod
```

## Environment Overview

### Docker Compose Files

| File | Purpose | Usage |
|------|---------|--------|
| `docker-compose.yml` | Development environment | Hot reload, debugging tools, exposed ports |
| `docker-compose.prod.yml` | Production environment | Optimized, secure, resource limits |
| `docker-compose.test.yml` | Testing environment | Isolated test databases, test runners |

### Service Matrix

| Service | Development | Production | Testing | Purpose |
|---------|-------------|------------|---------|---------|
| **app** | ✅ | ✅ | ✅ | FastAPI application |
| **db** | ✅ | ✅ | ✅ | PostgreSQL database |
| **redis** | ✅ | ✅ | ✅ | Cache and session store |
| **pgadmin** | ✅ | ❌ | ❌ | Database admin UI |
| **redis-commander** | ✅ | ❌ | ❌ | Redis web UI |
| **traefik** | ❌ | ✅ | ❌ | Reverse proxy |
| **prometheus** | Optional | ✅ | ❌ | Metrics collection |
| **grafana** | Optional | ✅ | ❌ | Metrics visualization |
| **loki** | ❌ | ✅ | ❌ | Log aggregation |
| **test_runner** | ❌ | ❌ | ✅ | Automated testing |

## Service Architecture

### Core Services

#### FastAPI Application (`app`)

**Development Configuration:**
- Hot reload enabled
- Debug mode active
- Source code mounted as volume
- Exposed on port 8000

**Production Configuration:**
- Optimized build with minimal layers
- Health checks enabled
- Resource limits enforced
- SSL termination via Traefik

```yaml
# Development
app:
  build:
    dockerfile: Dockerfile.dev
    target: development
  volumes:
    - .:/app  # Live code updates
  environment:
    - DEBUG=true
    - RELOAD=true

# Production
app:
  build:
    dockerfile: Dockerfile.prod
    target: production
  deploy:
    resources:
      limits:
        cpus: '1.0'
        memory: 512M
```

#### PostgreSQL Database (`db`)

**Features:**
- PostgreSQL 15 Alpine (lightweight)
- Optimized configuration for performance
- Persistent data storage
- Health checks
- Database initialization scripts

**Performance Tuning:**
```yaml
command: >
  postgres
  -c max_connections=200
  -c shared_buffers=256MB
  -c effective_cache_size=1GB
  -c work_mem=4MB
```

#### Redis Cache (`redis`)

**Configuration:**
- Redis 7 Alpine
- LRU eviction policy
- Persistence enabled
- Memory limits enforced

**Development:** 256MB memory limit
**Production:** 512MB memory limit

### Optional Services

#### Development Tools

**pgAdmin** - Database management interface
- Access: http://localhost:5050
- Default credentials: admin@temperature-app.local / admin

**Redis Commander** - Redis web interface
- Access: http://localhost:8081
- Default credentials: admin / admin

#### Production Services

**Traefik** - Reverse proxy and load balancer
- Automatic SSL with Let's Encrypt
- Service discovery
- Load balancing

**Monitoring Stack**
- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **Loki**: Log aggregation
- **Promtail**: Log shipping

## Environment Configuration

### Development (.env)

```bash
# Application
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=dev-secret-change-for-production

# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/temperature_app
POSTGRES_DB=temperature_app
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

# Redis
REDIS_URL=redis://redis:6379/0

# APIs (get from providers)
WEATHER_API_KEY=your_openweathermap_key
FALLBACK_WEATHER_API_KEY=your_accuweather_key

# Optional
GEOLOCATION_API_KEY=your_geolocation_key
```

### Production (.env.prod)

```bash
# Application
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-super-secure-secret-key-32-chars-minimum

# Database (use strong passwords)
DATABASE_URL=postgresql+asyncpg://postgres:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
POSTGRES_DB=temperature_app
POSTGRES_USER=postgres
POSTGRES_PASSWORD=ultra-secure-database-password

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=ultra-secure-redis-password

# APIs
WEATHER_API_KEY=production_openweathermap_key
FALLBACK_WEATHER_API_KEY=production_accuweather_key

# Domain and SSL
DOMAIN=your-domain.com
ACME_EMAIL=admin@your-domain.com

# Monitoring
GRAFANA_PASSWORD=secure-grafana-password
```

## Management Scripts

### Docker Management Script (`./docker-manage.sh`)

Comprehensive script for managing all environments:

```bash
# Start environments
./docker-manage.sh start dev      # Development
./docker-manage.sh start prod     # Production
./docker-manage.sh start test     # Testing

# View status and logs
./docker-manage.sh status         # All containers
./docker-manage.sh logs dev app   # App logs in dev

# Run tests
./docker-manage.sh test unit      # Unit tests
./docker-manage.sh test integration # Integration tests
./docker-manage.sh test all       # All tests

# Database operations
./docker-manage.sh backup dev     # Backup database
./docker-manage.sh restore dev backup_20231215_143022.sql

# Health checks
./docker-manage.sh health prod    # Production health

# Cleanup
./docker-manage.sh cleanup test   # Clean test environment
```

### Common Commands

```bash
# Development workflow
./docker-manage.sh start dev
./docker-manage.sh logs dev app
./docker-manage.sh test unit

# Production deployment
./docker-manage.sh start prod
./docker-manage.sh health prod
./docker-manage.sh backup prod

# Testing
./docker-manage.sh start test
./docker-manage.sh test all
./docker-manage.sh cleanup test
```

## Development Workflow

### 1. Initial Setup

```bash
# Clone repository
git clone <repo-url>
cd temperature-app

# Setup environment
cp env.example .env
# Edit .env with your API keys

# Build and start services
./docker-manage.sh start dev
```

### 2. Active Development

```bash
# Code changes are automatically reflected (hot reload)
# View logs in real-time
./docker-manage.sh logs dev app

# Run tests during development
./docker-manage.sh test unit

# Access development tools
open http://localhost:5050  # pgAdmin
open http://localhost:8081  # Redis Commander
```

### 3. Database Development

```bash
# Access database directly
docker-compose exec db psql -U postgres temperature_app

# Run migrations
docker-compose exec app alembic upgrade head

# Create migration
docker-compose exec app alembic revision --autogenerate -m "description"

# Backup/restore during development
./docker-manage.sh backup dev
./docker-manage.sh restore dev backup_file.sql
```

## Production Deployment

### 1. Server Preparation

```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Clone application
git clone <repo-url>
cd temperature-app
```

### 2. Environment Configuration

```bash
# Create production environment
cp env.example .env.prod

# Edit with production values
nano .env.prod

# Set strong passwords and API keys
# Configure domain and SSL settings
```

### 3. Deployment

```bash
# Create external volumes for data persistence
docker volume create temperature_postgres_data
docker volume create temperature_redis_data

# Start production stack
./docker-manage.sh start prod

# Verify deployment
./docker-manage.sh health prod
./docker-manage.sh status prod
```

### 4. SSL Configuration

```bash
# Traefik automatically handles SSL with Let's Encrypt
# Ensure DOMAIN and ACME_EMAIL are set in .env.prod

# Check certificate status
docker-compose -f docker-compose.prod.yml logs traefik
```

### 5. Monitoring Setup

```bash
# Start with monitoring profile
docker-compose -f docker-compose.prod.yml --profile monitoring up -d

# Access monitoring
open http://your-domain.com:3000  # Grafana
open http://your-domain.com:9090  # Prometheus
```

## Testing Setup

### Test Environment

The testing environment provides isolated databases and services:

```bash
# Start test environment
./docker-manage.sh start test

# Run specific test types
./docker-manage.sh test unit          # Unit tests
./docker-manage.sh test integration   # Integration tests
./docker-manage.sh test all          # All tests

# View test results
ls test_results/
ls coverage_reports/
```

### Test Configuration

- **Isolated databases**: Separate test database
- **In-memory storage**: tmpfs for speed
- **Test data**: Seeded test data
- **Coverage reports**: HTML and XML formats

### Continuous Integration

```yaml
# GitHub Actions example
- name: Run tests
  run: |
    ./docker-manage.sh start test
    ./docker-manage.sh test all
    ./docker-manage.sh cleanup test
```

## Monitoring & Observability

### Prometheus Metrics

**Application Metrics:**
- Request count and duration
- Database connection pool status
- Cache hit/miss rates
- Weather API response times

**Infrastructure Metrics:**
- Container resource usage
- Database performance
- Redis memory usage

### Grafana Dashboards

**Dashboards included:**
- Application Performance
- Database Monitoring
- Redis Cache Analytics
- Infrastructure Overview

**Access:** http://localhost:3000 (admin/password from .env.prod)

### Log Aggregation

**Loki + Promtail** for centralized logging:
- Application logs
- Database logs
- Container logs
- Access logs

## Database Management

### Development Database

```bash
# Connect to database
docker-compose exec db psql -U postgres temperature_app

# Run migrations
docker-compose exec app alembic upgrade head

# Reset database
docker-compose down -v
docker-compose up -d
```

### Production Database

```bash
# Backup database
./docker-manage.sh backup prod

# Monitor database performance
docker-compose -f docker-compose.prod.yml exec db psql -U postgres -c "SELECT * FROM pg_stat_activity;"

# View slow queries
docker-compose -f docker-compose.prod.yml exec db psql -U postgres -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

### Migration Management

```bash
# Create new migration
docker-compose exec app alembic revision --autogenerate -m "Add new table"

# Apply migrations
docker-compose exec app alembic upgrade head

# Rollback migration
docker-compose exec app alembic downgrade -1
```

## Troubleshooting

### Common Issues

#### Container Won't Start

```bash
# Check container logs
./docker-manage.sh logs dev app

# Check Docker daemon
docker system info

# Check disk space
df -h
docker system df
```

#### Database Connection Issues

```bash
# Verify database is running
docker-compose ps db

# Check database logs
./docker-manage.sh logs dev db

# Test connection
docker-compose exec app python -c "
import asyncpg
import asyncio
async def test():
    conn = await asyncpg.connect('postgresql://postgres:password@db:5432/temperature_app')
    print('Connection successful')
    await conn.close()
asyncio.run(test())
"
```

#### Performance Issues

```bash
# Monitor resource usage
docker stats

# Check application metrics
curl http://localhost:8000/metrics

# Database performance
docker-compose exec db psql -U postgres -c "SELECT * FROM pg_stat_activity;"
```

### Health Checks

```bash
# Application health
curl http://localhost:8000/health

# Database health
./docker-manage.sh health dev

# Redis health
docker-compose exec redis redis-cli ping
```

## Performance Optimization

### Resource Allocation

**Development:**
- CPU: 2-4 cores
- Memory: 4-8GB
- Storage: 20GB SSD

**Production:**
- CPU: 4-8 cores
- Memory: 8-16GB
- Storage: 100GB+ SSD

### Database Optimization

```sql
-- Monitor slow queries
SELECT query, total_time, calls, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;

-- Check index usage
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE tablename = 'weather_cache';
```

### Redis Optimization

```bash
# Monitor Redis performance
docker-compose exec redis redis-cli info stats
docker-compose exec redis redis-cli info memory

# Check slow log
docker-compose exec redis redis-cli slowlog get 10
```

### Application Optimization

- **Connection pooling**: SQLAlchemy async pool
- **Caching strategy**: Multi-level caching
- **API rate limiting**: Per-IP and per-user limits
- **Resource management**: Proper async/await usage

## Security Considerations

### Production Security

1. **Environment Variables**: Never commit secrets
2. **Network Security**: Internal-only service communication
3. **Database Security**: Strong passwords, limited connections
4. **SSL/TLS**: Automatic certificate management
5. **Container Security**: Non-root users, read-only filesystems

### Security Checklist

- [ ] Strong passwords in .env.prod
- [ ] API keys rotated regularly
- [ ] Database ports not exposed
- [ ] Redis password protected
- [ ] SSL certificates valid
- [ ] Container images up to date
- [ ] Security headers configured

## Backup and Recovery

### Automated Backups

```bash
# Daily backup script
#!/bin/bash
./docker-manage.sh backup prod
find backups/ -name "*.sql" -mtime +7 -delete
```

### Disaster Recovery

```bash
# Full environment restore
./docker-manage.sh cleanup prod
./docker-manage.sh start prod
./docker-manage.sh restore prod latest_backup.sql
```

## Contributing

### Development Guidelines

1. **Environment**: Always use Docker for development
2. **Testing**: Write tests before implementation
3. **Documentation**: Update docs with changes
4. **Performance**: Monitor metrics during development

### Code Quality

```bash
# Run linting and formatting
docker-compose exec app black .
docker-compose exec app flake8 .
docker-compose exec app mypy .

# Run tests with coverage
./docker-manage.sh test all
```

---

## Support

For issues and questions:
- Check logs: `./docker-manage.sh logs <env> <service>`
- Run health checks: `./docker-manage.sh health <env>`
- Review metrics: http://localhost:3000 (Grafana)
- Database admin: http://localhost:5050 (pgAdmin)

**Note:** This documentation covers Docker Compose setup. For basic Docker information, see [DOCKER.md](DOCKER.md). 