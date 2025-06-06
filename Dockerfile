# Temperature Display App - Multi-stage Dockerfile
# Supports both development and production environments
# Build with: docker build --target development . (for dev)
# Build with: docker build --target production . (for prod)

# ====================================================================
# Base Image - Common dependencies and setup
# ====================================================================
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Build essentials for Python packages
    build-essential \
    # PostgreSQL client
    libpq-dev \
    # For health checks
    curl \
    # For timezone data
    tzdata \
    # Git for development
    git \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Set working directory
WORKDIR /app

# ====================================================================
# Dependencies Stage - Install Python dependencies
# ====================================================================
FROM base as dependencies

# Copy dependency files
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# ====================================================================
# Development Stage - Hot reload, debugging tools
# ====================================================================
FROM dependencies as development

# Development environment variables
ENV ENVIRONMENT=development \
    DEBUG=true \
    RELOAD=true

# Install additional development tools
RUN pip install \
    # Interactive debugger
    ipdb \
    # Development server with auto-reload
    watchfiles \
    # Code quality tools (already in requirements.txt but ensure latest)
    black[jupyter] \
    isort \
    mypy \
    flake8 \
    # Testing tools
    pytest-xdist \
    pytest-sugar

# Copy application code
COPY . .

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port for development server
EXPOSE 8000

# Health check for development
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Development command with hot reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/app"]

# ====================================================================
# Production Builder Stage - Build optimized application
# ====================================================================
FROM dependencies as builder

# Copy application code
COPY . .

# Remove development dependencies and files
RUN find . -type d -name "__pycache__" -delete \
    && find . -type f -name "*.pyc" -delete \
    && rm -rf .git .pytest_cache tests/

# ====================================================================
# Production Stage - Minimal, secure, optimized
# ====================================================================
FROM python:3.11-slim as production

# Production environment variables
ENV ENVIRONMENT=production \
    DEBUG=false \
    RELOAD=false \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y \
    # PostgreSQL client library
    libpq5 \
    # For health checks
    curl \
    # For timezone data
    tzdata \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Create non-root user for security
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code from builder stage
COPY --from=builder --chown=appuser:appuser /app .

# Remove any remaining development files
RUN find . -name "*.pyc" -delete \
    && find . -name "*.pyo" -delete \
    && find . -name "__pycache__" -type d -exec rm -rf {} + \
    && rm -rf tests/ docs/ .pytest_cache/ .mypy_cache/ \
    && rm -f pytest.ini .gitignore .dockerignore

# Switch to non-root user
USER appuser

# Expose port for production server
EXPOSE 8000

# Health check for production
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production command with Gunicorn for better performance
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "30", \
     "--keep-alive", "2", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]

# ====================================================================
# Testing Stage - For running tests in CI/CD
# ====================================================================
FROM development as testing

# Install testing dependencies
RUN pip install \
    pytest-xdist \
    pytest-benchmark \
    pytest-mock

# Override command for testing
CMD ["pytest", "-v", "--tb=short", "--cov=app", "--cov-report=term-missing"] 