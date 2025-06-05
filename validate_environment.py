#!/usr/bin/env python3
"""
Standalone environment validation script for Temperature Display App.
This script can run without pytest to validate basic environment setup.
"""

import os
import sys
import platform
import subprocess
from typing import List, Tuple


def check_python_version() -> Tuple[bool, str]:
    """Check if Python version meets requirements."""
    version = sys.version_info
    if version.major != 3:
        return False, f"Python 3.x required, got {version.major}.{version.minor}"
    if version.minor < 11:
        return False, f"Python 3.11+ required, got {version.major}.{version.minor}"
    return True, f"Python {version.major}.{version.minor}.{version.micro}"


def check_virtual_environment() -> Tuple[bool, str]:
    """Check if virtual environment is active."""
    in_venv = (
        hasattr(sys, 'real_prefix') or 
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    )
    if in_venv:
        return True, "Virtual environment active"
    return False, "Virtual environment not detected"


def check_platform() -> Tuple[bool, str]:
    """Check if platform is supported."""
    supported_platforms = ['linux', 'darwin', 'win32']
    current_platform = sys.platform
    if current_platform in supported_platforms:
        return True, f"Platform: {current_platform} ({platform.system()})"
    return False, f"Unsupported platform: {current_platform}"


def check_dependencies() -> List[Tuple[bool, str]]:
    """Check if critical dependencies can be imported."""
    dependencies = [
        ('fastapi', 'FastAPI'),
        ('sqlalchemy', 'SQLAlchemy'),
        ('pydantic', 'Pydantic'),
        ('httpx', 'HTTPX'),
        ('redis', 'Redis'),
        ('asyncpg', 'asyncpg'),
        ('alembic', 'Alembic'),
        ('structlog', 'structlog'),
        ('pytest', 'pytest'),
    ]
    
    results = []
    for module, name in dependencies:
        try:
            __import__(module)
            results.append((True, f"{name} available"))
        except ImportError:
            results.append((False, f"{name} not installed"))
    
    return results


def check_environment_variables() -> List[Tuple[bool, str]]:
    """Check environment variable configuration."""
    vars_to_check = [
        ('DATABASE_URL', 'Database URL'),
        ('REDIS_URL', 'Redis URL'),
        ('WEATHER_API_KEY', 'Weather API key'),
        ('SECRET_KEY', 'Secret key'),
        ('ENVIRONMENT', 'Environment name'),
    ]
    
    results = []
    for var, description in vars_to_check:
        value = os.getenv(var)
        if value:
            results.append((True, f"{description} configured"))
        else:
            results.append((False, f"{description} not set (optional for initial setup)"))
    
    return results


def check_development_tools() -> List[Tuple[bool, str]]:
    """Check development tools availability."""
    tools = [
        ('black', 'Code formatter'),
        ('mypy', 'Type checker'),
    ]
    
    results = []
    for tool, description in tools:
        try:
            result = subprocess.run([tool, '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                results.append((True, f"{description} available"))
            else:
                results.append((False, f"{description} command failed"))
        except (subprocess.TimeoutExpired, FileNotFoundError):
            results.append((False, f"{description} not installed"))
    
    return results


def check_file_system() -> Tuple[bool, str]:
    """Check file system permissions."""
    test_file = 'test_write_permissions.tmp'
    try:
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        return True, "Project directory is writable"
    except (OSError, IOError) as e:
        return False, f"Project directory not writable: {e}"


def print_result(passed: bool, message: str, indent: int = 0):
    """Print a test result with appropriate formatting."""
    icon = "✅" if passed else "❌"
    spaces = "  " * indent
    print(f"{spaces}{icon} {message}")


def main():
    """Run all environment validation checks."""
    print("=" * 80)
    print("Temperature Display App - Environment Validation")
    print("=" * 80)
    
    all_passed = True
    
    # Core environment checks
    print("\n🔍 Core Environment:")
    passed, message = check_python_version()
    print_result(passed, message, 1)
    if not passed:
        all_passed = False
    
    passed, message = check_virtual_environment()
    print_result(passed, message, 1)
    
    passed, message = check_platform()
    print_result(passed, message, 1)
    if not passed:
        all_passed = False
    
    passed, message = check_file_system()
    print_result(passed, message, 1)
    if not passed:
        all_passed = False
    
    # Dependencies check
    print("\n📦 Dependencies:")
    dependency_results = check_dependencies()
    critical_deps_passed = 0
    for passed, message in dependency_results:
        print_result(passed, message, 1)
        if passed:
            critical_deps_passed += 1
    
    if critical_deps_passed < len(dependency_results):
        print(f"    ⚠️  {critical_deps_passed}/{len(dependency_results)} dependencies available")
        print("    💡 Run: pip install -r requirements.txt")
    
    # Environment variables
    print("\n🔧 Environment Variables:")
    env_results = check_environment_variables()
    for passed, message in env_results:
        print_result(passed, message, 1)
    
    # Development tools
    print("\n🛠️  Development Tools:")
    tool_results = check_development_tools()
    for passed, message in tool_results:
        print_result(passed, message, 1)
    
    # Summary
    print("\n" + "=" * 80)
    if all_passed and critical_deps_passed == len(dependency_results):
        print("🎉 Environment validation PASSED! Ready for development.")
        print("\nNext steps:")
        print("  1. ✅ Environment validation complete")
        print("  2. ⏳ Run: git init")
        print("  3. ⏳ Run: pytest tests/test_environment.py")
    else:
        print("⚠️  Environment validation found issues.")
        print("\nRecommended actions:")
        if not all_passed:
            print("  1. Fix Python version or virtual environment issues")
        if critical_deps_passed < len(dependency_results):
            print("  2. Install missing dependencies: pip install -r requirements.txt")
        print("  3. Configure environment variables (copy env.example to .env)")
        print("  4. Re-run this validation: python validate_environment.py")
    
    print("=" * 80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main()) 