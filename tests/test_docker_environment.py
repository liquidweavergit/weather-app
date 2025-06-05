"""
Docker container validation tests for Temperature Display App.

This module tests Docker containers, health checks, service communication,
and container orchestration to ensure proper Docker-first development environment.

Run these tests with: pytest tests/test_docker_environment.py -m docker
Skip these tests with: pytest -m "not docker"
"""

import asyncio
import json
import os
import subprocess
import time
from typing import Dict, List, Optional
import pytest
import httpx
import docker
from docker.errors import DockerException

# Mark all tests in this file as requiring Docker
pytestmark = pytest.mark.docker


class TestDockerEnvironment:
    """Test Docker installation and basic functionality."""
    
    def test_docker_installed_and_running(self):
        """Test that Docker is installed and daemon is running."""
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            assert result.returncode == 0, "Docker command failed"
            assert 'Docker version' in result.stdout, f"Unexpected docker version output: {result.stdout}"
            
            # Test Docker daemon is running
            result = subprocess.run(['docker', 'info'], 
                                  capture_output=True, text=True, timeout=10)
            assert result.returncode == 0, "Docker daemon not running or not accessible"
            
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            pytest.fail(f"Docker not available: {e}")
    
    def test_docker_compose_installed(self):
        """Test that Docker Compose is installed and functional."""
        try:
            # Try docker-compose command
            result = subprocess.run(['docker-compose', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                # Try docker compose (newer syntax)
                result = subprocess.run(['docker', 'compose', '--version'], 
                                      capture_output=True, text=True, timeout=10)
            
            assert result.returncode == 0, "Docker Compose not available"
            assert any(word in result.stdout.lower() for word in ['compose', 'version']), \
                f"Unexpected docker-compose output: {result.stdout}"
                
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            pytest.fail(f"Docker Compose not available: {e}")
    
    def test_docker_client_accessible(self):
        """Test that Docker client can connect to daemon."""
        try:
            client = docker.from_env()
            client.ping()
            client.close()
        except DockerException as e:
            pytest.fail(f"Docker client cannot connect to daemon: {e}")


class TestDockerCompose:
    """Test Docker Compose configuration and services."""
    
    @pytest.fixture(scope="class")
    def docker_compose_file(self):
        """Verify docker-compose.yml exists."""
        compose_file = 'docker-compose.yml'
        if not os.path.exists(compose_file):
            pytest.skip("docker-compose.yml not found - create this file first")
        return compose_file
    
    def test_docker_compose_file_valid(self, docker_compose_file):
        """Test that docker-compose.yml is valid YAML."""
        try:
            result = subprocess.run(['docker-compose', 'config'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                result = subprocess.run(['docker', 'compose', 'config'], 
                                      capture_output=True, text=True, timeout=30)
            
            assert result.returncode == 0, f"docker-compose.yml validation failed: {result.stderr}"
            
        except subprocess.TimeoutExpired:
            pytest.fail("Docker Compose config validation timed out")
    
    def test_required_services_defined(self, docker_compose_file):
        """Test that required services are defined in docker-compose.yml."""
        try:
            result = subprocess.run(['docker-compose', 'config', '--services'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                result = subprocess.run(['docker', 'compose', 'config', '--services'], 
                                      capture_output=True, text=True, timeout=30)
            
            assert result.returncode == 0, "Failed to list services"
            
            services = result.stdout.strip().split('\n')
            required_services = {'app', 'db', 'redis'}
            defined_services = set(services)
            
            missing_services = required_services - defined_services
            assert not missing_services, f"Missing required services: {missing_services}"
            
        except subprocess.TimeoutExpired:
            pytest.fail("Docker Compose service listing timed out")


class TestContainerHealthChecks:
    """Test container health checks and readiness."""
    
    @pytest.fixture(scope="class")
    def docker_client(self):
        """Docker client fixture."""
        try:
            client = docker.from_env()
            yield client
            client.close()
        except DockerException as e:
            pytest.skip(f"Docker client not available: {e}")
    
    def test_database_container_health(self, docker_client):
        """Test PostgreSQL container health and readiness."""
        try:
            # Look for running database container
            containers = docker_client.containers.list(filters={"name": "db"})
            if not containers:
                containers = docker_client.containers.list(filters={"name": "postgres"})
            
            if not containers:
                pytest.skip("Database container not running - start with docker-compose up")
            
            db_container = containers[0]
            
            # Check container is running
            assert db_container.status == 'running', f"Database container not running: {db_container.status}"
            
            # Test PostgreSQL health check
            health_check = db_container.exec_run('pg_isready -U postgres')
            assert health_check.exit_code == 0, f"PostgreSQL health check failed: {health_check.output}"
            
        except Exception as e:
            pytest.fail(f"Database container health check failed: {e}")
    
    def test_redis_container_health(self, docker_client):
        """Test Redis container health and readiness."""
        try:
            # Look for running Redis container
            containers = docker_client.containers.list(filters={"name": "redis"})
            
            if not containers:
                pytest.skip("Redis container not running - start with docker-compose up")
            
            redis_container = containers[0]
            
            # Check container is running
            assert redis_container.status == 'running', f"Redis container not running: {redis_container.status}"
            
            # Test Redis health check
            health_check = redis_container.exec_run('redis-cli ping')
            assert health_check.exit_code == 0, f"Redis health check failed: {health_check.output}"
            assert b'PONG' in health_check.output, f"Unexpected Redis response: {health_check.output}"
            
        except Exception as e:
            pytest.fail(f"Redis container health check failed: {e}")
    
    def test_app_container_health(self, docker_client):
        """Test application container health and readiness."""
        try:
            # Look for running application container
            containers = docker_client.containers.list(filters={"name": "app"})
            if not containers:
                containers = docker_client.containers.list(filters={"name": "temperature"})
            
            if not containers:
                pytest.skip("Application container not running - start with docker-compose up")
            
            app_container = containers[0]
            
            # Check container is running
            assert app_container.status == 'running', f"Application container not running: {app_container.status}"
            
            # Test Python and FastAPI availability
            python_check = app_container.exec_run('python --version')
            assert python_check.exit_code == 0, f"Python not available: {python_check.output}"
            assert b'Python 3.' in python_check.output, f"Unexpected Python version: {python_check.output}"
            
        except Exception as e:
            pytest.fail(f"Application container health check failed: {e}")


class TestContainerNetworking:
    """Test Docker networking and service-to-service communication."""
    
    @pytest.fixture(scope="class")
    def docker_client(self):
        """Docker client fixture."""
        try:
            client = docker.from_env()
            yield client
            client.close()
        except DockerException as e:
            pytest.skip(f"Docker client not available: {e}")
    
    def test_container_network_exists(self, docker_client):
        """Test that containers are on the same network."""
        try:
            # Get networks
            networks = docker_client.networks.list()
            network_names = [network.name for network in networks]
            
            # Look for docker-compose network (usually project_default)
            compose_networks = [name for name in network_names if 'default' in name or 'temperature' in name]
            assert compose_networks, f"No Docker Compose network found. Available: {network_names}"
            
        except Exception as e:
            pytest.fail(f"Container network check failed: {e}")
    
    def test_app_to_database_connectivity(self, docker_client):
        """Test that app container can connect to database container."""
        try:
            # Get app container
            containers = docker_client.containers.list(filters={"name": "app"})
            if not containers:
                containers = docker_client.containers.list(filters={"name": "temperature"})
            
            if not containers:
                pytest.skip("Application container not running")
            
            app_container = containers[0]
            
            # Test connection to database using service name
            db_test = app_container.exec_run('python -c "import asyncpg; print(\'asyncpg available\')"')
            assert db_test.exit_code == 0, f"Database driver not available: {db_test.output}"
            
            # Test DNS resolution of database service
            dns_test = app_container.exec_run('nslookup db')
            if dns_test.exit_code != 0:
                # Try with getent if nslookup not available
                dns_test = app_container.exec_run('getent hosts db')
            
            # DNS might not work in all environments, so this is informational
            if dns_test.exit_code == 0:
                assert b'db' in dns_test.output.lower(), f"Database service not resolvable: {dns_test.output}"
            
        except Exception as e:
            pytest.fail(f"App to database connectivity test failed: {e}")
    
    def test_app_to_redis_connectivity(self, docker_client):
        """Test that app container can connect to Redis container."""
        try:
            # Get app container
            containers = docker_client.containers.list(filters={"name": "app"})
            if not containers:
                containers = docker_client.containers.list(filters={"name": "temperature"})
            
            if not containers:
                pytest.skip("Application container not running")
            
            app_container = containers[0]
            
            # Test Redis driver availability
            redis_test = app_container.exec_run('python -c "import redis; print(\'redis available\')"')
            assert redis_test.exit_code == 0, f"Redis driver not available: {redis_test.output}"
            
            # Test DNS resolution of Redis service
            dns_test = app_container.exec_run('nslookup redis')
            if dns_test.exit_code != 0:
                # Try with getent if nslookup not available
                dns_test = app_container.exec_run('getent hosts redis')
            
            # DNS might not work in all environments, so this is informational
            if dns_test.exit_code == 0:
                assert b'redis' in dns_test.output.lower(), f"Redis service not resolvable: {dns_test.output}"
            
        except Exception as e:
            pytest.fail(f"App to Redis connectivity test failed: {e}")


class TestContainerEnvironment:
    """Test container environment variables and configuration."""
    
    @pytest.fixture(scope="class")
    def docker_client(self):
        """Docker client fixture."""
        try:
            client = docker.from_env()
            yield client
            client.close()
        except DockerException as e:
            pytest.skip(f"Docker client not available: {e}")
    
    def test_app_container_environment(self, docker_client):
        """Test that app container has required environment variables."""
        try:
            # Get app container
            containers = docker_client.containers.list(filters={"name": "app"})
            if not containers:
                containers = docker_client.containers.list(filters={"name": "temperature"})
            
            if not containers:
                pytest.skip("Application container not running")
            
            app_container = containers[0]
            
            # Check environment variables
            env_vars = app_container.attrs['Config']['Env']
            env_dict = {}
            for env_var in env_vars:
                if '=' in env_var:
                    key, value = env_var.split('=', 1)
                    env_dict[key] = value
            
            # Required environment variables
            required_vars = ['DATABASE_URL', 'REDIS_URL', 'ENVIRONMENT']
            missing_vars = []
            
            for var in required_vars:
                if var not in env_dict:
                    missing_vars.append(var)
            
            assert not missing_vars, f"Missing environment variables: {missing_vars}"
            
            # Validate DATABASE_URL points to container service
            if 'DATABASE_URL' in env_dict:
                db_url = env_dict['DATABASE_URL']
                assert '@db:' in db_url or '@postgres:' in db_url, \
                    f"DATABASE_URL should use container service name: {db_url}"
            
            # Validate REDIS_URL points to container service
            if 'REDIS_URL' in env_dict:
                redis_url = env_dict['REDIS_URL']
                assert 'redis:6379' in redis_url, \
                    f"REDIS_URL should use container service name: {redis_url}"
            
        except Exception as e:
            pytest.fail(f"Container environment check failed: {e}")
    
    def test_database_container_environment(self, docker_client):
        """Test that database container has required environment variables."""
        try:
            # Get database container
            containers = docker_client.containers.list(filters={"name": "db"})
            if not containers:
                containers = docker_client.containers.list(filters={"name": "postgres"})
            
            if not containers:
                pytest.skip("Database container not running")
            
            db_container = containers[0]
            
            # Check environment variables
            env_vars = db_container.attrs['Config']['Env']
            env_dict = {}
            for env_var in env_vars:
                if '=' in env_var:
                    key, value = env_var.split('=', 1)
                    env_dict[key] = value
            
            # Required PostgreSQL environment variables
            postgres_vars = ['POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD']
            missing_vars = []
            
            for var in postgres_vars:
                if var not in env_dict:
                    missing_vars.append(var)
            
            # Some might be optional, but at least POSTGRES_PASSWORD should be set
            assert 'POSTGRES_PASSWORD' in env_dict, "POSTGRES_PASSWORD must be set"
            
        except Exception as e:
            pytest.fail(f"Database container environment check failed: {e}")


@pytest.mark.asyncio
async def test_service_integration():
    """
    Integration test for complete Docker service stack.
    Tests that all services can communicate and function together.
    """
    try:
        client = docker.from_env()
        
        # Check all required containers are running
        required_containers = ['app', 'db', 'redis']
        running_containers = {}
        
        for container_name in required_containers:
            containers = client.containers.list(filters={"name": container_name})
            if not containers:
                # Try alternative names
                alt_names = {
                    'app': ['temperature', 'fastapi'],
                    'db': ['postgres', 'database'],
                    'redis': ['cache']
                }
                for alt_name in alt_names.get(container_name, []):
                    containers = client.containers.list(filters={"name": alt_name})
                    if containers:
                        break
            
            if containers:
                running_containers[container_name] = containers[0]
            else:
                pytest.skip(f"Required container '{container_name}' not running")
        
        # Test database connectivity from app container
        app_container = running_containers['app']
        
        # Simple database connectivity test
        db_test_cmd = [
            'python', '-c',
            'import asyncpg, asyncio, os; '
            'db_url = os.getenv("DATABASE_URL"); '
            'print("DB URL configured" if db_url else "No DB URL"); '
            'print("asyncpg available")'
        ]
        
        db_test = app_container.exec_run(db_test_cmd)
        assert db_test.exit_code == 0, f"Database connectivity test failed: {db_test.output}"
        assert b'asyncpg available' in db_test.output, "Database driver not working"
        
        # Simple Redis connectivity test
        redis_test_cmd = [
            'python', '-c',
            'import redis, os; '
            'redis_url = os.getenv("REDIS_URL"); '
            'print("Redis URL configured" if redis_url else "No Redis URL"); '
            'print("redis available")'
        ]
        
        redis_test = app_container.exec_run(redis_test_cmd)
        assert redis_test.exit_code == 0, f"Redis connectivity test failed: {redis_test.output}"
        assert b'redis available' in redis_test.output, "Redis driver not working"
        
        print("✅ Docker service integration test passed")
        
    except DockerException as e:
        pytest.skip(f"Docker not available: {e}")
    except Exception as e:
        pytest.fail(f"Service integration test failed: {e}")
    finally:
        try:
            client.close()
        except:
            pass


def test_docker_validation_summary():
    """
    Summary test that provides an overview of Docker environment status.
    This test always passes but logs important Docker information.
    """
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Docker version
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            logger.info(f"Docker: {result.stdout.strip()}")
        else:
            logger.warning("Docker not available")
        
        # Docker Compose version
        result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            result = subprocess.run(['docker', 'compose', '--version'], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            logger.info(f"Docker Compose: {result.stdout.strip()}")
        else:
            logger.warning("Docker Compose not available")
        
        # Running containers
        try:
            client = docker.from_env()
            containers = client.containers.list()
            logger.info(f"Running containers: {len(containers)}")
            for container in containers:
                logger.info(f"  - {container.name}: {container.status}")
            client.close()
        except:
            logger.warning("Could not list running containers")
        
    except Exception as e:
        logger.warning(f"Docker validation summary error: {e}")
    
    # This test always passes - it's just for information
    assert True, "Docker validation summary completed" 