#!/usr/bin/env python3
"""
Docker Environment Validation for Temperature Display App.
This script validates Docker containers, services, and environment configuration.
"""

import os
import sys
import subprocess
import json
import time
import socket
from typing import List, Tuple, Dict, Optional
from pathlib import Path
import requests


def run_command(command: List[str], timeout: int = 30) -> Tuple[bool, str, str]:
    """Run a command and return success status, stdout, and stderr."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        return False, "", str(e)


def check_docker_installation() -> Tuple[bool, str]:
    """Check if Docker is installed and accessible."""
    success, stdout, stderr = run_command(["docker", "--version"])
    if success:
        return True, f"Docker installed: {stdout}"
    return False, f"Docker not available: {stderr}"


def check_docker_compose_installation() -> Tuple[bool, str]:
    """Check if Docker Compose is installed and accessible."""
    success, stdout, stderr = run_command(["docker-compose", "--version"])
    if success:
        return True, f"Docker Compose installed: {stdout}"
    return False, f"Docker Compose not available: {stderr}"


def check_docker_daemon() -> Tuple[bool, str]:
    """Check if Docker daemon is running."""
    success, stdout, stderr = run_command(["docker", "info"])
    if success:
        lines = stdout.split('\n')
        for line in lines:
            if 'Server Version:' in line:
                return True, f"Docker daemon running: {line.strip()}"
        return True, "Docker daemon running"
    return False, f"Docker daemon not running: {stderr}"


def check_docker_compose_files() -> List[Tuple[bool, str]]:
    """Check if Docker Compose files exist and are valid."""
    compose_files = [
        ("docker-compose.yml", "Development environment"),
        ("docker-compose.prod.yml", "Production environment"),
        ("docker-compose.test.yml", "Testing environment")
    ]
    
    results = []
    for filename, description in compose_files:
        if Path(filename).exists():
            # Validate compose file syntax
            success, stdout, stderr = run_command([
                "docker-compose", "-f", filename, "config", "--quiet"
            ])
            if success:
                results.append((True, f"{description}: {filename} valid"))
            else:
                results.append((False, f"{description}: {filename} invalid - {stderr}"))
        else:
            results.append((False, f"{description}: {filename} not found"))
    
    return results


def check_environment_files() -> List[Tuple[bool, str]]:
    """Check environment configuration files."""
    env_files = [
        ("env.example", "Environment template", True),
        ("env.dev.template", "Development template", True),
        ("env.prod.template", "Production template", True),
        ("env.test.template", "Testing template", True),
        (".env", "Development environment", False),
        (".env.prod", "Production environment", False),
        (".env.test", "Testing environment", False),
    ]
    
    results = []
    for filename, description, required in env_files:
        if Path(filename).exists():
            # Check if file has content
            try:
                with open(filename, 'r') as f:
                    content = f.read().strip()
                    if content:
                        results.append((True, f"{description}: {filename} exists and has content"))
                    else:
                        results.append((False, f"{description}: {filename} exists but is empty"))
            except Exception as e:
                results.append((False, f"{description}: Error reading {filename} - {e}"))
        else:
            if required:
                results.append((False, f"{description}: {filename} missing (required template)"))
            else:
                results.append((True, f"{description}: {filename} not found (optional)"))
    
    return results


def check_docker_network() -> Tuple[bool, str]:
    """Check Docker network configuration."""
    success, stdout, stderr = run_command(["docker", "network", "ls"])
    if success:
        return True, "Docker networking available"
    return False, f"Docker network check failed: {stderr}"


def check_docker_volumes() -> List[Tuple[bool, str]]:
    """Check Docker volume configuration."""
    success, stdout, stderr = run_command(["docker", "volume", "ls"])
    if not success:
        return [(False, f"Docker volume check failed: {stderr}")]
    
    results = [(True, "Docker volumes accessible")]
    
    # Check for project-specific volumes if they exist
    if "temperature_postgres_data" in stdout:
        results.append((True, "PostgreSQL data volume exists"))
    if "temperature_redis_data" in stdout:
        results.append((True, "Redis data volume exists"))
    
    return results


def check_container_status(environment: str = "dev") -> List[Tuple[bool, str]]:
    """Check status of running containers for specified environment."""
    compose_file_map = {
        "dev": "docker-compose.yml",
        "prod": "docker-compose.prod.yml",
        "test": "docker-compose.test.yml"
    }
    
    compose_file = compose_file_map.get(environment)
    if not compose_file or not Path(compose_file).exists():
        return [(False, f"Compose file for {environment} not found")]
    
    # Check if containers are running
    success, stdout, stderr = run_command([
        "docker-compose", "-f", compose_file, "ps", "--services"
    ])
    
    if not success:
        return [(False, f"Failed to check {environment} services: {stderr}")]
    
    services = stdout.split('\n') if stdout else []
    results = []
    
    for service in services:
        if service.strip():
            # Check individual service status
            success, stdout, stderr = run_command([
                "docker-compose", "-f", compose_file, "ps", service
            ])
            if success and "Up" in stdout:
                results.append((True, f"{environment.title()} service '{service}' is running"))
            elif success and stdout:
                results.append((False, f"{environment.title()} service '{service}' is not running"))
            else:
                results.append((False, f"{environment.title()} service '{service}' status unknown"))
    
    return results


def check_service_connectivity(environment: str = "dev") -> List[Tuple[bool, str]]:
    """Check connectivity to running services."""
    service_ports = {
        "app": 8000,
        "db": 5432,
        "redis": 6379,
        "pgadmin": 5050,
        "redis-commander": 8081
    }
    
    results = []
    host = "localhost"
    
    for service, port in service_ports.items():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                if result == 0:
                    results.append((True, f"Service '{service}' accessible on port {port}"))
                else:
                    results.append((False, f"Service '{service}' not accessible on port {port}"))
        except Exception as e:
            results.append((False, f"Error checking service '{service}': {e}"))
    
    return results


def check_application_health() -> Tuple[bool, str]:
    """Check application health endpoint."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            return True, "Application health check passed"
        else:
            return False, f"Application health check failed: HTTP {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Application not accessible (connection refused)"
    except requests.exceptions.Timeout:
        return False, "Application health check timed out"
    except Exception as e:
        return False, f"Application health check error: {e}"


def check_database_connectivity() -> Tuple[bool, str]:
    """Check database connectivity via application."""
    try:
        response = requests.get("http://localhost:8000/health/db", timeout=10)
        if response.status_code == 200:
            return True, "Database connectivity check passed"
        else:
            return False, f"Database connectivity check failed: HTTP {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot check database connectivity (application not accessible)"
    except Exception as e:
        return False, f"Database connectivity check error: {e}"


def check_redis_connectivity() -> Tuple[bool, str]:
    """Check Redis connectivity via application."""
    try:
        response = requests.get("http://localhost:8000/health/redis", timeout=10)
        if response.status_code == 200:
            return True, "Redis connectivity check passed"
        else:
            return False, f"Redis connectivity check failed: HTTP {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot check Redis connectivity (application not accessible)"
    except Exception as e:
        return False, f"Redis connectivity check error: {e}"


def check_docker_resources() -> List[Tuple[bool, str]]:
    """Check Docker resource usage and limits."""
    success, stdout, stderr = run_command(["docker", "system", "df"])
    if not success:
        return [(False, f"Docker resource check failed: {stderr}")]
    
    results = [(True, "Docker system resources accessible")]
    
    # Check for available disk space
    lines = stdout.split('\n')
    for line in lines:
        if 'Local Volumes' in line:
            parts = line.split()
            if len(parts) >= 4:
                size = parts[2]
                results.append((True, f"Docker volumes using {size} of disk space"))
    
    return results


def check_docker_images() -> List[Tuple[bool, str]]:
    """Check if required Docker images exist."""
    required_images = [
        "postgres:15-alpine",
        "redis:7-alpine"
    ]
    
    success, stdout, stderr = run_command(["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"])
    if not success:
        return [(False, f"Docker images check failed: {stderr}")]
    
    available_images = set(stdout.split('\n')) if stdout else set()
    results = []
    
    for image in required_images:
        if image in available_images:
            results.append((True, f"Required image '{image}' available"))
        else:
            results.append((False, f"Required image '{image}' not found"))
    
    # Check for application images
    app_images = [img for img in available_images if 'temperature-app' in img]
    if app_images:
        results.append((True, f"Application images found: {len(app_images)}"))
    else:
        results.append((False, "No application images found"))
    
    return results


def validate_environment_variables(env_file: str = ".env") -> List[Tuple[bool, str]]:
    """Validate environment variables from specified file."""
    if not Path(env_file).exists():
        return [(False, f"Environment file {env_file} not found")]
    
    required_vars = [
        "ENVIRONMENT",
        "DATABASE_URL",
        "REDIS_URL", 
        "SECRET_KEY",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD"
    ]
    
    results = []
    env_vars = {}
    
    try:
        with open(env_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except Exception as e:
        return [(False, f"Error reading {env_file}: {e}")]
    
    for var in required_vars:
        if var in env_vars:
            value = env_vars[var]
            if value and value not in ['your_api_key_here', 'password', 'changeme']:
                results.append((True, f"Environment variable '{var}' configured"))
            else:
                results.append((False, f"Environment variable '{var}' needs proper value"))
        else:
            results.append((False, f"Environment variable '{var}' missing"))
    
    # Check for sensitive defaults
    sensitive_checks = [
        ("SECRET_KEY", ["dev-secret", "test-secret", "change"]),
        ("POSTGRES_PASSWORD", ["password", "changeme", "admin"]),
        ("REDIS_PASSWORD", ["password", "changeme", "admin"])
    ]
    
    for var, bad_values in sensitive_checks:
        if var in env_vars:
            value = env_vars[var].lower()
            if any(bad in value for bad in bad_values):
                results.append((False, f"Environment variable '{var}' uses insecure default"))
    
    return results


def print_result(passed: bool, message: str, indent: int = 0):
    """Print a test result with appropriate formatting."""
    icon = "✅" if passed else "❌"
    spaces = "  " * indent
    print(f"{spaces}{icon} {message}")


def main():
    """Run all Docker environment validation checks."""
    print("=" * 80)
    print("Temperature Display App - Docker Environment Validation")
    print("=" * 80)
    
    environment = sys.argv[1] if len(sys.argv) > 1 else "dev"
    if environment not in ["dev", "prod", "test"]:
        print(f"❌ Invalid environment: {environment}")
        print("Valid environments: dev, prod, test")
        return 1
    
    all_passed = True
    
    # Docker Installation
    print("\n🐳 Docker Installation:")
    passed, message = check_docker_installation()
    print_result(passed, message, 1)
    if not passed:
        all_passed = False
    
    passed, message = check_docker_compose_installation()
    print_result(passed, message, 1)
    if not passed:
        all_passed = False
    
    passed, message = check_docker_daemon()
    print_result(passed, message, 1)
    if not passed:
        all_passed = False
        print("    💡 Start Docker daemon: systemctl start docker (Linux) or Docker Desktop")
    
    # Docker Configuration
    print("\n📋 Docker Configuration:")
    compose_results = check_docker_compose_files()
    for passed, message in compose_results:
        print_result(passed, message, 1)
        if not passed:
            all_passed = False
    
    env_results = check_environment_files()
    for passed, message in env_results:
        print_result(passed, message, 1)
    
    # Docker Resources
    print("\n💾 Docker Resources:")
    passed, message = check_docker_network()
    print_result(passed, message, 1)
    if not passed:
        all_passed = False
    
    volume_results = check_docker_volumes()
    for passed, message in volume_results:
        print_result(passed, message, 1)
    
    resource_results = check_docker_resources()
    for passed, message in resource_results:
        print_result(passed, message, 1)
    
    # Docker Images
    print("\n🏗️  Docker Images:")
    image_results = check_docker_images()
    for passed, message in image_results:
        print_result(passed, message, 1)
    
    # Environment Variables
    print(f"\n🔧 Environment Variables ({environment}):")
    env_file = f".env.{environment}" if environment != "dev" else ".env"
    env_var_results = validate_environment_variables(env_file)
    for passed, message in env_var_results:
        print_result(passed, message, 1)
    
    # Container Status (if any are running)
    print(f"\n🚀 Container Status ({environment}):")
    container_results = check_container_status(environment)
    for passed, message in container_results:
        print_result(passed, message, 1)
    
    # Service Connectivity (if containers are running)
    print(f"\n🌐 Service Connectivity ({environment}):")
    connectivity_results = check_service_connectivity(environment)
    running_services = sum(1 for passed, _ in connectivity_results if passed)
    
    if running_services > 0:
        for passed, message in connectivity_results:
            print_result(passed, message, 1)
        
        # Application Health (if app is running)
        if running_services >= 3:  # app, db, redis
            print(f"\n🏥 Application Health ({environment}):")
            passed, message = check_application_health()
            print_result(passed, message, 1)
            
            passed, message = check_database_connectivity()
            print_result(passed, message, 1)
            
            passed, message = check_redis_connectivity()
            print_result(passed, message, 1)
    else:
        print("    ℹ️  No services running. Start with: ./docker-manage.sh start " + environment)
    
    # Summary
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 Docker environment validation PASSED!")
        print(f"\nEnvironment '{environment}' is ready for use.")
        print("\nNext steps:")
        if running_services == 0:
            print(f"  1. Start services: ./docker-manage.sh start {environment}")
        print("  2. Run tests: ./docker-manage.sh test unit")
        print("  3. Check logs: ./docker-manage.sh logs " + environment)
    else:
        print("⚠️  Docker environment validation found issues.")
        print("\nRecommended actions:")
        print("  1. Install Docker and Docker Compose if missing")
        print("  2. Start Docker daemon")
        print("  3. Fix Docker Compose file syntax errors")
        print("  4. Configure environment variables")
        print("  5. Re-run validation: python validate_docker_environment.py " + environment)
    
    print("=" * 80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main()) 