"""
Cache-Accelerated RAG System
带缓存加速的RAG系统 - 结合语义缓存和长时记忆
"""
from custom_rag import CustomRAGSystem
from semantic_cache import semantic_cache, SemanticCache
from typing import Dict, Optional, List
import logging
import time

logger = logging.getLogger(__name__)


class CachedRAGSystem:
    """
    缓存加速的RAG系统

    三层架构:
    1. L1: 语义缓存 (最快, ~5ms)
    2. L2: 文档检索 + LLM (中速, ~500ms)
    3. L3: 自动缓存新答案

    优势:
    - 高频问题极速响应
    - 降低90%+ API成本
    - 自适应学习
    """

    def __init__(
        self,
        rag_system: CustomRAGSystem,
        enable_cache: bool = True,
        cache_instance: Optional[SemanticCache] = None
    ):
        """
        Args:
            rag_system: 基础RAG系统
            enable_cache: 是否启用缓存
            cache_instance: 自定义缓存实例 (可选)
        """
        self.rag = rag_system
        self.enable_cache = enable_cache
        self.cache = cache_instance or semantic_cache

    def answer(
        self,
        query: str,
        llm_client,
        conversation_id: Optional[int] = None,
        model: str = "gpt-4-turbo",
        use_cache: bool = True,
        save_to_cache: bool = True
    ) -> Dict:
        """
        智能问答 (带缓存加速)

        Args:
            query: 用户问题
            llm_client: LLM客户端
            conversation_id: 对话ID
            model: 模型名称
            use_cache: 是否尝试从缓存获取
            save_to_cache: 是否保存到缓存

        Returns:
            {
                'answer': str,
                'source': 'cache' | 'llm',
                'cache_hit': bool,
                'similarity': float (if from cache),
                'response_time_ms': float,
                'cached_question': str (if from cache)
            }
        """
        start_time = time.time()
        result = {
            'answer': '',
            'source': 'llm',
            'cache_hit': False,
            'response_time_ms': 0
        }

        # ===== 步骤1: 生成查询向量 =====
        query_embedding = self.rag.embedder.embed_texts([query])[0]

        # ===== 步骤2: 尝试从缓存获取 =====
        if use_cache and self.enable_cache:
            cached_result = self.cache.get(
                question_embedding=query_embedding,
                question_text=query
            )

            if cached_result:
                # 缓存命中!
                result.update({
                    'answer': cached_result['answer'],
                    'source': 'cache',
                    'cache_hit': True,
                    'similarity': cached_result['similarity'],
                    'cached_question': cached_result['cached_question'],
                    'response_time_ms': cached_result['response_time_ms']
                })

                logger.info(
                    f"Cache HIT: Saved ~500ms and API cost "
                    f"(similarity: {cached_result['similarity']:.3f})"
                )

                return result

        # ===== 步骤3: 缓存未命中,调用RAG + LLM =====
        logger.info("Cache MISS: Calling LLM...")

        # 检索文档上下文
        doc_results = self.rag.search(
            query=query,
            top_k=5,
            conversation_id=conversation_id
        )
        contexts = [text for text, score in doc_results]

        # 生成答案
        answer = self.rag.generate_answer_with_search(
            query=query,
            llm_client=llm_client,
            doc_contexts=contexts,
            model=model
        )

        result['answer'] = answer
        result['response_time_ms'] = (time.time() - start_time) * 1000

        # ===== 步骤4: 保存到缓存 =====
        if save_to_cache and self.enable_cache and answer:
            try:
                self.cache.set(
                    question_embedding=query_embedding,
                    question_text=query,
                    answer=answer,
                    metadata={
                        'conversation_id': conversation_id,
                        'model': model,
                        'context_count': len(contexts)
                    }
                )
                logger.info(f"Saved to cache: '{query[:50]}...'")

            except Exception as e:
                logger.error(f"Failed to save to cache: {e}")

        return result

    def get_cache_stats(self) -> Dict:
        """获取缓存statistics"""
        if not self.enable_cache:
            return {'enabled': False}

        stats = self.cache.get_stats()
        return {
            'enabled': True,
            **stats,
            'estimated_cost_savings': self._estimate_cost_savings(stats)
        }

    def _estimate_cost_savings(self, stats: Dict) -> Dict:
        """
        估算成本节省

        假设:
        - GPT-4 Turbo: $0.01 / 1K tokens
        - 平均每次调用: ~500 tokens
        - 每次调用成本: ~$0.005
        """
        hits = stats['cache_hits']
        cost_per_call = 0.005  # $0.005
        saved_usd = hits * cost_per_call

        return {
            'api_calls_saved': hits,
            'estimated_usd_saved': round(saved_usd, 2),
            'avg_time_saved_ms': 500  # 平均节省500ms
        }

    def clear_cache(self):
        """清空缓存"""
        if self.enable_cache:
            self.cache.clear()
            logger.info("Cache cleared")

    def adjust_cache_threshold(self, new_threshold: float):
        """
        调整缓存相似度阈值

        Args:
            new_threshold: 新阈值 (0.90-0.98)

        建议:
        - 命中率太低 → 降低阈值 (0.93)
        - 答案不准确 → 提高阈值 (0.97)
        """
        if self.enable_cache:
            self.cache.adjust_threshold(new_threshold)


# ==================== usage examples ====================

def example_usage():
    """
    usage examples:带缓存的RAG系统
    """
    from custom_rag import CustomEmbedder
    from openai import OpenAI

    # 1. initialized
    embedder = CustomEmbedder(
        api_key="your-api-key",
        model="text-embedding-3-large"
    )

    rag = CustomRAGSystem(embedder=embedder)
    cached_rag = CachedRAGSystem(rag, enable_cache=True)

    llm_client = OpenAI(api_key="your-api-key")

    # 2. 第一次查询 - 缓存未命中
    result1 = cached_rag.answer(
        query="What is machine learning?",
        llm_client=llm_client,
        conversation_id=1
    )

    print(f"Answer: {result1['answer']}")
    print(f"Source: {result1['source']}")  # 'llm'
    print(f"Time: {result1['response_time_ms']:.0f}ms")  # ~500ms

    # 3. 第二次查询 (语义相似) - 缓存命中!
    result2 = cached_rag.answer(
        query="Explain machine learning",  # 语义相似
        llm_client=llm_client,
        conversation_id=1
    )

    print(f"\nAnswer: {result2['answer']}")  # 相同答案
    print(f"Source: {result2['source']}")  # 'cache'
    print(f"Time: {result2['response_time_ms']:.0f}ms")  # ~5ms!
    print(f"Similarity: {result2['similarity']:.3f}")  # 0.97

    # 4. 查看缓存统计
    stats = cached_rag.get_cache_stats()
    print(f"\nCache Stats:")
    print(f"  Hit Rate: {stats['hit_rate']}%")
    print(f"  Saved: ${stats['estimated_cost_savings']['estimated_usd_saved']}")


if __name__ == "__main__":
    print("请查看usage examples了解如何集成缓存加速")
