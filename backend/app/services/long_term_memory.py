"""
Long-term Memory Module
Stores and retrieves vectorized conversation history for cross-session knowledge retrieval
"""
import sqlite3
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class LongTermMemory:
    """
    长时记忆系统 - 向量化存储对话历史

    Features:
    1. 对话QA对向量化存储
    2. 基于语义相似度检索历史对话
    3. 支持跨会话知识积累
    """

    def __init__(self, db_path: str = "long_term_memory.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """initialized长时记忆数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 对话记忆表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                conversation_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                question_embedding BLOB NOT NULL,
                answer_embedding BLOB NOT NULL,
                importance_score REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memory_user_id
            ON conversation_memory(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memory_conversation_id
            ON conversation_memory(conversation_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memory_created_at
            ON conversation_memory(user_id, created_at DESC)
        """)

        conn.commit()
        conn.close()
        logger.info(f"Long-term memory database initialized at: {self.db_path}")

    def add_memory(
        self,
        user_id: int,
        conversation_id: int,
        question: str,
        answer: str,
        question_embedding: List[float],
        answer_embedding: List[float],
        importance_score: float = 1.0
    ) -> int:
        """
        添加对话记忆

        Args:
            user_id: 用户ID
            conversation_id: 对话ID
            question: 用户问题
            answer: 系统回答
            question_embedding: 问题向量
            answer_embedding: 答案向量
            importance_score: 重要性评分 (0-1)

        Returns:
            Memory ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 转换向量为二进制
            question_blob = np.array(question_embedding, dtype=np.float32).tobytes()
            answer_blob = np.array(answer_embedding, dtype=np.float32).tobytes()

            cursor.execute(
                """INSERT INTO conversation_memory
                   (user_id, conversation_id, question, answer,
                    question_embedding, answer_embedding, importance_score)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user_id, conversation_id, question, answer,
                 question_blob, answer_blob, importance_score)
            )

            conn.commit()
            memory_id = cursor.lastrowid
            logger.info(f"Added memory {memory_id} for user {user_id}")
            return memory_id

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to add memory: {e}")
            raise e
        finally:
            conn.close()

    def search_similar_memories(
        self,
        user_id: int,
        query_embedding: List[float],
        top_k: int = 5,
        min_similarity: float = 0.7,
        exclude_conversation_id: Optional[int] = None
    ) -> List[Dict]:
        """
        搜索语义相似的历史记忆

        Args:
            user_id: 用户ID
            query_embedding: 查询向量
            top_k: 返回数量
            min_similarity: 最小相似度阈值
            exclude_conversation_id: 排除的对话ID (避免检索当前对话)

        Returns:
            相似记忆列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 构建SQL查询
        if exclude_conversation_id:
            sql = """
                SELECT id, conversation_id, question, answer,
                       question_embedding, answer_embedding,
                       importance_score, created_at
                FROM conversation_memory
                WHERE user_id = ? AND conversation_id != ?
                ORDER BY created_at DESC
                LIMIT 500
            """
            cursor.execute(sql, (user_id, exclude_conversation_id))
        else:
            sql = """
                SELECT id, conversation_id, question, answer,
                       question_embedding, answer_embedding,
                       importance_score, created_at
                FROM conversation_memory
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 500
            """
            cursor.execute(sql, (user_id,))

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return []

        # 向量化相似度计算
        query_vec = np.array(query_embedding, dtype=np.float32)
        query_norm = np.linalg.norm(query_vec)

        results = []
        for row in rows:
            memory_id, conv_id, question, answer, q_blob, a_blob, importance, created_at = row

            # 解码向量
            q_embedding = np.frombuffer(q_blob, dtype=np.float32)

            # 计算余弦相似度
            similarity = np.dot(q_embedding, query_vec) / (
                np.linalg.norm(q_embedding) * query_norm + 1e-8
            )

            # 应用重要性权重
            weighted_similarity = similarity * importance

            if weighted_similarity >= min_similarity:
                results.append({
                    'memory_id': memory_id,
                    'conversation_id': conv_id,
                    'question': question,
                    'answer': answer,
                    'similarity': float(similarity),
                    'weighted_similarity': float(weighted_similarity),
                    'importance': importance,
                    'created_at': created_at
                })

        # 按加权相似度排序
        results.sort(key=lambda x: x['weighted_similarity'], reverse=True)

        return results[:top_k]

    def get_recent_memories(
        self,
        user_id: int,
        limit: int = 10,
        exclude_conversation_id: Optional[int] = None
    ) -> List[Dict]:
        """
        获取用户最近的记忆

        Args:
            user_id: 用户ID
            limit: 返回数量
            exclude_conversation_id: 排除的对话ID

        Returns:
            最近记忆列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if exclude_conversation_id:
            cursor.execute(
                """SELECT id, conversation_id, question, answer,
                          importance_score, created_at
                   FROM conversation_memory
                   WHERE user_id = ? AND conversation_id != ?
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (user_id, exclude_conversation_id, limit)
            )
        else:
            cursor.execute(
                """SELECT id, conversation_id, question, answer,
                          importance_score, created_at
                   FROM conversation_memory
                   WHERE user_id = ?
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (user_id, limit)
            )

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                'memory_id': row[0],
                'conversation_id': row[1],
                'question': row[2],
                'answer': row[3],
                'importance': row[4],
                'created_at': row[5]
            }
            for row in rows
        ]

    def calculate_importance(
        self,
        question: str,
        answer: str,
        user_feedback: Optional[str] = None
    ) -> float:
        """
        计算对话重要性评分

        启发式规则:
        1. 长回答通常更重要 (知识密集)
        2. 特定关键词表示重要话题
        3. 用户反馈影响重要性

        Args:
            question: 用户问题
            answer: 系统回答
            user_feedback: 用户反馈 (positive/negative)

        Returns:
            重要性评分 (0-1)
        """
        score = 0.5  # 基础分

        # 1. 回答长度 (更长 = 更详细)
        answer_length = len(answer)
        if answer_length > 500:
            score += 0.2
        elif answer_length > 200:
            score += 0.1

        # 2. 关键词检测 (重要主题)
        important_keywords = [
            '如何', 'how to', '步骤', 'step', '教程', 'tutorial',
            '错误', 'error', '问题', 'problem', '解决', 'solve',
            '为什么', 'why', '原因', 'reason', '原理', 'principle'
        ]

        question_lower = question.lower()
        if any(kw in question_lower for kw in important_keywords):
            score += 0.15

        # 3. 用户反馈
        if user_feedback == 'positive':
            score += 0.2
        elif user_feedback == 'negative':
            score -= 0.3

        # 限制在 [0.1, 1.0] 范围
        return max(0.1, min(1.0, score))

    def get_memory_stats(self, user_id: int) -> Dict:
        """获取用户记忆统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """SELECT COUNT(*), AVG(importance_score)
               FROM conversation_memory
               WHERE user_id = ?""",
            (user_id,)
        )
        count, avg_importance = cursor.fetchone()

        conn.close()

        return {
            'total_memories': count or 0,
            'average_importance': round(avg_importance or 0, 2)
        }
