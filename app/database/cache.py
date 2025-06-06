"""
Redis cache module for Temperature Display App.

Provides async Redis connection management for containerized Redis.
Following project rules: async operations, Docker integration, error resilience,
performance monitoring, and comprehensive health checks.
"""

import asyncio
import os
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any, Optional
import logging

import redis.asyncio as aioredis
from redis.exceptions import RedisError, ConnectionError, TimeoutError

# Configure logging
logger = logging.getLogger(__name__)

# Global Redis client instance (singleton pattern for containerized environment)
_redis_client: Optional[aioredis.Redis] = None


def _get_redis_url() -> str:
    """
    Get Redis URL from environment variables.
    
    Returns:
        str: Redis connection URL
        
    Raises:
        ValueError: If REDIS_URL environment variable is not set
    """
    redis_url = os.getenv('REDIS_URL')
    if not redis_url:
        raise ValueError("REDIS_URL environment variable is required")
    return redis_url


async def _create_redis_client() -> aioredis.Redis:
    """
    Create Redis client with Docker-optimized configuration.
    
    Following project rules for containerized environment and performance optimization.
    
    Returns:
        aioredis.Redis: Configured async Redis client
    """
    global _redis_client
    
    if _redis_client is not None:
        return _redis_client
    
    redis_url = _get_redis_url()
    
    # Docker-optimized Redis client settings
    _redis_client = aioredis.from_url(
        redis_url,
        # Connection settings for containerized environment
        max_connections=20,  # Connection pool size
        retry_on_timeout=True,  # Retry on timeout
        retry_on_error=[ConnectionError, TimeoutError],  # Retry on specific errors
        health_check_interval=30,  # Health check every 30 seconds
        # Performance settings
        socket_timeout=5.0,  # Socket timeout
        socket_connect_timeout=5.0,  # Connection timeout
        socket_keepalive=True,  # Keep connections alive
        socket_keepalive_options={},  # Default keepalive options
        # Encoding settings
        decode_responses=True,  # Decode responses to strings
        encoding='utf-8',  # Use UTF-8 encoding
    )
    
    logger.info("Redis client created successfully")
    return _redis_client


@asynccontextmanager
async def get_redis_client() -> AsyncGenerator[aioredis.Redis, None]:
    """
    Async context manager for Redis client.
    
    Provides automatic client management with proper cleanup and error handling.
    Following project rules for comprehensive error handling.
    
    Yields:
        aioredis.Redis: Redis client with automatic cleanup
    """
    client = await _create_redis_client()
    
    try:
        logger.debug("Redis client session started")
        yield client
        logger.debug("Redis client session completed successfully")
    except Exception as e:
        logger.error(f"Redis client session error: {e}")
        raise
    finally:
        # Note: We don't close the client here as it's a singleton
        # The connection pool will manage connections automatically
        logger.debug("Redis client session ended")


async def ping_redis() -> bool:
    """
    Ping Redis to check basic connectivity.
    
    Following project rules for performance targets and timeout handling.
    
    Returns:
        bool: True if Redis responds successfully, False otherwise
    """
    try:
        async with get_redis_client() as redis_client:
            result = await redis_client.ping()
            return result is True
    except Exception as e:
        logger.error(f"Redis ping failed: {e}")
        return False


async def get_redis_health() -> Dict[str, Any]:
    """
    Get detailed Redis health information with metrics.
    
    Following project rules for comprehensive monitoring and performance tracking.
    
    Returns:
        Dict[str, Any]: Detailed health information including metrics
    """
    start_time = time.time()
    health_info = {
        "status": "unhealthy",
        "response_time_ms": 0,
        "memory_usage": "unknown",
        "connected_clients": 0,
        "error": None,
    }
    
    try:
        async with get_redis_client() as redis_client:
            # Test basic connectivity
            await redis_client.ping()
            
            # Get Redis info
            info = await redis_client.info()
            
            # Extract relevant metrics
            health_info["memory_usage"] = info.get("used_memory_human", "unknown")
            health_info["connected_clients"] = info.get("connected_clients", 0)
            
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
            
            logger.info(f"Redis health check completed in {response_time_ms:.2f}ms")
            
    except RedisError as e:
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        health_info["response_time_ms"] = round(response_time_ms, 2)
        health_info["error"] = f"Redis error: {str(e)}"
        logger.error(f"Redis health check failed with Redis error: {e}")
        
    except Exception as e:
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        health_info["response_time_ms"] = round(response_time_ms, 2)
        health_info["error"] = str(e)
        logger.error(f"Redis health check failed: {e}")
    
    return health_info


async def test_redis_operations() -> bool:
    """
    Test basic Redis operations (set, get, delete).
    
    Returns:
        bool: True if all operations successful, False otherwise
    """
    test_key = "health_check_test_key"
    test_value = "health_check_test_value"
    
    try:
        async with get_redis_client() as redis_client:
            # Test SET operation
            await redis_client.set(test_key, test_value, ex=10)  # 10 second expiry
            
            # Test GET operation
            retrieved_value = await redis_client.get(test_key)
            if retrieved_value != test_value:
                logger.error(f"Redis GET operation failed: expected {test_value}, got {retrieved_value}")
                return False
            
            # Test DELETE operation
            await redis_client.delete(test_key)
            
            # Verify deletion
            deleted_value = await redis_client.get(test_key)
            if deleted_value is not None:
                logger.error(f"Redis DELETE operation failed: key still exists with value {deleted_value}")
                return False
            
            logger.debug("Redis operations test completed successfully")
            return True
            
    except Exception as e:
        logger.error(f"Redis operations test failed: {e}")
        return False


async def get_redis_metrics() -> Dict[str, Any]:
    """
    Get detailed Redis metrics for monitoring and alerting.
    
    Following project rules for performance monitoring and observability.
    
    Returns:
        Dict[str, Any]: Detailed Redis metrics
    """
    metrics = {
        "memory": {
            "used_memory_bytes": 0,
            "used_memory_human": "unknown",
            "max_memory_bytes": 0,
            "memory_usage_percentage": 0,
        },
        "connections": {
            "connected_clients": 0,
            "blocked_clients": 0,
            "total_connections_received": 0,
        },
        "performance": {
            "total_commands_processed": 0,
            "instantaneous_ops_per_sec": 0,
            "keyspace_hits": 0,
            "keyspace_misses": 0,
            "hit_rate_percentage": 0,
        },
        "persistence": {
            "rdb_last_save_time": 0,
            "rdb_changes_since_last_save": 0,
        },
        "health": {
            "last_check_time": time.time(),
            "status": "unknown",
        }
    }
    
    try:
        async with get_redis_client() as redis_client:
            # Get comprehensive Redis info
            info = await redis_client.info()
            
            # Memory metrics
            metrics["memory"]["used_memory_bytes"] = info.get("used_memory", 0)
            metrics["memory"]["used_memory_human"] = info.get("used_memory_human", "unknown")
            metrics["memory"]["max_memory_bytes"] = info.get("maxmemory", 0)
            
            if metrics["memory"]["max_memory_bytes"] > 0:
                usage_percentage = (metrics["memory"]["used_memory_bytes"] / 
                                  metrics["memory"]["max_memory_bytes"]) * 100
                metrics["memory"]["memory_usage_percentage"] = round(usage_percentage, 2)
            
            # Connection metrics
            metrics["connections"]["connected_clients"] = info.get("connected_clients", 0)
            metrics["connections"]["blocked_clients"] = info.get("blocked_clients", 0)
            metrics["connections"]["total_connections_received"] = info.get("total_connections_received", 0)
            
            # Performance metrics
            metrics["performance"]["total_commands_processed"] = info.get("total_commands_processed", 0)
            metrics["performance"]["instantaneous_ops_per_sec"] = info.get("instantaneous_ops_per_sec", 0)
            metrics["performance"]["keyspace_hits"] = info.get("keyspace_hits", 0)
            metrics["performance"]["keyspace_misses"] = info.get("keyspace_misses", 0)
            
            # Calculate hit rate
            total_requests = metrics["performance"]["keyspace_hits"] + metrics["performance"]["keyspace_misses"]
            if total_requests > 0:
                hit_rate = (metrics["performance"]["keyspace_hits"] / total_requests) * 100
                metrics["performance"]["hit_rate_percentage"] = round(hit_rate, 2)
            
            # Persistence metrics
            metrics["persistence"]["rdb_last_save_time"] = info.get("rdb_last_save_time", 0)
            metrics["persistence"]["rdb_changes_since_last_save"] = info.get("rdb_changes_since_last_save", 0)
            
            metrics["health"]["status"] = "healthy"
            
    except Exception as e:
        logger.error(f"Failed to collect Redis metrics: {e}")
        metrics["health"]["status"] = "error"
        metrics["health"]["error"] = str(e)
    
    return metrics


async def cleanup_redis_client():
    """
    Cleanup Redis client and connections.
    
    Should be called during application shutdown.
    """
    global _redis_client
    
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis client closed successfully")


async def test_redis_performance() -> Dict[str, Any]:
    """
    Test Redis performance with various operations.
    
    Following project rules for performance monitoring and sub-2-second targets.
    
    Returns:
        Dict[str, Any]: Performance test results
    """
    performance_results = {
        "set_operations": {
            "count": 0,
            "total_time_ms": 0,
            "avg_time_ms": 0,
        },
        "get_operations": {
            "count": 0,
            "total_time_ms": 0,
            "avg_time_ms": 0,
        },
        "overall": {
            "total_time_ms": 0,
            "operations_per_second": 0,
            "meets_performance_target": False,
        }
    }
    
    test_operations = 100  # Number of operations to test
    overall_start_time = time.time()
    
    try:
        async with get_redis_client() as redis_client:
            # Test SET operations
            set_start_time = time.time()
            for i in range(test_operations):
                await redis_client.set(f"perf_test_key_{i}", f"perf_test_value_{i}", ex=60)
            set_end_time = time.time()
            
            set_total_time_ms = (set_end_time - set_start_time) * 1000
            performance_results["set_operations"]["count"] = test_operations
            performance_results["set_operations"]["total_time_ms"] = round(set_total_time_ms, 2)
            performance_results["set_operations"]["avg_time_ms"] = round(set_total_time_ms / test_operations, 2)
            
            # Test GET operations
            get_start_time = time.time()
            for i in range(test_operations):
                await redis_client.get(f"perf_test_key_{i}")
            get_end_time = time.time()
            
            get_total_time_ms = (get_end_time - get_start_time) * 1000
            performance_results["get_operations"]["count"] = test_operations
            performance_results["get_operations"]["total_time_ms"] = round(get_total_time_ms, 2)
            performance_results["get_operations"]["avg_time_ms"] = round(get_total_time_ms / test_operations, 2)
            
            # Cleanup test keys
            for i in range(test_operations):
                await redis_client.delete(f"perf_test_key_{i}")
            
            # Calculate overall performance
            overall_end_time = time.time()
            overall_total_time_ms = (overall_end_time - overall_start_time) * 1000
            total_operations = test_operations * 2  # SET + GET operations
            
            performance_results["overall"]["total_time_ms"] = round(overall_total_time_ms, 2)
            
            if overall_total_time_ms > 0:
                ops_per_second = (total_operations / overall_total_time_ms) * 1000
                performance_results["overall"]["operations_per_second"] = round(ops_per_second, 2)
            
            # Check if meets performance target (sub-2-second for all operations)
            performance_results["overall"]["meets_performance_target"] = overall_total_time_ms < 2000
            
            logger.info(f"Redis performance test completed: {total_operations} operations in {overall_total_time_ms:.2f}ms")
            
    except Exception as e:
        logger.error(f"Redis performance test failed: {e}")
        performance_results["error"] = str(e)
    
    return performance_results 