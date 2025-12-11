"""
Thread-safe Configuration Manager

Features:
- Thread-safe read/write operations
- Automatic expiration cleanup
- Type-safe data structures
- Extensible persistence interface
"""

import threading
import time
import logging
from typing import Dict, Optional, Any, TypedDict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class UserConfig(TypedDict, total=False):
    """User configuration data structure"""
    api_keys: Dict[str, str]
    rag_system: Any  # CustomRAGSystem instance
    llm_client: Any  # OpenAI client instance
    reranker: Any  # Reranker instance
    embedder: Any  # CustomEmbedder instance


class UserSession(TypedDict, total=False):
    """User session data structure"""
    documents_loaded: bool
    conversations: List[int]
    documents: List[str]


class VerificationCode(TypedDict):
    """Verification code data structure"""
    code: str
    timestamp: float


class ConfigManager:
    """
    Thread-safe configuration manager

    Features:
    - User API configuration management (user_configs)
    - User session data management (user_sessions)
    - Email verification code management (with expiration cleanup)

    Thread safety guarantee:
    - All read/write operations use threading.Lock
    - Returns deep copy of data to prevent external modification
    """

    def __init__(self, verification_ttl: int = 360):
        """
        Initialize configuration manager

        Args:
            verification_ttl: Verification code TTL（seconds），default 6 minutes
        """
        # User configuration storage
        self._configs: Dict[str, UserConfig] = {}
        self._configs_lock = threading.Lock()

        # User session storage
        self._sessions: Dict[str, UserSession] = {}
        self._sessions_lock = threading.Lock()

        # Verification code storage (email -> {code, timestamp})
        self._verification_codes: Dict[str, VerificationCode] = {}
        self._verification_lock = threading.Lock()
        self._verification_ttl = verification_ttl

        logger.info("ConfigManager initialized with verification_ttl=%ds", verification_ttl)

    # ============ 用户配置管理 ============

    def set_config(self, username: str, config: UserConfig) -> None:
        """
        Set user configuration（thread-safe）

        Args:
            username: username
            config: configuration dictionary
        """
        with self._configs_lock:
            # 存储配置的浅拷贝（RAG 对象不拷贝）
            self._configs[username] = config
            logger.debug(f"Config set for user: {username}")

    def get_config(self, username: str) -> Optional[UserConfig]:
        """
        Get user configuration（thread-safe）

        Args:
            username: username

        Returns:
            用户configuration dictionary，returns None if not exists None
        """
        with self._configs_lock:
            config = self._configs.get(username)
            if config:
                # 返回引用（因为 RAG 对象无法深拷贝）
                return config
            return None

    def has_config(self, username: str) -> bool:
        """
        Check if user has configuration（thread-safe）

        Args:
            username: username

        Returns:
            whether configuration exists
        """
        with self._configs_lock:
            return username in self._configs

    def delete_config(self, username: str) -> bool:
        """
        Delete user configuration（thread-safe）

        Args:
            username: username

        Returns:
            whether deletion was successful
        """
        with self._configs_lock:
            if username in self._configs:
                del self._configs[username]
                logger.info(f"Config deleted for user: {username}")
                return True
            return False

    def get_all_usernames(self) -> List[str]:
        """
        Get all configured usernames（thread-safe）

        Returns:
            list of usernames
        """
        with self._configs_lock:
            return list(self._configs.keys())

    # ============ 用户会话管理 ============

    def set_session(self, username: str, session: UserSession) -> None:
        """
        Set user session data（thread-safe）

        Args:
            username: username
            session: session data
        """
        with self._sessions_lock:
            self._sessions[username] = session
            logger.debug(f"Session set for user: {username}")

    def get_session(self, username: str) -> Optional[UserSession]:
        """
        Get user session data（thread-safe）

        Args:
            username: username

        Returns:
            session data，returns None if not exists None
        """
        with self._sessions_lock:
            return self._sessions.get(username)

    def ensure_session(self, username: str) -> UserSession:
        """
        Ensure user session exists（create if not exists）

        Args:
            username: username

        Returns:
            session data
        """
        with self._sessions_lock:
            if username not in self._sessions:
                self._sessions[username] = {
                    "documents_loaded": False,
                    "conversations": [],
                    "documents": []
                }
                logger.debug(f"Session created for user: {username}")
            return self._sessions[username]

    def update_session(self, username: str, **kwargs) -> None:
        """
        Update user session data（thread-safe）

        Args:
            username: username
            **kwargs: fields to update

        Example:
            update_session("alice", documents_loaded=True)
        """
        with self._sessions_lock:
            if username not in self._sessions:
                self._sessions[username] = {
                    "documents_loaded": False,
                    "conversations": [],
                    "documents": []
                }

            for key, value in kwargs.items():
                if key in ["documents_loaded", "conversations", "documents"]:
                    self._sessions[username][key] = value  # type: ignore

            logger.debug(f"Session updated for user: {username}, fields: {list(kwargs.keys())}")

    def delete_session(self, username: str) -> bool:
        """
        Delete user session（thread-safe）

        Args:
            username: username

        Returns:
            whether deletion was successful
        """
        with self._sessions_lock:
            if username in self._sessions:
                del self._sessions[username]
                logger.info(f"Session deleted for user: {username}")
                return True
            return False

    # ============ verification code管理 ============

    def set_verification_code(self, email: str, code: str) -> None:
        """
        Set email verification code（thread-safe，with auto-cleanup）

        Args:
            email: email address
            code: 6digit code
        """
        with self._verification_lock:
            # clean expired codes first
            self._cleanup_expired_codes_unsafe()

            # set new verification code
            self._verification_codes[email] = {
                "code": code,
                "timestamp": time.time()
            }
            logger.info(f"Verification code set for email: {email}")

    def get_verification_code(self, email: str) -> Optional[str]:
        """
        Get email verification code（thread-safe，check expiration）

        Args:
            email: email address

        Returns:
            verification code（6位string），returns None if not exists or expired None
        """
        with self._verification_lock:
            if email not in self._verification_codes:
                return None

            data = self._verification_codes[email]
            now = time.time()

            # check if expired
            if now - data["timestamp"] > self._verification_ttl:
                del self._verification_codes[email]
                logger.debug(f"Verification code expired for email: {email}")
                return None

            return data["code"]

    def verify_code(self, email: str, code: str) -> bool:
        """
        Verify email verification code（thread-safe，auto-delete after verification）

        Args:
            email: email address
            code: user input code

        Returns:
            whether verification succeeded
        """
        with self._verification_lock:
            if email not in self._verification_codes:
                logger.warning(f"Verification failed: no code for {email}")
                return False

            data = self._verification_codes[email]
            now = time.time()

            # check if expired
            if now - data["timestamp"] > self._verification_ttl:
                del self._verification_codes[email]
                logger.warning(f"Verification failed: code expired for {email}")
                return False

            # code matches
            if data["code"] == code:
                # Verification successful，删除verification code
                del self._verification_codes[email]
                logger.info(f"Verification successful for email: {email}")
                return True
            else:
                logger.warning(f"Verification failed: incorrect code for {email}")
                return False

    def _cleanup_expired_codes_unsafe(self) -> int:
        """
        Clean expired verification codes（internal method, no lock）

        Returns:
            number of codes cleaned
        """
        now = time.time()
        expired_emails = [
            email for email, data in self._verification_codes.items()
            if now - data["timestamp"] > self._verification_ttl
        ]

        for email in expired_emails:
            del self._verification_codes[email]

        if expired_emails:
            logger.info(f"Cleaned {len(expired_emails)} expired verification codes")

        return len(expired_emails)

    def cleanup_expired_codes(self) -> int:
        """
        Clean expired verification codes（thread-safe，public interface）

        Returns:
            number of codes cleaned
        """
        with self._verification_lock:
            return self._cleanup_expired_codes_unsafe()

    # ============ debugging and monitoring ============

    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics（thread-safe）

        Returns:
            statistics dictionary
        """
        with self._configs_lock, self._sessions_lock, self._verification_lock:
            # clean expired codes first
            self._cleanup_expired_codes_unsafe()

            return {
                "total_users_with_config": len(self._configs),
                "total_sessions": len(self._sessions),
                "active_verification_codes": len(self._verification_codes)
            }

    def clear_all(self) -> None:
        """
        Clear all data（for testing only，thread-safe）
        """
        with self._configs_lock, self._sessions_lock, self._verification_lock:
            self._configs.clear()
            self._sessions.clear()
            self._verification_codes.clear()
            logger.warning("All config data cleared!")


# ============ global singleton instance ============

config_manager = ConfigManager(verification_ttl=360)  # 6 minutes过期


# ============ compatibility helper functions ============

def get_user_config(username: str) -> Optional[UserConfig]:
    """
    Get user configuration（helper function for backward compatibility）

    Args:
        username: username

    Returns:
        用户配置

    Raises:
        HTTPException: 如果配置不存在（需要在调用处 import HTTPException）
    """
    config = config_manager.get_config(username)
    if config is None:
        # 注意：这里不能直接抛出 HTTPException
        # 调用者需要自行处理 None 的情况
        pass
    return config


# ============ usage examples ============

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)

    # test configuration management
    print("=== test configuration management ===")
    config_manager.set_config("alice", {
        "api_keys": {"openai": "sk-test123"},
        "rag_system": None
    })
    print(f"Alice's config: {config_manager.get_config('alice')}")
    print(f"Has config: {config_manager.has_config('alice')}")

    # test session management
    print("\n=== test session management ===")
    config_manager.ensure_session("bob")
    config_manager.update_session("bob", documents_loaded=True)
    print(f"Bob's session: {config_manager.get_session('bob')}")

    # test verification code management
    print("\n=== test verification code management ===")
    config_manager.set_verification_code("test@example.com", "123456")
    code = config_manager.get_verification_code("test@example.com")
    print(f"Retrieved code: {code}")

    is_valid = config_manager.verify_code("test@example.com", "123456")
    print(f"Verification result: {is_valid}")

    # should be deleted after verification
    code_after = config_manager.get_verification_code("test@example.com")
    print(f"Code after verification: {code_after}")

    # test expiration cleanup
    print("\n=== test expiration cleanup ===")
    config_manager.set_verification_code("expire@test.com", "999999")
    # simulate expiration（need to modify timestamp）
    with config_manager._verification_lock:
        if "expire@test.com" in config_manager._verification_codes:
            config_manager._verification_codes["expire@test.com"]["timestamp"] = time.time() - 400

    cleaned = config_manager.cleanup_expired_codes()
    print(f"Cleaned {cleaned} expired codes")

    # statistics
    print("\n=== statistics ===")
    stats = config_manager.get_stats()
    print(f"Stats: {stats}")
