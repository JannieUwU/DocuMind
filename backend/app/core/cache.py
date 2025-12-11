"""
Cache module with Redis and memory fallback
Provides unified caching layer for high-frequency database queries
"""
import json
import logging
from typing import Optional, Any
from functools import wraps
import time

logger = logging.getLogger(__name__)

# Redis 客户端 (单例)
_redis_client = None

def get_redis_client():
    """获取 Redis 客户端 (延迟加载)"""
    global _redis_client
    if _redis_client is None:
        try:
            import redis
            _redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            _redis_client.ping()  # 测试连接
            logger.info("Redis connected successfully")
        except ImportError:
            logger.warning("Redis package not installed. Using memory cache fallback.")
            _redis_client = None
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}. Using memory cache fallback.")
            _redis_client = None
    return _redis_client


class CacheManager:
    """统一缓存管理器 (支持 Redis + 内存降级)"""

    def __init__(self):
        self.redis = get_redis_client()
        self.memory_cache = {}  # 内存降级缓存
        self.memory_cache_ttl = {}  # TTL tracking for memory cache
        self.max_memory_items = 500

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            if self.redis:
                value = self.redis.get(key)
                if value:
                    return json.loads(value)
            else:
                # 检查内存缓存是否过期
                if key in self.memory_cache:
                    if key in self.memory_cache_ttl:
                        if time.time() < self.memory_cache_ttl[key]:
                            return self.memory_cache[key]
                        else:
                            # 过期，删除
                            del self.memory_cache[key]
                            del self.memory_cache_ttl[key]
                    else:
                        return self.memory_cache[key]
        except Exception as e:
            logger.warning(f"Cache get failed for key '{key}': {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 300):
        """设置缓存 (default 5 minutes TTL)"""
        try:
            if self.redis:
                self.redis.setex(key, ttl, json.dumps(value))
            else:
                # 内存缓存 LRU 淘汰
                if len(self.memory_cache) >= self.max_memory_items:
                    # 删除最早的 10% 条目
                    to_remove = list(self.memory_cache.keys())[:50]
                    for k in to_remove:
                        self.memory_cache.pop(k, None)
                        self.memory_cache_ttl.pop(k, None)

                self.memory_cache[key] = value
                self.memory_cache_ttl[key] = time.time() + ttl
        except Exception as e:
            logger.warning(f"Cache set failed for key '{key}': {e}")

    def delete(self, key: str):
        """删除缓存"""
        try:
            if self.redis:
                self.redis.delete(key)
            else:
                self.memory_cache.pop(key, None)
                self.memory_cache_ttl.pop(key, None)
        except Exception as e:
            logger.warning(f"Cache delete failed for key '{key}': {e}")

    def clear_pattern(self, pattern: str):
        """清除匹配模式的所有缓存

        Args:
            pattern: 匹配模式，如 "user:*" 或 "conversations:*"
        """
        try:
            if self.redis:
                keys = self.redis.keys(pattern)
                if keys:
                    self.redis.delete(*keys)
            else:
                # 内存缓存简单匹配
                pattern_str = pattern.replace('*', '')
                to_delete = [k for k in self.memory_cache if pattern_str in k]
                for k in to_delete:
                    self.memory_cache.pop(k, None)
                    self.memory_cache_ttl.pop(k, None)
        except Exception as e:
            logger.warning(f"Cache clear failed for pattern '{pattern}': {e}")

    def get_stats(self) -> dict:
        """获取缓存statistics"""
        stats = {
            "backend": "redis" if self.redis else "memory",
            "items_count": 0
        }

        try:
            if self.redis:
                info = self.redis.info()
                stats["items_count"] = info.get("db0", {}).get("keys", 0)
                stats["memory_usage"] = info.get("used_memory_human", "N/A")
            else:
                stats["items_count"] = len(self.memory_cache)
                stats["max_items"] = self.max_memory_items
        except Exception as e:
            logger.warning(f"Failed to get cache stats: {e}")

        return stats


# 全局缓存实例
cache = CacheManager()


# ====== 装饰器: 自动缓存函数结果 ======

def cached(ttl: int = 300, key_prefix: str = ""):
    """缓存装饰器

    usage examples:
        @cached(ttl=600, key_prefix="user")
        def get_user_by_username(username: str):
            # ... 数据库查询 ...

    Args:
        ttl: 缓存过期时间（seconds），default5minutes
        key_prefix: 缓存键前缀，default使用函数名
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key_parts = [key_prefix or func.__name__]
            cache_key_parts.extend(str(arg) for arg in args)
            cache_key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(cache_key_parts)

            # 尝试从缓存获取
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_result

            # 缓存未命中，执行函数
            logger.debug(f"Cache miss: {cache_key}")
            result = func(*args, **kwargs)

            # 存入缓存 (只缓存非 None 结果)
            if result is not None:
                cache.set(cache_key, result, ttl)

            return result

        # 添加清除缓存的辅助方法
        def clear_cache(*args, **kwargs):
            """清除特定参数的缓存"""
            cache_key_parts = [key_prefix or func.__name__]
            cache_key_parts.extend(str(arg) for arg in args)
            cache_key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(cache_key_parts)
            cache.delete(cache_key)

        wrapper.clear_cache = clear_cache
        return wrapper
    return decorator
