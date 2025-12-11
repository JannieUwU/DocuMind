"""
Two-Level Indexing for Long Document Storage
两级索引优化 - 文档摘要 + 精确检索

架构:
Level 1 (文档级): 摘要向量 → 快速过滤相关文档
Level 2 (块级): 精确向量 → 精准检索答案

优势:
1. 检索速度提升 3-5倍
2. 大规模文档支持 (1000+文档)
3. 降低无关文档干扰
"""
import sqlite3
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging
import hashlib

logger = logging.getLogger(__name__)


class TwoLevelVectorDB:
    """
    两级索引向量数据库

    Level 1: document_summaries 表
      - 每个文档一个摘要向量
      - 快速筛选相关文档

    Level 2: chunks 表
      - 每个文档多个chunk向量
      - 精确检索答案
    """

    def __init__(self, db_path: str = "two_level_rag.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """initialized两级索引数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Level 1: 文档表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_hash TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Level 1: 文档摘要表 (新增)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                conversation_id INTEGER,
                summary_text TEXT NOT NULL,
                summary_embedding BLOB NOT NULL,
                chunk_count INTEGER DEFAULT 0,
                avg_chunk_length REAL DEFAULT 0,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        """)

        # Level 2: 文档块表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                conversation_id INTEGER,
                chunk_text TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                embedding BLOB NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_document_id
            ON chunks(document_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunks_conversation_id
            ON chunks(conversation_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_summaries_conversation_id
            ON document_summaries(conversation_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_summaries_doc_id
            ON document_summaries(document_id)
        """)

        conn.commit()
        conn.close()

        logger.info("Two-level vector database initialized")

    def add_document_with_summary(
        self,
        filename: str,
        chunks: List[str],
        embeddings: List[List[float]],
        summary_text: str,
        summary_embedding: List[float],
        conversation_id: Optional[int] = None
    ) -> int:
        """
        添加文档 (两级索引)

        Args:
            filename: 文件名
            chunks: 文本块列表
            embeddings: 块向量列表
            summary_text: 文档摘要
            summary_embedding: 摘要向量
            conversation_id: 对话ID

        Returns:
            document_id
        """
        file_hash = hashlib.md5(filename.encode()).hexdigest()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 1. 插入文档记录
            cursor.execute(
                "INSERT OR REPLACE INTO documents (filename, file_hash) VALUES (?, ?)",
                (filename, file_hash)
            )
            doc_id = cursor.lastrowid

            # 2. 插入文档摘要 (Level 1)
            summary_blob = np.array(summary_embedding, dtype=np.float32).tobytes()
            avg_chunk_len = np.mean([len(c) for c in chunks])

            cursor.execute(
                """INSERT INTO document_summaries
                   (document_id, conversation_id, summary_text, summary_embedding,
                    chunk_count, avg_chunk_length)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (doc_id, conversation_id, summary_text, summary_blob,
                 len(chunks), avg_chunk_len)
            )

            # 3. 批量插入文档块 (Level 2)
            chunk_data = [
                (doc_id, conversation_id, chunk, idx,
                 np.array(embedding, dtype=np.float32).tobytes())
                for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings))
            ]

            cursor.executemany(
                """INSERT INTO chunks
                   (document_id, conversation_id, chunk_text, chunk_index, embedding)
                   VALUES (?, ?, ?, ?, ?)""",
                chunk_data
            )

            conn.commit()
            logger.info(
                f"Added document '{filename}' with 2-level indexing: "
                f"1 summary + {len(chunks)} chunks"
            )
            return doc_id

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to add document: {e}")
            raise e
        finally:
            conn.close()

    def search_two_level(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        conversation_id: Optional[int] = None,
        doc_filter_threshold: float = 0.6,
        max_documents: int = 3
    ) -> List[Tuple[str, float, Dict]]:
        """
        两级检索

        流程:
        1. Level 1: 在文档摘要中检索,筛选出top-N相关文档
        2. Level 2: 在相关文档的chunks中精确检索

        Args:
            query_embedding: 查询向量
            top_k: 返回的chunk数量
            conversation_id: 对话ID
            doc_filter_threshold: 文档筛选阈值
            max_documents: 最多检索几个文档

        Returns:
            [(chunk_text, similarity, metadata)]
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # ===== Level 1: 文档级筛选 =====
        if conversation_id is not None:
            sql = """
                SELECT ds.document_id, ds.summary_text, ds.summary_embedding,
                       d.filename, ds.chunk_count
                FROM document_summaries ds
                JOIN documents d ON ds.document_id = d.id
                WHERE ds.conversation_id = ?
            """
            cursor.execute(sql, (conversation_id,))
        else:
            logger.warning("No conversation_id provided, searching all documents")
            sql = """
                SELECT ds.document_id, ds.summary_text, ds.summary_embedding,
                       d.filename, ds.chunk_count
                FROM document_summaries ds
                JOIN documents d ON ds.document_id = d.id
            """
            cursor.execute(sql)

        summaries = cursor.fetchall()

        if not summaries:
            conn.close()
            return []

        # 计算文档相似度
        query_vec = np.array(query_embedding, dtype=np.float32)
        query_norm = np.linalg.norm(query_vec)

        doc_scores = []
        for doc_id, summary_text, summary_blob, filename, chunk_count in summaries:
            summary_vec = np.frombuffer(summary_blob, dtype=np.float32)
            summary_norm = np.linalg.norm(summary_vec)

            similarity = np.dot(summary_vec, query_vec) / (
                summary_norm * query_norm + 1e-8
            )

            if similarity >= doc_filter_threshold:
                doc_scores.append({
                    'document_id': doc_id,
                    'filename': filename,
                    'similarity': float(similarity),
                    'chunk_count': chunk_count
                })

        # 排序并选择top-N文档
        doc_scores.sort(key=lambda x: x['similarity'], reverse=True)
        selected_docs = doc_scores[:max_documents]

        logger.info(
            f"Level 1: Filtered {len(summaries)} docs → {len(selected_docs)} relevant docs"
        )

        if not selected_docs:
            conn.close()
            return []

        # ===== Level 2: 精确chunk检索 =====
        selected_doc_ids = [d['document_id'] for d in selected_docs]

        # 构建SQL: 只检索相关文档的chunks
        placeholders = ','.join('?' * len(selected_doc_ids))
        sql = f"""
            SELECT chunk_text, embedding, document_id, chunk_index
            FROM chunks
            WHERE document_id IN ({placeholders})
        """

        if conversation_id is not None:
            sql += " AND conversation_id = ?"
            params = selected_doc_ids + [conversation_id]
        else:
            params = selected_doc_ids

        cursor.execute(sql, params)
        chunks = cursor.fetchall()
        conn.close()

        if not chunks:
            return []

        # 计算chunk相似度
        texts = []
        embeddings_list = []
        doc_ids = []
        chunk_indices = []

        for chunk_text, embedding_blob, doc_id, chunk_idx in chunks:
            texts.append(chunk_text)
            embeddings_list.append(np.frombuffer(embedding_blob, dtype=np.float32))
            doc_ids.append(doc_id)
            chunk_indices.append(chunk_idx)

        # 向量化计算
        embeddings_matrix = np.vstack(embeddings_list)
        norms = np.linalg.norm(embeddings_matrix, axis=1)
        similarities = np.dot(embeddings_matrix, query_vec) / (
            norms * query_norm + 1e-8
        )

        # 获取top-k
        if len(similarities) > top_k:
            top_indices = np.argpartition(similarities, -top_k)[-top_k:]
            top_indices = top_indices[np.argsort(similarities[top_indices])][::-1]
        else:
            top_indices = np.argsort(similarities)[::-1]

        # 构建结果
        results = []
        for i in top_indices:
            # 找到对应的文档信息
            doc_info = next(
                (d for d in selected_docs if d['document_id'] == doc_ids[i]),
                None
            )

            results.append((
                texts[i],
                float(similarities[i]),
                {
                    'document_id': doc_ids[i],
                    'filename': doc_info['filename'] if doc_info else 'Unknown',
                    'chunk_index': chunk_indices[i],
                    'doc_similarity': doc_info['similarity'] if doc_info else 0.0
                }
            ))

        logger.info(
            f"Level 2: Searched {len(chunks)} chunks from {len(selected_docs)} docs "
            f"→ {len(results)} results"
        )

        return results

    def get_document_summary(self, document_id: int) -> Optional[Dict]:
        """获取文档摘要"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """SELECT ds.summary_text, ds.chunk_count, ds.avg_chunk_length,
                      d.filename, d.created_at
               FROM document_summaries ds
               JOIN documents d ON ds.document_id = d.id
               WHERE ds.document_id = ?""",
            (document_id,)
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'summary': row[0],
                'chunk_count': row[1],
                'avg_chunk_length': row[2],
                'filename': row[3],
                'created_at': row[4]
            }

        return None

    def get_stats(self) -> Dict:
        """获取数据库统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM documents")
        total_docs = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM chunks")
        total_chunks = cursor.fetchone()[0]

        cursor.execute("SELECT AVG(chunk_count) FROM document_summaries")
        avg_chunks_per_doc = cursor.fetchone()[0] or 0

        conn.close()

        return {
            'total_documents': total_docs,
            'total_chunks': total_chunks,
            'avg_chunks_per_document': round(avg_chunks_per_doc, 1)
        }


# ==================== 摘要生成工具 ====================

class SummaryGenerator:
    """
    文档摘要生成器

    方法:
    1. 提取式: 选择最重要的句子
    2. 抽象式: 使用LLM生成摘要
    """

    @staticmethod
    def extractive_summary(
        chunks: List[str],
        max_length: int = 500
    ) -> str:
        """
        提取式摘要 (快速,无需LLM)

        策略:
        - 取每个chunk的第一句
        - 合并直到达到max_length
        """
        sentences = []
        current_length = 0

        for chunk in chunks:
            # 提取第一句
            first_sent = chunk.split('.')[0] + '.'
            sent_len = len(first_sent)

            if current_length + sent_len <= max_length:
                sentences.append(first_sent)
                current_length += sent_len
            else:
                break

        summary = ' '.join(sentences)
        return summary if summary else chunks[0][:max_length]

    @staticmethod
    def abstractive_summary(
        chunks: List[str],
        llm_client,
        model: str = "gpt-3.5-turbo"
    ) -> str:
        """
        抽象式摘要 (高质量,需要LLM)

        使用LLM生成文档摘要
        """
        # 合并chunks (限制长度避免超token)
        full_text = '\n\n'.join(chunks[:5])  # 只用前5个chunks
        if len(full_text) > 4000:
            full_text = full_text[:4000]

        prompt = f"""请用2-3句话总结以下文档的主要内容:

{full_text}

摘要:"""

        try:
            response = llm_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一个专业的文档摘要助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=150
            )

            summary = response.choices[0].message.content.strip()
            logger.info(f"Generated abstractive summary: {len(summary)} chars")
            return summary

        except Exception as e:
            logger.error(f"LLM summary failed: {e}, falling back to extractive")
            return SummaryGenerator.extractive_summary(chunks)
