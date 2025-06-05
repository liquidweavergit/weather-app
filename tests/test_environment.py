"""
Local environment validation tests for Temperature Display App.

This module tests local development environment setup, Python version, dependencies,
and critical configuration. For Docker container validation, see test_docker_environment.py.

Note: These tests are for local development setup only. The production app runs in Docker.
"""

import os
import sys
import subprocess
import platform
import pytest
from typing import Optional
import importlib.util


class TestPythonEnvironment:
    """Test Python version and basic environment setup."""
    
    def test_python_version_meets_requirements(self):
        """Test that Python version is 3.11 or higher."""
        version = sys.version_info
        assert version.major == 3, f"Python 3.x required, got {version.major}.{version.minor}"
        assert version.minor >= 11, f"Python 3.11+ required, got {version.major}.{version.minor}"
    
    def test_platform_compatibility(self):
        """Test that platform is supported."""
        supported_platforms = ['linux', 'darwin', 'win32']
        current_platform = sys.platform
        assert current_platform in supported_platforms, (
            f"Unsupported platform: {current_platform}. "
            f"Supported: {', '.join(supported_platforms)}"
        )
    
    def test_virtual_environment_active(self):
        """Test that virtual environment is activated."""
        # Check if we're in a virtual environment
        in_venv = (
            hasattr(sys, 'real_prefix') or 
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        )
        assert in_venv, (
            "Virtual environment not detected. "
            "Please activate your virtual environment before running tests."
        )


class TestRequiredEnvironmentVariables:
    """Test that required environment variables are set."""
    
    def test_database_url_configured(self):
        """Test that DATABASE_URL environment variable is set."""
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            assert database_url.startswith(('postgresql://', 'postgresql+asyncpg://')), (
                f"DATABASE_URL must be PostgreSQL URL, got: {database_url[:20]}..."
            )
        else:
            # Allow missing in test environment, but warn
            pytest.skip("DATABASE_URL not set - acceptable for initial setup")
    
    def test_redis_url_configured(self):
        """Test that REDIS_URL environment variable is set."""
        redis_url = os.getenv('REDIS_URL')
        if redis_url:
            assert redis_url.startswith('redis://'), (
                f"REDIS_URL must be Redis URL, got: {redis_url[:20]}..."
            )
        else:
            pytest.skip("REDIS_URL not set - acceptable for initial setup")
    
    def test_weather_api_key_configured(self):
        """Test that WEATHER_API_KEY environment variable is set."""
        api_key = os.getenv('WEATHER_API_KEY')
        if api_key:
            assert len(api_key) >= 16, "WEATHER_API_KEY appears to be too short"
            assert api_key.isalnum(), "WEATHER_API_KEY should be alphanumeric"
        else:
            pytest.skip("WEATHER_API_KEY not set - acceptable for initial setup")
    
    def test_secret_key_configured(self):
        """Test that SECRET_KEY environment variable is set."""
        secret_key = os.getenv('SECRET_KEY')
        if secret_key:
            assert len(secret_key) >= 32, "SECRET_KEY must be at least 32 characters"
        else:
            pytest.skip("SECRET_KEY not set - acceptable for initial setup")
    
    def test_environment_name_set(self):
        """Test that ENVIRONMENT environment variable is set."""
        environment = os.getenv('ENVIRONMENT', 'development')
        valid_environments = ['development', 'testing', 'staging', 'production']
        assert environment in valid_environments, (
            f"ENVIRONMENT must be one of {valid_environments}, got: {environment}"
        )


class TestCriticalDependencies:
    """Test that critical dependencies are available."""
    
    def test_fastapi_available(self):
        """Test that FastAPI is installed and importable."""
        try:
            import fastapi
            # Check minimum version requirement
            version_parts = fastapi.__version__.split('.')
            major, minor = int(version_parts[0]), int(version_parts[1])
            assert (major, minor) >= (0, 104), (
                f"FastAPI 0.104+ required, got {fastapi.__version__}"
            )
        except ImportError:
            pytest.fail("FastAPI not installed. Run: pip install fastapi[all]")
    
    def test_sqlalchemy_available(self):
        """Test that SQLAlchemy is installed and importable."""
        try:
            import sqlalchemy
            # Check for SQLAlchemy 2.0+
            version_parts = sqlalchemy.__version__.split('.')
            major = int(version_parts[0])
            assert major >= 2, (
                f"SQLAlchemy 2.0+ required, got {sqlalchemy.__version__}"
            )
        except ImportError:
            pytest.fail("SQLAlchemy not installed. Run: pip install sqlalchemy[asyncio]")
    
    def test_postgresql_driver_available(self):
        """Test that asyncpg (PostgreSQL async driver) is available."""
        try:
            import asyncpg
        except ImportError:
            pytest.fail("asyncpg not installed. Run: pip install asyncpg")
    
    def test_redis_driver_available(self):
        """Test that redis driver is available."""
        try:
            import redis
        except ImportError:
            pytest.fail("redis not installed. Run: pip install redis")
    
    def test_http_client_available(self):
        """Test that httpx (async HTTP client) is available."""
        try:
            import httpx
        except ImportError:
            pytest.fail("httpx not installed. Run: pip install httpx")
    
    def test_pydantic_available(self):
        """Test that Pydantic is installed and compatible."""
        try:
            import pydantic
            # Check for Pydantic v2
            version_parts = pydantic.__version__.split('.')
            major = int(version_parts[0])
            assert major >= 2, (
                f"Pydantic v2+ required, got {pydantic.__version__}"
            )
        except ImportError:
            pytest.fail("Pydantic not installed. Run: pip install pydantic")
    
    def test_alembic_available(self):
        """Test that Alembic (database migrations) is available."""
        try:
            import alembic
        except ImportError:
            pytest.fail("Alembic not installed. Run: pip install alembic")
    
    def test_structlog_available(self):
        """Test that structlog (structured logging) is available."""
        try:
            import structlog
        except ImportError:
            pytest.fail("structlog not installed. Run: pip install structlog")


class TestDevelopmentTools:
    """Test that development tools are available."""
    
    def test_pytest_available(self):
        """Test that pytest is installed and working."""
        try:
            import pytest
        except ImportError:
            pytest.fail("pytest not installed. Run: pip install pytest")
    
    def test_pytest_asyncio_available(self):
        """Test that pytest-asyncio is available for async testing."""
        try:
            import pytest_asyncio
        except ImportError:
            pytest.fail("pytest-asyncio not installed. Run: pip install pytest-asyncio")
    
    def test_black_available(self):
        """Test that black (code formatter) is available."""
        try:
            result = subprocess.run(['black', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            assert result.returncode == 0, "black command failed"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.fail("black not installed. Run: pip install black")
    
    def test_mypy_available(self):
        """Test that mypy (type checker) is available."""
        try:
            result = subprocess.run(['mypy', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            assert result.returncode == 0, "mypy command failed"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.fail("mypy not installed. Run: pip install mypy")


class TestFileSystemStructure:
    """Test that required directories and files exist or can be created."""
    
    def test_project_root_writeable(self):
        """Test that project root directory is writeable."""
        test_file = 'test_write_permissions.tmp'
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except (OSError, IOError) as e:
            pytest.fail(f"Project root not writeable: {e}")
    
    def test_can_create_required_directories(self):
        """Test that we can create required project directories."""
        required_dirs = [
            'app',
            'app/api',
            'app/models', 
            'app/services',
            'app/core',
            'tests',
            'tests/unit',
            'tests/integration',
            'migrations',
            'static',
            'templates'
        ]
        
        for directory in required_dirs:
            try:
                os.makedirs(directory, exist_ok=True)
                assert os.path.isdir(directory), f"Failed to create directory: {directory}"
                # Test write permissions
                test_file = os.path.join(directory, '.test_write')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
            except (OSError, IOError) as e:
                pytest.fail(f"Cannot create/write to directory {directory}: {e}")


class TestDatabaseConnectivity:
    """Test database connectivity (if configured)."""
    
    @pytest.mark.asyncio
    async def test_postgresql_connection(self):
        """Test PostgreSQL connection if DATABASE_URL is configured."""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            pytest.skip("DATABASE_URL not configured")
        
        try:
            import asyncpg
            import asyncio
            
            # Extract connection parameters from URL
            conn = await asyncpg.connect(database_url)
            
            # Test basic query
            version = await conn.fetchval('SELECT version()')
            assert 'PostgreSQL' in version, f"Unexpected database: {version}"
            
            # Test that we can create/drop test tables
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS test_connection (
                    id SERIAL PRIMARY KEY,
                    test_value TEXT
                )
            """)
            await conn.execute("DROP TABLE test_connection")
            
            await conn.close()
            
        except Exception as e:
            pytest.fail(f"PostgreSQL connection failed: {e}")
    
    def test_redis_connection(self):
        """Test Redis connection if REDIS_URL is configured."""
        redis_url = os.getenv('REDIS_URL')
        if not redis_url:
            pytest.skip("REDIS_URL not configured")
        
        try:
            import redis
            
            r = redis.from_url(redis_url)
            
            # Test basic operations
            test_key = 'test:connection'
            r.set(test_key, 'test_value', ex=60)
            value = r.get(test_key)
            assert value == b'test_value', "Redis read/write test failed"
            r.delete(test_key)
            
        except Exception as e:
            pytest.fail(f"Redis connection failed: {e}")


class TestDockerEnvironment:
    """Test Docker environment if applicable."""
    
    def test_docker_available(self):
        """Test that Docker is available (optional)."""
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                assert 'Docker version' in result.stdout
            else:
                pytest.skip("Docker not available - acceptable for development")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Docker not available - acceptable for development")
    
    def test_docker_compose_available(self):
        """Test that Docker Compose is available (optional)."""
        try:
            result = subprocess.run(['docker-compose', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                # Try docker compose (newer syntax)
                result = subprocess.run(['docker', 'compose', '--version'], 
                                      capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                assert any(word in result.stdout for word in ['compose', 'Compose'])
            else:
                pytest.skip("Docker Compose not available - acceptable for development")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Docker Compose not available - acceptable for development")


def test_environment_validation_summary():
    """
    Summary test that provides an overview of environment status.
    This test always passes but logs important environment information.
    """
    import logging
    
    logger = logging.getLogger(__name__)
    
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Virtual environment: {hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Log environment variables (without values for security)
    env_vars = ['DATABASE_URL', 'REDIS_URL', 'WEATHER_API_KEY', 'SECRET_KEY', 'ENVIRONMENT']
    for var in env_vars:
        is_set = var in os.environ
        logger.info(f"{var}: {'SET' if is_set else 'NOT SET'}")
    
    # This test always passes - it's just for information
    assert True, "Environment validation summary completed" 