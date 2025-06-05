"""
Pytest configuration and shared fixtures for Temperature Display App tests.
"""

import asyncio
import os
import sys
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio


# Add the app directory to the Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create an instance of the default event loop for the test session.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_environment_variables() -> dict:
    """
    Set up test environment variables.
    Returns a dictionary of test environment variables.
    """
    test_env = {
        'ENVIRONMENT': 'testing',
        'DATABASE_URL': 'postgresql+asyncpg://test:test@localhost:5432/test_temperature_app',
        'REDIS_URL': 'redis://localhost:6379/1',  # Use different Redis DB for tests
        'SECRET_KEY': 'test_secret_key_minimum_32_characters_long_for_testing',
        'WEATHER_API_KEY': 'test_weather_api_key',
        'LOG_LEVEL': 'DEBUG',
        'DEBUG': 'true'
    }
    
    # Set environment variables for tests
    for key, value in test_env.items():
        os.environ[key] = value
    
    yield test_env
    
    # Clean up environment variables after tests
    for key in test_env.keys():
        os.environ.pop(key, None)


@pytest.fixture
def clean_environment():
    """
    Provide a clean environment for environment validation tests.
    This fixture temporarily removes all environment variables and restores them after.
    """
    # Save current environment
    original_env = dict(os.environ)
    
    # Clear environment variables that might interfere with tests
    test_vars = [
        'DATABASE_URL', 'REDIS_URL', 'WEATHER_API_KEY', 
        'SECRET_KEY', 'ENVIRONMENT', 'DEBUG'
    ]
    
    saved_values = {}
    for var in test_vars:
        if var in os.environ:
            saved_values[var] = os.environ[var]
            del os.environ[var]
    
    yield
    
    # Restore environment variables
    for var, value in saved_values.items():
        os.environ[var] = value


@pytest.fixture
def mock_environment_variables():
    """
    Provide mock environment variables for testing.
    """
    mock_env = {
        'DATABASE_URL': 'postgresql+asyncpg://user:pass@localhost:5432/testdb',
        'REDIS_URL': 'redis://localhost:6379/0',
        'WEATHER_API_KEY': 'test_weather_api_key_1234567890',
        'SECRET_KEY': 'test_secret_key_with_minimum_32_characters',
        'ENVIRONMENT': 'testing'
    }
    
    # Save original values
    original_values = {}
    for key in mock_env:
        original_values[key] = os.environ.get(key)
    
    # Set mock values
    for key, value in mock_env.items():
        os.environ[key] = value
    
    yield mock_env
    
    # Restore original values
    for key, original_value in original_values.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


def pytest_configure(config):
    """
    Configure pytest with custom markers and settings.
    """
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "external: mark test as requiring external services"
    )


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to add markers based on test location and names.
    """
    for item in items:
        # Add markers based on file location
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Add markers based on test names
        if "slow" in item.name:
            item.add_marker(pytest.mark.slow)
        if "external" in item.name or "connection" in item.name:
            item.add_marker(pytest.mark.external)


def pytest_sessionstart(session):
    """
    Called after the Session object has been created.
    """
    print("\n" + "="*80)
    print("Temperature Display App - Test Suite")
    print("="*80)


def pytest_sessionfinish(session, exitstatus):
    """
    Called after whole test run finished.
    """
    print("\n" + "="*80)
    print(f"Test session finished with exit status: {exitstatus}")
    print("="*80) 