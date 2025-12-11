"""
Semantic Cache Module
智能语义缓存 - 基于向量相似度匹配缓存QA对

特点:
1. 不是精确匹配,而是语义相似匹配
2. 支持 Redis 后端 + 内存降级
3. 自动过期和LRU淘汰
4. 命中率统计
"""
import numpy as np
import json
import time
import logging
from typing import Optional, Dict, List, Tuple
from cache import cache, get_redis_client
import hashlib

logger = logging.getLogger(__name__)


class SemanticCache:
    """
    语义缓存 - 智能QA缓存系统

    工作流程:
    1. 用户提问 → 生成向量
    2. 与缓存中的问题向量比较相似度
    3. 相似度 > 阈值 → 缓存命中,直接返回答案
    4. 相似度 < 阈值 → 缓存未命中,调用LLM
    5. 缓存新的QA对

    优势:
    - "如何配置Redis?" 和 "怎么设置Redis?" 被视为相同问题
    - 大幅降低API调用成本
    - 极快的响应速度 (<10ms)
    """

    def __init__(
        self,
        similarity_threshold: float = 0.95,
        ttl: int = 3600,
        max_cache_size: int = 1000
    ):
        """
        Args:
            similarity_threshold: 相似度阈值 (0.9-0.98推荐)
            ttl: 缓存过期时间(seconds), default1小时
            max_cache_size: 最大缓存条目数
        """
        self.similarity_threshold = similarity_threshold
        self.ttl = ttl
        self.max_cache_size = max_cache_size
        self.redis = get_redis_client()

        # statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'total_queries': 0
        }

        # 内存缓存 (降级方案)
        self.memory_cache = []  # [(question_embedding, answer, metadata)]

    def get(
        self,
        question_embedding: List[float],
        question_text: str = ""
    ) -> Optional[Dict]:
        """
        查询缓存

        Args:
            question_embedding: 问题向量
            question_text: 问题文本 (用于日志)

        Returns:
            缓存命中: {
                'answer': str,
                'similarity': float,
                'cached_question': str,
                'hit': True
            }
            未命中: None
        """
        self.stats['total_queries'] += 1
        start_time = time.time()

        # 转换为numpy数组
        query_vec = np.array(question_embedding, dtype=np.float32)
        query_norm = np.linalg.norm(query_vec)

        # 尝试从缓存检索
        cache_entries = self._load_cache_entries()

        if not cache_entries:
            self.stats['misses'] += 1
            return None

        # 计算与所有缓存问题的相似度
        best_match = None
        best_similarity = 0.0

        for entry in cache_entries:
            cached_embedding = np.array(entry['embedding'], dtype=np.float32)
            cached_norm = np.linalg.norm(cached_embedding)

            # 余弦相似度
            similarity = np.dot(cached_embedding, query_vec) / (
                cached_norm * query_norm + 1e-8
            )

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = entry

        # 检查是否超过阈值
        if best_similarity >= self.similarity_threshold:
            self.stats['hits'] += 1
            elapsed = (time.time() - start_time) * 1000

            logger.info(
                f"Cache HIT: '{question_text[:50]}...' "
                f"(similarity: {best_similarity:.3f}, {elapsed:.2f}ms)"
            )

            return {
                'answer': best_match['answer'],
                'similarity': float(best_similarity),
                'cached_question': best_match['question'],
                'hit': True,
                'response_time_ms': elapsed
            }
        else:
            self.stats['misses'] += 1
            logger.debug(
                f"Cache MISS: '{question_text[:50]}...' "
                f"(best similarity: {best_similarity:.3f})"
            )
            return None

    def set(
        self,
        question_embedding: List[float],
        question_text: str,
        answer: str,
        metadata: Optional[Dict] = None
    ):
        """
        保存到缓存

        Args:
            question_embedding: 问题向量
            question_text: 问题文本
            answer: 答案文本
            metadata: 额外元数据
        """
        cache_entry = {
            'embedding': question_embedding,
            'question': question_text,
            'answer': answer,
            'metadata': metadata or {},
            'created_at': time.time()
        }

        # 使用Redis存储
        if self.redis:
            try:
                # 生成唯一键
                cache_key = self._generate_cache_key(question_text)

                # 序列化并存储
                self.redis.setex(
                    cache_key,
                    self.ttl,
                    json.dumps(cache_entry)
                )

                # 维护索引 (所有缓存键的列表)
                index_key = "semantic_cache:index"
                self.redis.sadd(index_key, cache_key)

                logger.info(f"Cached question: '{question_text[:50]}...'")

            except Exception as e:
                logger.error(f"Failed to cache to Redis: {e}")
                self._add_to_memory_cache(cache_entry)
        else:
            self._add_to_memory_cache(cache_entry)

    def _load_cache_entries(self) -> List[Dict]:
        """加载所有缓存条目"""
        if self.redis:
            try:
                # 从Redis加载
                index_key = "semantic_cache:index"
                cache_keys = self.redis.smembers(index_key)

                entries = []
                for key in cache_keys:
                    data = self.redis.get(key)
                    if data:
                        entry = json.loads(data)
                        entries.append(entry)
                    else:
                        # 键已过期,从索引移除
                        self.redis.srem(index_key, key)

                return entries

            except Exception as e:
                logger.error(f"Failed to load from Redis: {e}")
                return self.memory_cache
        else:
            return self.memory_cache

    def _add_to_memory_cache(self, entry: Dict):
        """添加到内存缓存 (降级方案)"""
        # LRU淘汰
        if len(self.memory_cache) >= self.max_cache_size:
            # 移除最旧的10%
            remove_count = max(1, self.max_cache_size // 10)
            self.memory_cache = self.memory_cache[remove_count:]

        self.memory_cache.append(entry)

    def _generate_cache_key(self, question: str) -> str:
        """生成缓存键"""
        hash_val = hashlib.md5(question.encode()).hexdigest()
        return f"semantic_cache:qa:{hash_val}"

    def get_stats(self) -> Dict:
        """获取缓存statistics"""
        total = self.stats['total_queries']
        hits = self.stats['hits']
        misses = self.stats['misses']

        hit_rate = (hits / total * 100) if total > 0 else 0

        return {
            'total_queries': total,
            'cache_hits': hits,
            'cache_misses': misses,
            'hit_rate': round(hit_rate, 2),
            'backend': 'redis' if self.redis else 'memory',
            'cache_size': self._get_cache_size(),
            'similarity_threshold': self.similarity_threshold
        }

    def _get_cache_size(self) -> int:
        """获取缓存大小"""
        if self.redis:
            try:
                index_key = "semantic_cache:index"
                return self.redis.scard(index_key) or 0
            except:
                return 0
        else:
            return len(self.memory_cache)

    def clear(self):
        """清空缓存"""
        if self.redis:
            try:
                index_key = "semantic_cache:index"
                cache_keys = self.redis.smembers(index_key)
                if cache_keys:
                    self.redis.delete(*cache_keys)
                self.redis.delete(index_key)
                logger.info("Cleared semantic cache from Redis")
            except Exception as e:
                logger.error(f"Failed to clear Redis cache: {e}")
        else:
            self.memory_cache.clear()
            logger.info("Cleared semantic cache from memory")

        # 重置统计
        self.stats = {
            'hits': 0,
            'misses': 0,
            'total_queries': 0
        }

    def adjust_threshold(self, new_threshold: float):
        """
        动态调整相似度阈值

        Args:
            new_threshold: 新阈值 (0.9-0.98推荐)

        建议:
        - 0.98: 严格匹配,几乎完全相同才命中
        - 0.95: 推荐值,语义相似即可
        - 0.90: 宽松匹配,可能产生不准确结果
        """
        old_threshold = self.similarity_threshold
        self.similarity_threshold = new_threshold
        logger.info(
            f"Adjusted similarity threshold: {old_threshold:.2f} → {new_threshold:.2f}"
        )


# ==================== 全局缓存实例 ====================

# 创建全局语义缓存 (推荐参数)
semantic_cache = SemanticCache(
    similarity_threshold=0.95,  # 95%相似度
    ttl=3600,                   # 1小时过期
    max_cache_size=1000         # 最多1000条
)
