"""
Database health check module for Temperature Display App.

Provides comprehensive health monitoring for containerized database services.
Following project rules: async operations, Docker integration, performance monitoring,
sub-2-second response targets, and comprehensive error handling.
"""

import asyncio
import os
import time
from typing import Dict, Any, Optional
import logging

from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError

from .connection import get_database_session, create_database_engine

# Configure logging
logger = logging.getLogger(__name__)


async def _ping_database_internal() -> bool:
    """
    Internal ping function without timeout handling.
    """
    async with get_database_session() as session:
        result = await session.execute(text("SELECT 1"))
        row = result.fetchone()
        return row[0] == 1


async def ping_database(timeout: float = 5.0) -> bool:
    """
    Ping database to check basic connectivity.
    
    Following project rules for performance targets and timeout handling.
    
    Args:
        timeout: Maximum time to wait for response in seconds
        
    Returns:
        bool: True if database responds successfully, False otherwise
    """
    try:
        result = await asyncio.wait_for(
            _ping_database_internal(), timeout=timeout
        )
        return result
    except asyncio.TimeoutError:
        logger.warning(f"Database ping timed out after {timeout} seconds")
        return False
    except Exception as e:
        logger.error(f"Database ping failed: {e}")
        return False


async def get_database_health() -> Dict[str, Any]:
    """
    Get detailed database health information with metrics.
    
    Following project rules for comprehensive monitoring and performance tracking.
    
    Returns:
        Dict[str, Any]: Detailed health information including metrics
    """
    start_time = time.time()
    health_info = {
        "status": "unhealthy",
        "response_time_ms": 0,
        "connection_count": 0,
        "database_size": "unknown",
        "error": None,
    }
    
    try:
        async with get_database_session() as session:
            # Test basic connectivity
            await session.execute(text("SELECT 1"))
            
            # Get connection count
            result = await session.execute(text(
                "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
            ))
            health_info["connection_count"] = result.scalar()
            
            # Get database size
            result = await session.execute(text(
                "SELECT pg_size_pretty(pg_database_size(current_database()))"
            ))
            health_info["database_size"] = result.scalar()
            
            # Calculate response time
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            health_info["response_time_ms"] = round(response_time_ms, 2)
            
            # Check if response time meets performance target
            if response_time_ms < 2000:  # 2 second target
                health_info["status"] = "healthy"
            else:
                health_info["status"] = "degraded"
                health_info["error"] = f"Response time {response_time_ms:.2f}ms exceeds 2s target"
            
            logger.info(f"Database health check completed in {response_time_ms:.2f}ms")
            
    except Exception as e:
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        health_info["response_time_ms"] = round(response_time_ms, 2)
        health_info["error"] = str(e)
        logger.error(f"Database health check failed: {e}")
    
    return health_info


async def check_database_availability() -> Dict[str, Any]:
    """
    Check database availability with detailed error information.
    
    Following project rules for graceful degradation and error handling.
    
    Returns:
        Dict[str, Any]: Availability status with error details
    """
    availability_info = {
        "available": False,
        "error": None,
        "error_type": None,
        "retry_suggested": False,
    }
    
    try:
        # Test basic connection
        ping_result = await ping_database(timeout=10.0)
        
        if ping_result:
            availability_info["available"] = True
            logger.info("Database is available")
        else:
            availability_info["error"] = "Database ping failed"
            availability_info["error_type"] = "connectivity"
            availability_info["retry_suggested"] = True
            
    except SQLAlchemyError as e:
        availability_info["error"] = f"SQLAlchemy error: {str(e)}"
        availability_info["error_type"] = "database"
        availability_info["retry_suggested"] = True
        logger.error(f"Database availability check failed with SQLAlchemy error: {e}")
        
    except Exception as e:
        availability_info["error"] = f"Unexpected error: {str(e)}"
        availability_info["error_type"] = "system"
        availability_info["retry_suggested"] = False
        logger.error(f"Database availability check failed with unexpected error: {e}")
    
    return availability_info


async def get_all_health_status() -> Dict[str, Any]:
    """
    Get combined health status for all database services.
    
    Following project rules for comprehensive monitoring and container orchestration.
    
    Returns:
        Dict[str, Any]: Combined health status for PostgreSQL and Redis
    """
    health_status = {
        "postgres": {
            "status": "unknown",
            "response_time_ms": 0,
            "error": None,
        },
        "redis": {
            "status": "unknown", 
            "response_time_ms": 0,
            "error": None,
        },
        "overall": {
            "status": "unknown",
            "healthy_services": 0,
            "total_services": 2,
        }
    }
    
    # Check PostgreSQL health
    try:
        postgres_health = await get_database_health()
        health_status["postgres"] = {
            "status": postgres_health["status"],
            "response_time_ms": postgres_health["response_time_ms"],
            "error": postgres_health.get("error"),
        }
    except Exception as e:
        health_status["postgres"]["error"] = str(e)
        health_status["postgres"]["status"] = "unhealthy"
    
    # Check Redis health (import here to avoid circular imports)
    try:
        from .cache import get_redis_health
        redis_health = await get_redis_health()
        health_status["redis"] = {
            "status": redis_health["status"],
            "response_time_ms": redis_health["response_time_ms"],
            "error": redis_health.get("error"),
        }
    except Exception as e:
        health_status["redis"]["error"] = str(e)
        health_status["redis"]["status"] = "unhealthy"
    
    # Calculate overall status
    healthy_services = sum(
        1 for service in ["postgres", "redis"]
        if health_status[service]["status"] == "healthy"
    )
    
    health_status["overall"]["healthy_services"] = healthy_services
    
    if healthy_services == 2:
        health_status["overall"]["status"] = "healthy"
    elif healthy_services == 1:
        health_status["overall"]["status"] = "degraded"
    else:
        health_status["overall"]["status"] = "unhealthy"
    
    logger.info(f"Overall health status: {health_status['overall']['status']} "
                f"({healthy_services}/2 services healthy)")
    
    return health_status


async def readiness_probe() -> bool:
    """
    Kubernetes-style readiness probe for container orchestration.
    
    Following project rules for Docker integration and container health checks.
    
    Returns:
        bool: True if application is ready to receive traffic, False otherwise
    """
    try:
        # Check if database is available and responsive
        health_info = await get_database_health()
        
        # Application is ready if database is healthy or degraded (but not unhealthy)
        is_ready = health_info["status"] in ["healthy", "degraded"]
        
        if is_ready:
            logger.debug("Readiness probe: Application is ready")
        else:
            logger.warning(f"Readiness probe: Application not ready - {health_info.get('error', 'Unknown error')}")
        
        return is_ready
        
    except Exception as e:
        logger.error(f"Readiness probe failed: {e}")
        return False


async def liveness_probe() -> bool:
    """
    Kubernetes-style liveness probe for container orchestration.
    
    Following project rules for Docker integration and container health monitoring.
    
    Returns:
        bool: True if application is alive and should not be restarted, False otherwise
    """
    try:
        # Basic application liveness check
        # For database module, we check if we can create a database engine
        engine = create_database_engine()
        
        # Application is alive if engine can be created (doesn't require actual connection)
        is_alive = engine is not None
        
        if is_alive:
            logger.debug("Liveness probe: Application is alive")
        else:
            logger.error("Liveness probe: Application is not alive - cannot create database engine")
        
        return is_alive
        
    except Exception as e:
        logger.error(f"Liveness probe failed: {e}")
        return False


async def get_database_metrics() -> Dict[str, Any]:
    """
    Get detailed database metrics for monitoring and alerting.
    
    Following project rules for performance monitoring and observability.
    
    Returns:
        Dict[str, Any]: Detailed database metrics
    """
    metrics = {
        "connections": {
            "active": 0,
            "idle": 0,
            "total": 0,
        },
        "performance": {
            "avg_query_time_ms": 0,
            "slow_queries": 0,
        },
        "storage": {
            "database_size_bytes": 0,
            "table_count": 0,
        },
        "health": {
            "last_check_time": time.time(),
            "status": "unknown",
        }
    }
    
    try:
        async with get_database_session() as session:
            # Get connection statistics
            result = await session.execute(text("""
                SELECT 
                    state,
                    count(*) as count
                FROM pg_stat_activity 
                WHERE datname = current_database()
                GROUP BY state
            """))
            
            for row in result:
                state, count = row
                if state == 'active':
                    metrics["connections"]["active"] = count
                elif state == 'idle':
                    metrics["connections"]["idle"] = count
            
            metrics["connections"]["total"] = (
                metrics["connections"]["active"] + metrics["connections"]["idle"]
            )
            
            # Get database size in bytes
            result = await session.execute(text(
                "SELECT pg_database_size(current_database())"
            ))
            metrics["storage"]["database_size_bytes"] = result.scalar()
            
            # Get table count
            result = await session.execute(text("""
                SELECT count(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            metrics["storage"]["table_count"] = result.scalar()
            
            metrics["health"]["status"] = "healthy"
            
    except Exception as e:
        logger.error(f"Failed to collect database metrics: {e}")
        metrics["health"]["status"] = "error"
        metrics["health"]["error"] = str(e)
    
    return metrics 