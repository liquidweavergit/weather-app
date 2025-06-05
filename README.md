# Temperature Display App

A fast, focused temperature display application built with Python/FastAPI backend and modern frontend technologies.

**🐳 Docker-First Development**: This project is fully containerized with no local machine dependencies.

## Docker Environment Validation (Task 1.1)

This project follows a Test-Driven Development approach with Docker-first deployment. The first step is validating your Docker development environment.

### Quick Start

1. **Docker Requirements**
   ```bash
   docker --version  # Docker 20.10+ recommended
   docker-compose --version  # Docker Compose v2+ recommended
   ```

2. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd temperature-display-app
   cp env.example .env
   # Edit .env with your actual values (see Docker Environment Variables below)
   ```

3. **Build and Start Services**
   ```bash
   docker-compose up --build -d
   ```

4. **Run Environment Validation Tests**
   ```bash
   docker-compose exec app pytest tests/test_environment.py -v
   ```

5. **Access Application**
   ```bash
   # API: http://localhost:8000
   # Docs: http://localhost:8000/docs
   ```

### Environment Validation Tests

The environment validation tests (`tests/test_environment.py`) verify:

#### **Critical Checks (Must Pass)**
- ✅ Python 3.11+ installed
- ✅ Virtual environment activated  
- ✅ Platform compatibility (Linux/macOS/Windows)
- ✅ Project directories can be created
- ✅ Write permissions in project root

#### **Dependency Checks**
- FastAPI 0.104+ with async support
- SQLAlchemy 2.0+ with asyncio support
- PostgreSQL driver (asyncpg)
- Redis client library
- HTTP client (httpx) for external APIs
- Pydantic v2+ for data validation
- Alembic for database migrations
- Structlog for structured logging

#### **Development Tools**
- pytest for testing framework
- pytest-asyncio for async test support
- black for code formatting
- mypy for type checking

#### **Optional Checks (Can Skip Initially)**
- Database connectivity (if DATABASE_URL set)
- Redis connectivity (if REDIS_URL set)  
- Weather API key validation
- Docker/Docker Compose availability

### Docker Environment Variables

Required variables for Docker deployment (copy from `env.example`):

```bash
# Application
ENVIRONMENT=development

# Database (Docker service names)
DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/temperature_app

# Cache (Docker service names)
REDIS_URL=redis://redis:6379/0

# External APIs
WEATHER_API_KEY=your_openweathermap_api_key

# Security
SECRET_KEY=your_32_character_secret_key

# Docker-specific settings
POSTGRES_DB=temperature_app
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
```

### Running Tests

```bash
# Run all environment validation tests
pytest tests/test_environment.py -v

# Run specific test categories
pytest tests/test_environment.py::TestPythonEnvironment -v
pytest tests/test_environment.py::TestCriticalDependencies -v

# Skip external service tests
pytest tests/test_environment.py -m "not external" -v

# Get test coverage
pytest tests/test_environment.py --cov=tests --cov-report=html
```

### Expected Output

When environment is properly configured:

```
================================= ENVIRONMENT VALIDATION =================================
✅ Python 3.11.5 detected
✅ Virtual environment active  
✅ Platform: darwin (macOS)
✅ All critical dependencies installed
✅ Project structure can be created
✅ Environment variables configured
✅ Database connection successful (if configured)
✅ Redis connection successful (if configured)
=========================================================================================
```

### Troubleshooting

**Docker Issues:**
```bash
# Check Docker is running
docker info

# Rebuild containers from scratch
docker-compose down --volumes --rmi all
docker-compose up --build -d
```

**Service Connection Issues:**
```bash
# Check service status
docker-compose ps

# View service logs
docker-compose logs app
docker-compose logs db
docker-compose logs redis
```

**Database Connection Issues:**
```bash
# Reset database
docker-compose down db
docker-compose up -d db

# Access database directly
docker-compose exec db psql -U postgres -d temperature_app
```

**Application Issues:**
```bash
# Restart application container
docker-compose restart app

# Access application shell
docker-compose exec app bash

# Run tests inside container
docker-compose exec app pytest tests/ -v
```

**Performance Issues:**
```bash
# Check resource usage
docker stats

# Clean up unused resources
docker system prune -f
docker volume prune -f
```

### Next Steps

Once environment validation passes:

1. ✅ **Task 1.1**: Environment validation tests ← **CURRENT**
2. ⏳ **Task 1.2**: Initialize Git repository 
3. ⏳ **Task 1.3**: Set up requirements.txt (completed)
4. ⏳ **Task 1.4**: Configure Docker setup
5. ⏳ **Task 1.5**: Create environment validation
6. ⏳ **Task 1.6**: Set up pre-commit hooks

### Project Structure

```
temperature-app/
├── docker-compose.yml           # Docker services orchestration
├── Dockerfile                   # Multi-stage Docker build (future)
├── .dockerignore               # Docker ignore patterns (future)
├── tests/
│   ├── conftest.py              # Pytest configuration
│   ├── test_environment.py      # Docker environment validation tests
│   ├── unit/                    # Unit tests (future)
│   └── integration/             # Integration tests (future)
├── app/                         # Application code (future)
├── requirements.txt             # Python dependencies
├── pytest.ini                  # Pytest settings
├── env.example                  # Environment variables template
└── README.md                    # This file
```

---

**Tech Stack**: Docker, Python 3.11+, FastAPI, PostgreSQL, Redis, Bootstrap + Tailwind  
**Deployment**: Docker-first with no local dependencies  
**Approach**: Test-Driven Development with >90% coverage target  
**Performance**: Sub-2-second response times, >80% cache hit rates 