"""
Database Configuration and Migration Support

Supports both SQLite (development) and PostgreSQL (production)
with seamless migration path.

Environment Variables:
- DATABASE_TYPE: 'sqlite' or 'postgresql' (default: sqlite)
- DATABASE_URL: PostgreSQL connection string
- SQLITE_PATH: Path to SQLite database file
"""

import os
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager
from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import QueuePool, NullPool

logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()

# ====== Database Configuration ======

class DatabaseConfig:
    """Database configuration based on environment"""

    def __init__(self):
        self.db_type = os.getenv('DATABASE_TYPE', 'sqlite').lower()
        self.database_url = self._get_database_url()
        self.engine_kwargs = self._get_engine_kwargs()

    def _get_database_url(self) -> str:
        """Get database URL based on type"""
        if self.db_type == 'postgresql':
            # PostgreSQL for production
            url = os.getenv(
                'DATABASE_URL',
                'postgresql://user:password@localhost:5432/ragchat'
            )
            logger.info(f"Using PostgreSQL database")
            return url

        elif self.db_type == 'sqlite':
            # SQLite for development
            db_path = os.getenv(
                'SQLITE_PATH',
                os.path.join(os.path.dirname(__file__), 'users.db')
            )
            logger.info(f"Using SQLite database at: {db_path}")
            return f'sqlite:///{db_path}'

        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

    def _get_engine_kwargs(self) -> Dict[str, Any]:
        """Get engine configuration based on database type"""
        if self.db_type == 'postgresql':
            return {
                'poolclass': QueuePool,
                'pool_size': int(os.getenv('DB_POOL_SIZE', '10')),
                'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '20')),
                'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', '30')),
                'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', '3600')),
                'pool_pre_ping': True,  # Verify connections before using
                'echo': os.getenv('DB_ECHO', 'false').lower() == 'true',
                'connect_args': {
                    'connect_timeout': 10,
                    'options': '-c statement_timeout=30000'  # 30s query timeout
                }
            }

        elif self.db_type == 'sqlite':
            return {
                'poolclass': NullPool,  # SQLite doesn't need connection pooling
                'echo': os.getenv('DB_ECHO', 'false').lower() == 'true',
                'connect_args': {
                    'check_same_thread': False,
                    'timeout': 30
                }
            }

        return {}

    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL"""
        return self.db_type == 'postgresql'

    def is_sqlite(self) -> bool:
        """Check if using SQLite"""
        return self.db_type == 'sqlite'


# ====== Database Engine ======

class DatabaseEngine:
    """Database engine with support for multiple backends"""

    _instance = None
    _engine = None
    _SessionLocal = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._engine is None:
            self._config = DatabaseConfig()
            self._initialize_engine()

    def _initialize_engine(self):
        """Initialize database engine"""
        try:
            # Create engine
            self._engine = create_engine(
                self._config.database_url,
                **self._config.engine_kwargs
            )

            # Add SQLite-specific optimizations
            if self._config.is_sqlite():
                self._configure_sqlite()

            # Add PostgreSQL-specific optimizations
            if self._config.is_postgresql():
                self._configure_postgresql()

            # Create session factory
            self._SessionLocal = sessionmaker(
                bind=self._engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )

            logger.info(f"✓ Database engine initialized ({self._config.db_type})")

        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise

    def _configure_sqlite(self):
        """Configure SQLite-specific optimizations"""

        @event.listens_for(self._engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            # Enable Write-Ahead Logging for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            # Reduce fsync calls (faster but slightly less durable)
            cursor.execute("PRAGMA synchronous=NORMAL")
            # Increase cache size to 64MB
            cursor.execute("PRAGMA cache_size=-64000")
            # Use memory for temporary tables
            cursor.execute("PRAGMA temp_store=MEMORY")
            # Foreign key support
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        logger.info("✓ SQLite optimizations applied")

    def _configure_postgresql(self):
        """Configure PostgreSQL-specific optimizations"""

        @event.listens_for(self._engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            # Set connection-level settings
            with dbapi_conn.cursor() as cursor:
                # Set timezone
                cursor.execute("SET TIME ZONE 'UTC'")
                # Set statement timeout (30 seconds)
                cursor.execute("SET statement_timeout = '30s'")
                # Set idle in transaction timeout (5 minutes)
                cursor.execute("SET idle_in_transaction_session_timeout = '5min'")

        logger.info("✓ PostgreSQL optimizations applied")

    @property
    def engine(self):
        """Get SQLAlchemy engine"""
        return self._engine

    @property
    def SessionLocal(self):
        """Get session factory"""
        return self._SessionLocal

    @property
    def config(self):
        """Get database configuration"""
        return self._config

    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(bind=self._engine)
        logger.info("✓ Database tables created")

    def drop_tables(self):
        """Drop all tables (use with caution!)"""
        Base.metadata.drop_all(bind=self._engine)
        logger.warning("⚠ Database tables dropped")


# ====== Database Session Management ======

# Initialize global engine
db_engine = DatabaseEngine()


@contextmanager
def get_db_session() -> Session:
    """
    Get database session with automatic transaction management

    Usage:
        with get_db_session() as session:
            user = session.query(User).filter_by(id=1).first()
            session.commit()
    """
    session = db_engine.SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def get_db():
    """
    Dependency for FastAPI endpoints

    Usage:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = db_engine.SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ====== Database Health Check ======

def check_database_health() -> Dict[str, Any]:
    """
    Check database connectivity and health

    Returns:
        Dict with health status and metrics
    """
    try:
        with get_db_session() as session:
            # Execute simple query
            if db_engine.config.is_postgresql():
                result = session.execute("SELECT 1").scalar()
            else:
                result = session.execute("SELECT 1").scalar()

            # Get connection pool stats (PostgreSQL only)
            pool_stats = {}
            if db_engine.config.is_postgresql():
                pool = db_engine.engine.pool
                pool_stats = {
                    'pool_size': pool.size(),
                    'checked_out': pool.checkedout(),
                    'overflow': pool.overflow(),
                    'checked_in': pool.size() - pool.checkedout()
                }

            return {
                'status': 'healthy',
                'database_type': db_engine.config.db_type,
                'connection_test': result == 1,
                'pool_stats': pool_stats
            }

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            'status': 'unhealthy',
            'database_type': db_engine.config.db_type,
            'error': str(e)
        }


# ====== Database Monitoring ======

def get_database_metrics() -> Dict[str, Any]:
    """
    Get database performance metrics

    Returns:
        Dict with various database metrics
    """
    metrics = {
        'database_type': db_engine.config.db_type,
        'timestamp': datetime.now().isoformat()
    }

    try:
        with get_db_session() as session:
            if db_engine.config.is_postgresql():
                # PostgreSQL-specific metrics

                # Active connections
                result = session.execute("""
                    SELECT count(*)
                    FROM pg_stat_activity
                    WHERE state = 'active'
                """).scalar()
                metrics['active_connections'] = result

                # Database size
                result = session.execute("""
                    SELECT pg_size_pretty(pg_database_size(current_database()))
                """).scalar()
                metrics['database_size'] = result

                # Table sizes (top 5)
                results = session.execute("""
                    SELECT
                        schemaname || '.' || tablename AS table,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
                    FROM pg_tables
                    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                    LIMIT 5
                """).fetchall()
                metrics['top_tables'] = [
                    {'table': r[0], 'size': r[1]} for r in results
                ]

            elif db_engine.config.is_sqlite():
                # SQLite-specific metrics

                # Database size
                import os
                db_path = db_engine.config.database_url.replace('sqlite:///', '')
                if os.path.exists(db_path):
                    size_bytes = os.path.getsize(db_path)
                    metrics['database_size'] = f"{size_bytes / 1024 / 1024:.2f} MB"

                # Table count
                result = session.execute("""
                    SELECT COUNT(*)
                    FROM sqlite_master
                    WHERE type='table'
                """).scalar()
                metrics['table_count'] = result

        return metrics

    except Exception as e:
        logger.error(f"Failed to get database metrics: {e}")
        return {**metrics, 'error': str(e)}


# ====== Utility Functions ======

def init_database():
    """Initialize database (create tables)"""
    db_engine.create_tables()


def reset_database():
    """Reset database (drop and recreate tables)"""
    db_engine.drop_tables()
    db_engine.create_tables()


# Export commonly used items
__all__ = [
    'Base',
    'db_engine',
    'get_db_session',
    'get_db',
    'init_database',
    'reset_database',
    'check_database_health',
    'get_database_metrics',
    'DatabaseConfig',
    'DatabaseEngine'
]
