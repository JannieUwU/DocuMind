"""
Memory-enhanced RAG system integration
Automatically stores conversations to long-term memory
"""
from long_term_memory import LongTermMemory
from custom_rag import CustomRAGSystem
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class MemoryEnhancedRAG:
    """
    带长时记忆的RAG系统

    Features流程:
    1. 用户提问 → 检索相似历史对话
    2. 结合历史记忆 + 文档上下文 → LLM生成答案
    3. 自动向量化存储QA对 → 长时记忆库
    4. 跨会话知识积累
    """

    def __init__(self, rag_system: CustomRAGSystem, enable_memory: bool = True):
        self.rag = rag_system
        self.memory = LongTermMemory() if enable_memory else None
        self.enable_memory = enable_memory

    def answer_with_memory(
        self,
        user_id: int,
        conversation_id: int,
        query: str,
        llm_client,
        model: str = "gpt-4-turbo",
        use_memory: bool = True,
        save_to_memory: bool = True
    ) -> Dict:
        """
        带记忆检索的问答

        Args:
            user_id: 用户ID
            conversation_id: 对话ID
            query: 用户问题
            llm_client: LLM客户端
            model: 模型名称
            use_memory: 是否检索历史记忆
            save_to_memory: 是否保存到记忆

        Returns:
            {
                'answer': str,
                'relevant_memories': List[Dict],
                'memory_id': int (if saved)
            }
        """
        result = {
            'answer': '',
            'relevant_memories': [],
            'memory_id': None
        }

        # 1. 生成查询向量
        query_embedding = self.rag.embedder.embed_texts([query])[0]

        # 2. 检索相关历史记忆
        relevant_memories = []
        if use_memory and self.enable_memory:
            relevant_memories = self.memory.search_similar_memories(
                user_id=user_id,
                query_embedding=query_embedding,
                top_k=3,
                min_similarity=0.7,
                exclude_conversation_id=conversation_id
            )
            result['relevant_memories'] = relevant_memories

        # 3. 检索文档上下文
        doc_results = self.rag.search(
            query=query,
            top_k=5,
            conversation_id=conversation_id
        )
        doc_contexts = [text for text, score in doc_results]

        # 4. 构建增强上下文
        all_contexts = []

        # 添加历史记忆上下文
        if relevant_memories:
            memory_context = self._format_memory_context(relevant_memories)
            all_contexts.append(memory_context)

        # 添加文档上下文
        all_contexts.extend(doc_contexts)

        # 5. 生成答案
        answer = self.rag.generate_answer(
            query=query,
            llm_client=llm_client,
            contexts=all_contexts,
            model=model
        )
        result['answer'] = answer

        # 6. 保存到长时记忆
        if save_to_memory and self.enable_memory and answer:
            try:
                # 生成答案向量
                answer_embedding = self.rag.embedder.embed_texts([answer])[0]

                # 计算重要性
                importance = self.memory.calculate_importance(query, answer)

                # 保存记忆
                memory_id = self.memory.add_memory(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    question=query,
                    answer=answer,
                    question_embedding=query_embedding,
                    answer_embedding=answer_embedding,
                    importance_score=importance
                )
                result['memory_id'] = memory_id
                logger.info(f"Saved to long-term memory: {memory_id} (importance: {importance:.2f})")

            except Exception as e:
                logger.error(f"Failed to save memory: {e}")

        return result

    def _format_memory_context(self, memories: List[Dict]) -> str:
        """格式化历史记忆为上下文"""
        if not memories:
            return ""

        context = "### 相关历史对话\n\n"
        for idx, mem in enumerate(memories, 1):
            context += f"**历史问题 {idx}**: {mem['question']}\n"
            context += f"**历史回答**: {mem['answer'][:200]}...\n"  # 截断长答案
            context += f"相似度: {mem['similarity']:.2f}\n\n"

        return context

    def get_memory_summary(self, user_id: int, conversation_id: int) -> Dict:
        """获取当前对话的记忆摘要"""
        if not self.enable_memory:
            return {'enabled': False}

        stats = self.memory.get_memory_stats(user_id)
        recent = self.memory.get_recent_memories(
            user_id=user_id,
            limit=5,
            exclude_conversation_id=conversation_id
        )

        return {
            'enabled': True,
            'total_memories': stats['total_memories'],
            'average_importance': stats['average_importance'],
            'recent_topics': [m['question'][:50] + '...' for m in recent]
        }
