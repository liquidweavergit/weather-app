"""
Database package for Temperature Display App.

This package contains database connection, health check, and caching modules
for containerized PostgreSQL and Redis services.
Following project rules for async operations and Docker integration.
"""

from .connection import (
    create_database_engine,
    get_database_session,
    get_session_factory,
    test_connection,
    connect_with_retry,
    get_pool_status,
    test_connection_recovery,
    connect_with_timeout,
    time_connection_establishment,
    test_concurrent_connections,
)

from .health import (
    ping_database,
    get_database_health,
    check_database_availability,
    get_all_health_status,
    readiness_probe,
    liveness_probe,
)

from .cache import (
    ping_redis,
    get_redis_client,
    get_redis_health,
)

__all__ = [
    # Connection functions
    "create_database_engine",
    "get_database_session", 
    "get_session_factory",
    "test_connection",
    "connect_with_retry",
    "get_pool_status",
    "test_connection_recovery",
    "connect_with_timeout",
    "time_connection_establishment",
    "test_concurrent_connections",
    # Health check functions
    "ping_database",
    "get_database_health",
    "check_database_availability",
    "get_all_health_status",
    "readiness_probe",
    "liveness_probe",
    # Cache functions
    "ping_redis",
    "get_redis_client",
    "get_redis_health",
] 