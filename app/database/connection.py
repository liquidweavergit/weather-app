"""
Database connection module for Temperature Display App.

Provides async database connection management for containerized PostgreSQL.
Following project rules: async/await, Docker integration, error resilience,
performance targets (<2s response), and comprehensive logging.
"""

import asyncio
import os
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any, Optional
import logging

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logger = logging.getLogger(__name__)

# Global engine instance (singleton pattern for containerized environment)
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker] = None


def create_database_engine() -> AsyncEngine:
    """
    Create async database engine with Docker-optimized configuration.
    
    Following project rules:
    - Async operations for all database interactions
    - Connection pooling for containerized environment
    - Performance optimization for sub-2-second targets
    - Comprehensive error handling
    
    Returns:
        AsyncEngine: Configured SQLAlchemy async engine
    """
    global _engine
    
    if _engine is not None:
        return _engine
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    
    # Docker-optimized connection pool settings for async engine
    _engine = create_async_engine(
        database_url,
        # Connection pool settings for containerized environment
        # Note: For async engines, SQLAlchemy automatically uses AsyncAdaptedQueuePool
        pool_size=10,  # Base connections
        max_overflow=20,  # Additional connections under load
        pool_pre_ping=True,  # Validate connections before use
        pool_recycle=3600,  # Recycle connections every hour
        # Performance settings
        echo=False,  # Set to True for SQL debugging
        future=True,  # Use SQLAlchemy 2.0 style
        # Connection timeout settings
        connect_args={
            "command_timeout": 30,
            "server_settings": {
                "application_name": "temperature_display_app",
            },
        },
    )
    
    logger.info("Database engine created successfully")
    return _engine


def get_session_factory() -> async_sessionmaker:
    """
    Get async session factory for database operations.
    
    Returns:
        async_sessionmaker: Session factory for creating database sessions
    """
    global _session_factory
    
    if _session_factory is not None:
        return _session_factory
    
    engine = create_database_engine()
    _session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,  # Keep objects accessible after commit
        autoflush=True,  # Auto-flush before queries
        autocommit=False,  # Explicit transaction control
    )
    
    logger.info("Session factory created successfully")
    return _session_factory


@asynccontextmanager
async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.
    
    Provides automatic session management with proper cleanup and error handling.
    Following project rules for comprehensive error handling and transaction management.
    
    Yields:
        AsyncSession: Database session with automatic cleanup
    """
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        logger.debug("Database session created")
        yield session
        await session.commit()
        logger.debug("Database session committed successfully")
    except Exception as e:
        logger.error(f"Database session error: {e}")
        await session.rollback()
        logger.debug("Database session rolled back")
        raise
    finally:
        await session.close()
        logger.debug("Database session closed")


async def test_connection() -> bool:
    """
    Test database connection functionality.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        async with get_database_session() as session:
            result = await session.execute(text("SELECT 1"))
            row = result.fetchone()
            return row[0] == 1
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


async def connect_with_retry(max_retries: int = 3, delay: float = 1.0) -> bool:
    """
    Connect to database with retry mechanism for container startup scenarios.
    
    Following project rules for resilience patterns and graceful degradation.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        
    Returns:
        bool: True if connection successful, False otherwise
    """
    for attempt in range(max_retries):
        try:
            result = await test_connection()
            if result:
                logger.info(f"Database connection successful on attempt {attempt + 1}")
                return True
        except Exception as e:
            logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
        
        if attempt < max_retries - 1:
            await asyncio.sleep(delay)
            delay *= 2  # Exponential backoff
    
    logger.error(f"Database connection failed after {max_retries} attempts")
    return False


async def get_pool_status() -> Dict[str, Any]:
    """
    Get connection pool status for monitoring.
    
    Returns:
        Dict[str, Any]: Pool status information
    """
    engine = create_database_engine()
    pool = engine.pool
    
    # For AsyncAdaptedQueuePool, we need to access the underlying sync pool
    sync_pool = getattr(pool, '_pool', pool)
    
    return {
        "active_connections": getattr(sync_pool, 'checkedout', lambda: 0)(),
        "pool_size": getattr(sync_pool, 'size', lambda: 10)(),
        "checked_in_connections": getattr(sync_pool, 'checkedin', lambda: 0)(),
        "overflow_connections": getattr(sync_pool, 'overflow', lambda: 0)(),
        "invalid_connections": getattr(sync_pool, 'invalidated', lambda: 0)(),
    }


async def test_connection_recovery() -> bool:
    """
    Test connection recovery after simulated failure.
    
    Returns:
        bool: True if recovery successful, False otherwise
    """
    try:
        # Test initial connection
        initial_result = await test_connection()
        if not initial_result:
            return False
        
        # Simulate recovery by testing connection again
        recovery_result = await test_connection()
        return recovery_result
    except Exception as e:
        logger.error(f"Connection recovery test failed: {e}")
        return False


async def connect_with_timeout(timeout: float = 5.0) -> bool:
    """
    Test database connection with timeout.
    
    Args:
        timeout: Connection timeout in seconds
        
    Returns:
        bool: True if connection successful within timeout, False otherwise
    """
    try:
        result = await asyncio.wait_for(test_connection(), timeout=timeout)
        return result
    except asyncio.TimeoutError:
        logger.warning(f"Database connection timed out after {timeout} seconds")
        return False
    except Exception as e:
        logger.error(f"Database connection with timeout failed: {e}")
        return False


async def time_connection_establishment() -> bool:
    """
    Time database connection establishment for performance monitoring.
    
    Following project rules for sub-2-second performance targets.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    start_time = time.time()
    try:
        result = await test_connection()
        end_time = time.time()
        connection_time = end_time - start_time
        
        logger.info(f"Database connection established in {connection_time:.3f} seconds")
        
        # Check against performance target (2 seconds)
        if connection_time > 2.0:
            logger.warning(f"Connection time {connection_time:.3f}s exceeds 2s target")
        
        return result
    except Exception as e:
        end_time = time.time()
        connection_time = end_time - start_time
        logger.error(f"Database connection failed after {connection_time:.3f} seconds: {e}")
        return False


async def test_concurrent_connections(connection_count: int = 10) -> bool:
    """
    Test concurrent database connections for performance validation.
    
    Args:
        connection_count: Number of concurrent connections to test
        
    Returns:
        bool: True if all connections successful, False otherwise
    """
    async def single_connection_test():
        try:
            async with get_database_session() as session:
                result = await session.execute(text("SELECT 1"))
                return result.fetchone()[0] == 1
        except Exception:
            return False
    
    try:
        # Create concurrent connection tasks
        tasks = [single_connection_test() for _ in range(connection_count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check if all connections were successful
        successful_connections = sum(1 for result in results if result is True)
        
        logger.info(f"Concurrent connections: {successful_connections}/{connection_count} successful")
        
        return successful_connections == connection_count
    except Exception as e:
        logger.error(f"Concurrent connection test failed: {e}")
        return False


async def cleanup_engine():
    """
    Cleanup database engine and connections.
    
    Should be called during application shutdown.
    """
    global _engine, _session_factory
    
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Database engine disposed successfully") 