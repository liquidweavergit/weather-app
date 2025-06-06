# Environment Setup and Validation Guide

This guide covers setting up and validating the development environment for the Temperature Display App.

## Table of Contents

- [Quick Start](#quick-start)
- [Environment Files](#environment-files)
- [Environment Validation](#environment-validation)
- [Docker Environment Validation](#docker-environment-validation)
- [Environment-Specific Setup](#environment-specific-setup)
- [Troubleshooting](#troubleshooting)

## Quick Start

### 1. Basic Environment Setup

```bash
# 1. Clone repository and navigate to project
cd temperature-display-app

# 2. Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment template
cp env.example .env

# 5. Validate basic environment
python validate_environment.py

# 6. Validate Docker environment (if using Docker)
python validate_docker_environment.py dev
```

### 2. Docker-First Setup (Recommended)

```bash
# 1. Ensure Docker is installed and running
docker --version
docker-compose --version

# 2. Copy environment template
cp env.dev.template .env

# 3. Validate Docker environment
python validate_docker_environment.py dev

# 4. Start development services
./docker-manage.sh start dev

# 5. Verify services are running
./docker-manage.sh status dev
```

## Environment Files

### Available Templates

| File | Purpose | Usage |
|------|---------|-------|
| `env.example` | Comprehensive template with all variables | `cp env.example .env` |
| `env.dev.template` | Development-optimized settings | `cp env.dev.template .env` |
| `env.prod.template` | Production-hardened configuration | `cp env.prod.template .env.prod` |
| `env.test.template` | Testing environment with isolated services | `cp env.test.template .env.test` |

### Environment File Priority

The application loads environment variables in this order:

1. System environment variables
2. `.env.{ENVIRONMENT}` (e.g., `.env.prod`, `.env.test`)
3. `.env` (development default)
4. Default values in application code

### Critical Environment Variables

#### Required for All Environments

```bash
ENVIRONMENT=development|production|testing
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
REDIS_URL=redis://host:port/db
SECRET_KEY=secure-random-key-minimum-32-characters
```

#### API Keys (Required for Weather Features)

```bash
WEATHER_API_KEY=your_openweathermap_api_key
FALLBACK_WEATHER_API_KEY=your_accuweather_api_key
GEOLOCATION_API_KEY=your_geolocation_api_key  # Optional
```

#### Security Settings (Production)

```bash
SECURE_SSL_REDIRECT=true
SECURE_HSTS_SECONDS=31536000
CORS_ORIGINS=https://your-domain.com
ALLOWED_HOSTS=your-domain.com
```

## Environment Validation

### Basic Validation

Validates Python environment, dependencies, and basic configuration:

```bash
# Standard validation
python validate_environment.py

# Include Docker checks
python validate_environment.py --docker
```

**Checks performed:**
- ✅ Python version (3.11+)
- ✅ Virtual environment
- ✅ Platform compatibility
- ✅ Required dependencies
- ✅ Environment variables
- ✅ Development tools
- ✅ File system permissions
- ✅ Docker availability (with --docker flag)

### Sample Output

```
================================================================================
Temperature Display App - Environment Validation
================================================================================

🔍 Core Environment:
  ✅ Python 3.11.5
  ✅ Virtual environment active
  ✅ Platform: darwin (Darwin)
  ✅ Project directory is writable

📦 Dependencies:
  ✅ FastAPI available
  ✅ SQLAlchemy available
  ✅ Pydantic available
  ❌ Redis not installed

🔧 Environment Variables:
  ✅ Database URL configured
  ✅ Redis URL configured
  ❌ Weather API key not set (optional for initial setup)

🛠️  Development Tools:
  ✅ Code formatter available
  ✅ Type checker available

🎉 Environment validation PASSED! Ready for development.
```

## Docker Environment Validation

### Comprehensive Docker Validation

Validates Docker installation, containers, services, and connectivity:

```bash
# Validate development environment
python validate_docker_environment.py dev

# Validate production environment
python validate_docker_environment.py prod

# Validate testing environment
python validate_docker_environment.py test
```

**Checks performed:**
- ✅ Docker installation and daemon
- ✅ Docker Compose availability
- ✅ Compose file syntax validation
- ✅ Environment file validation
- ✅ Docker networks and volumes
- ✅ Required Docker images
- ✅ Container status and health
- ✅ Service connectivity
- ✅ Application health endpoints
- ✅ Database and Redis connectivity

### Sample Output

```
================================================================================
Temperature Display App - Docker Environment Validation
================================================================================

🐳 Docker Installation:
  ✅ Docker installed: Docker version 24.0.6
  ✅ Docker Compose installed: docker-compose version 2.21.0
  ✅ Docker daemon running: Server Version: 24.0.6

📋 Docker Configuration:
  ✅ Development environment: docker-compose.yml valid
  ✅ Production environment: docker-compose.prod.yml valid
  ✅ Testing environment: docker-compose.test.yml valid

🚀 Container Status (dev):
  ✅ Dev service 'app' is running
  ✅ Dev service 'db' is running
  ✅ Dev service 'redis' is running

🌐 Service Connectivity (dev):
  ✅ Service 'app' accessible on port 8000
  ✅ Service 'db' accessible on port 5432
  ✅ Service 'redis' accessible on port 6379

🏥 Application Health (dev):
  ✅ Application health check passed
  ✅ Database connectivity check passed
  ✅ Redis connectivity check passed

🎉 Docker environment validation PASSED!
```

## Environment-Specific Setup

### Development Environment

**Optimized for:** Fast iteration, debugging, comprehensive logging

```bash
# Setup
cp env.dev.template .env
python validate_docker_environment.py dev
./docker-manage.sh start dev

# Features enabled:
# - Hot reload
# - Debug mode
# - Verbose logging
# - All development tools
# - pgAdmin and Redis Commander
```

**Available Services:**
- Application: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- pgAdmin: http://localhost:5050
- Redis Commander: http://localhost:8081

### Production Environment

**Optimized for:** Security, performance, monitoring

```bash
# Setup
cp env.prod.template .env.prod
# Edit .env.prod with production values
python validate_docker_environment.py prod
./docker-manage.sh start prod

# Features enabled:
# - SSL/TLS termination
# - Security headers
# - Monitoring stack
# - Resource limits
# - Log aggregation
```

**Security Checklist:**
- [ ] Changed `SECRET_KEY` to secure random value
- [ ] Set strong passwords for database and Redis
- [ ] Updated API keys to production values
- [ ] Configured SSL certificates
- [ ] Set up monitoring and alerting
- [ ] Verified security headers

### Testing Environment

**Optimized for:** Isolated testing, fast execution, CI/CD

```bash
# Setup
cp env.test.template .env.test
python validate_docker_environment.py test
./docker-manage.sh start test

# Features enabled:
# - Isolated test databases
# - Mocked external services
# - Fast cache TTL
# - Comprehensive test coverage
```

**Testing Services:**
- Test Database: Port 5433
- Test Redis: Port 6380
- All external APIs mocked

## Troubleshooting

### Common Issues

#### 1. Docker Daemon Not Running

**Error:** `Docker daemon not running`

**Solution:**
```bash
# Linux
sudo systemctl start docker

# macOS/Windows
# Start Docker Desktop application
```

#### 2. Permission Denied (Docker)

**Error:** `permission denied while trying to connect to the Docker daemon`

**Solution:**
```bash
# Add user to docker group (Linux)
sudo usermod -aG docker $USER
newgrp docker

# Or run with sudo (not recommended for development)
sudo docker --version
```

#### 3. Port Already in Use

**Error:** `port is already allocated`

**Solution:**
```bash
# Check what's using the port
lsof -i :8000
netstat -tulpn | grep :8000

# Stop conflicting services
./docker-manage.sh stop dev

# Or change port in environment file
APP_PORT=8001
```

#### 4. Environment Variables Not Loading

**Error:** Environment variables not found or using defaults

**Solution:**
```bash
# Check if .env file exists and has content
ls -la .env
cat .env

# Verify file format (no spaces around =)
VARIABLE=value  # ✅ Correct
VARIABLE = value  # ❌ Incorrect

# Check for BOM or encoding issues
file .env
dos2unix .env  # If on Windows
```

#### 5. Database Connection Failed

**Error:** `connection to server at "db" (172.x.x.x), port 5432 failed`

**Solution:**
```bash
# Check if database container is running
docker ps | grep postgres

# Check database logs
./docker-manage.sh logs dev db

# Verify database URL format
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database

# Test database connectivity
python validate_docker_environment.py dev
```

#### 6. Redis Connection Failed

**Error:** `Error connecting to Redis`

**Solution:**
```bash
# Check if Redis container is running
docker ps | grep redis

# Check Redis logs
./docker-manage.sh logs dev redis

# Test Redis connectivity
redis-cli -h localhost -p 6379 ping

# Verify Redis URL format
REDIS_URL=redis://host:port/database
```

### Validation Command Reference

```bash
# Basic environment validation
python validate_environment.py
python validate_environment.py --docker

# Docker environment validation
python validate_docker_environment.py [dev|prod|test]

# Service management
./docker-manage.sh start [dev|prod|test]
./docker-manage.sh status [dev|prod|test]
./docker-manage.sh logs [dev|prod|test] [service]
./docker-manage.sh stop [dev|prod|test]

# Testing
./docker-manage.sh test unit
./docker-manage.sh test integration
./docker-manage.sh test all

# Cleanup
./docker-manage.sh cleanup
./docker-manage.sh reset [dev|prod|test]
```

### Getting Help

1. **Check Logs:** `./docker-manage.sh logs dev`
2. **Validate Environment:** `python validate_docker_environment.py dev`
3. **Check Service Status:** `docker ps`
4. **Review Documentation:** See `DOCKER_COMPOSE.md` for detailed service information
5. **Reset Environment:** `./docker-manage.sh reset dev`

### Performance Optimization

#### Development Environment

```bash
# Allocate more resources (if needed)
APP_MEMORY_LIMIT=512m
DB_MEMORY_LIMIT=1g

# Disable unnecessary services
# Comment out pgadmin and redis-commander in docker-compose.yml

# Use faster storage
# Mount volumes with :cached flag on macOS
```

#### CI/CD Environment

```bash
# Use test environment template
cp env.test.template .env.test

# Minimal resource allocation
APP_MEMORY_LIMIT=128m
DB_MEMORY_LIMIT=256m

# Disable monitoring
ENABLE_METRICS=false
ENABLE_TRACING=false
```

---

## Next Steps

After successful environment validation:

1. **Development:** Start coding with hot reload
2. **Testing:** Run test suite to verify setup
3. **Production:** Follow production deployment checklist
4. **Monitoring:** Set up logging and metrics collection

For detailed Docker service information, see [`DOCKER_COMPOSE.md`](DOCKER_COMPOSE.md). 