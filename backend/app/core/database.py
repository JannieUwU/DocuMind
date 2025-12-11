"""
Database module for user management and chat history storage
"""
import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
import logging
import threading
import queue
from cache import cached, cache

logger = logging.getLogger(__name__)

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")

# ====== 连接池实现 ======

class SQLiteConnectionPool:
    """thread-safe的 SQLite 连接池"""

    def __init__(self, db_path: str, pool_size: int = 10):
        self.db_path = db_path
        self.pool_size = pool_size
        self.pool = queue.Queue(maxsize=pool_size)
        self._lock = threading.Lock()

        # 预创建连接
        for _ in range(pool_size):
            conn = sqlite3.connect(db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            # 优化 SQLite 性能
            conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
            conn.execute("PRAGMA synchronous=NORMAL")  # 降低同步级别
            conn.execute("PRAGMA cache_size=-64000")  # 64MB 缓存
            conn.execute("PRAGMA temp_store=MEMORY")  # 临时表使用内存
            self.pool.put(conn)

    def get_connection(self):
        """获取连接 (阻塞直到有可用连接)"""
        try:
            return self.pool.get(timeout=5.0)
        except queue.Empty:
            raise TimeoutError("数据库连接池耗尽，请稍后重试")

    def return_connection(self, conn):
        """归还连接"""
        if conn:
            try:
                conn.rollback()  # 清除未提交的事务
                self.pool.put(conn, block=False)
            except queue.Full:
                conn.close()

    def close_all(self):
        """关闭所有连接"""
        while not self.pool.empty():
            try:
                conn = self.pool.get(block=False)
                conn.close()
            except queue.Empty:
                break

# 创建全局连接池
_connection_pool = None
_pool_lock = threading.Lock()

def get_connection_pool():
    """获取全局连接池 (单例模式)"""
    global _connection_pool
    if _connection_pool is None:
        with _pool_lock:
            if _connection_pool is None:
                _connection_pool = SQLiteConnectionPool(DB_PATH, pool_size=10)
    return _connection_pool

# ====== 使用连接池的上下文管理器 ======

@contextmanager
def get_db_connection():
    """使用连接池的上下文管理器"""
    pool = get_connection_pool()
    conn = pool.get_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        pool.return_connection(conn)

def init_database():
    """Initialize database with required tables"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
        """)

        # User documents table - UPDATED to include conversation_id for session isolation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                conversation_id INTEGER,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
        """)

        # ====== 数据库迁移: 添加 conversation_id 列 (如果不存在) ======
        try:
            # 检查 user_documents 表是否有 conversation_id 列
            cursor.execute("PRAGMA table_info(user_documents)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'conversation_id' not in columns:
                logger.info("Migrating user_documents table: adding conversation_id column")
                cursor.execute("ALTER TABLE user_documents ADD COLUMN conversation_id INTEGER")
                conn.commit()
                logger.info("Migration completed successfully")
        except Exception as e:
            logger.warning(f"Migration check failed (may be expected): {e}")

        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_documents_user_id ON user_documents(user_id)")

        # ====== Additional Performance Indexes ======

        # 1. messages table - optimize time-sorted queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_created_at
            ON messages(conversation_id, created_at)
        """)

        # 2. conversations table - optimize recent conversation list queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_updated_at
            ON conversations(user_id, updated_at DESC)
        """)

        # 3. user_documents table - optimize conversation document queries (只有在列存在时才创建)
        cursor.execute("PRAGMA table_info(user_documents)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'conversation_id' in columns:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_documents_conversation
                ON user_documents(user_id, conversation_id)
            """)

        conn.commit()
        logger.info("Database initialized successfully")

# ============ User Management Functions ============

def create_user(username: str, email: str, hashed_password: str) -> Optional[int]:
    """Create a new user and return user ID"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, hashed_password) VALUES (?, ?, ?)",
                (username, email, hashed_password)
            )
            return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            raise ValueError("Username already exists")
        elif "email" in str(e):
            raise ValueError("Email already registered")
        raise

@cached(ttl=600, key_prefix="user:username")
def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username (with cache)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        return dict(row) if row else None

@cached(ttl=600, key_prefix="user:email")
def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email (with cache)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        return dict(row) if row else None

@cached(ttl=600, key_prefix="user:id")
def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID (with cache)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def update_user_password(email: str, hashed_password: str) -> bool:
    """Update user password by email"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET hashed_password = ?, updated_at = CURRENT_TIMESTAMP WHERE email = ?",
            (hashed_password, email)
        )
        return cursor.rowcount > 0

def user_exists(username: str) -> bool:
    """Check if user exists by username"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username = ? LIMIT 1", (username,))
        return cursor.fetchone() is not None

def email_exists(email: str) -> bool:
    """Check if email is already registered"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE email = ? LIMIT 1", (email,))
        return cursor.fetchone() is not None

# ============ Conversation Management Functions ============

def create_conversation(user_id: int, title: str) -> int:
    """Create a new conversation and return conversation ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (user_id, title) VALUES (?, ?)",
            (user_id, title)
        )
        conv_id = cursor.lastrowid

        # Clear user conversations cache
        cache.delete(f"conversations:{user_id}")

        return conv_id

@cached(ttl=300, key_prefix="conversations")
def get_user_conversations(user_id: int) -> List[Dict[str, Any]]:
    """Get all conversations for a user (with cache)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.*, COUNT(m.id) as message_count
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            WHERE c.user_id = ?
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            """,
            (user_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

@cached(ttl=300, key_prefix="conversation")
def get_conversation_by_id(conversation_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """Get conversation by ID (with user ownership check and cache)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM conversations WHERE id = ? AND user_id = ?",
            (conversation_id, user_id)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

def update_conversation_timestamp(conversation_id: int):
    """Update conversation's updated_at timestamp"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (conversation_id,)
        )

def delete_conversation(conversation_id: int, user_id: int) -> bool:
    """Delete conversation (with user ownership check)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM conversations WHERE id = ? AND user_id = ?",
            (conversation_id, user_id)
        )
        success = cursor.rowcount > 0

        if success:
            # Clear caches
            cache.delete(f"conversations:{user_id}")
            cache.delete(f"conversation:{conversation_id}:{user_id}")

        return success

def update_conversation_title(conversation_id: int, user_id: int, new_title: str) -> bool:
    """Update conversation title (with user ownership check)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE conversations SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
            (new_title, conversation_id, user_id)
        )
        success = cursor.rowcount > 0

        if success:
            # Clear caches
            cache.delete(f"conversations:{user_id}")
            cache.delete(f"conversation:{conversation_id}:{user_id}")

        return success

# ============ Message Management Functions ============

def add_message(conversation_id: int, role: str, content: str) -> int:
    """Add a message to a conversation"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
            (conversation_id, role, content)
        )
        # Update conversation timestamp
        cursor.execute(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (conversation_id,)
        )
        return cursor.lastrowid

def get_conversation_messages(conversation_id: int, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """Get messages for a conversation with pagination support

    Args:
        conversation_id: Conversation ID
        limit: Maximum number of messages to return (default: 100)
        offset: Number of messages to skip for pagination (default: 0)

    Returns:
        List of message dictionaries
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, conversation_id, role, content,
                   datetime(created_at, 'localtime') as timestamp
            FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
            LIMIT ? OFFSET ?
            """,
            (conversation_id, limit, offset)
        )
        return [dict(row) for row in cursor.fetchall()]

# ============ Document Management Functions ============

def add_user_document(user_id: int, filename: str, file_path: str, conversation_id: Optional[int] = None) -> int:
    """Add a document record for a user with optional conversation binding"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user_documents (user_id, filename, file_path, conversation_id) VALUES (?, ?, ?, ?)",
            (user_id, filename, file_path, conversation_id)
        )
        return cursor.lastrowid

def get_user_documents(user_id: int) -> List[Dict[str, Any]]:
    """Get all documents for a user"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM user_documents WHERE user_id = ? ORDER BY uploaded_at DESC",
            (user_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

def has_user_documents(user_id: int, conversation_id: Optional[int] = None) -> bool:
    """Check if user has uploaded any documents (optionally filtered by conversation)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if conversation_id is not None:
            cursor.execute(
                "SELECT 1 FROM user_documents WHERE user_id = ? AND conversation_id = ? LIMIT 1",
                (user_id, conversation_id)
            )
        else:
            cursor.execute(
                "SELECT 1 FROM user_documents WHERE user_id = ? LIMIT 1",
                (user_id,)
            )
        return cursor.fetchone() is not None

# Initialize database on module import
try:
    init_database()
    logger.info(f"Database initialized at: {DB_PATH}")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    raise
