"""
Custom RAG implementation with:
- OpenAI text-embedding-3-large for embeddings
- gpt-4-turbo for LLM
- BAAI/bge-reranker-v2-m3 for reranking
- SQLite vector database
- DuckDuckGo web search
"""
import os
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import requests
import json
import numpy as np
from openai import OpenAI
import sqlite3
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import functools

logger = logging.getLogger(__name__)


# Simple LRU cache for embeddings
class EmbeddingCache:
    """Simple LRU cache for embedding results."""

    def __init__(self, max_size: int = 200):
        self.cache = {}
        self.max_size = max_size
        self.access_order = []

    def get(self, key: str) -> Optional[List[float]]:
        """Get cached embedding."""
        if key in self.cache:
            # Update access order
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None

    def put(self, key: str, value: List[float]):
        """Put embedding in cache."""
        if key in self.cache:
            self.access_order.remove(key)
        elif len(self.cache) >= self.max_size:
            # Remove least recently used
            oldest = self.access_order.pop(0)
            del self.cache[oldest]

        self.cache[key] = value
        self.access_order.append(key)


class WebSearchTool:
    """Web search tool using DuckDuckGo."""

    @staticmethod
    def search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Search the web for information."""
        try:
            from duckduckgo_search import DDGS

            logger.info(f"Searching web for: {query}")
            results = []

            with DDGS() as ddgs:
                search_results = list(ddgs.text(query, max_results=max_results))

                for result in search_results:
                    results.append({
                        'title': result.get('title', ''),
                        'snippet': result.get('body', ''),
                        'url': result.get('href', '')
                    })

            logger.info(f"Found {len(results)} search results")
            return results
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return []

    @staticmethod
    def format_search_results(results: List[Dict[str, str]]) -> str:
        """Format search results for LLM context."""
        if not results:
            return "No search results found."

        formatted = "Web Search Results:\n\n"
        for i, result in enumerate(results, 1):
            formatted += f"{i}. {result['title']}\n"
            formatted += f"   {result['snippet']}\n"
            formatted += f"   Source: {result['url']}\n\n"

        return formatted


class CustomEmbedder:
    """Custom embedder that works with any OpenAI-compatible API."""

    def __init__(self, api_key: str, base_url: str = None, model: str = "text-embedding-3-large"):
        self.api_key = api_key
        self.base_url = base_url or "https://api.openai.com/v1"
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.cache = EmbeddingCache(max_size=200)  # Cache for speed

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts with caching."""
        results = []
        texts_to_embed = []
        indices_to_embed = []

        # Check cache first
        for i, text in enumerate(texts):
            cache_key = hashlib.md5(text.encode()).hexdigest()
            cached = self.cache.get(cache_key)
            if cached is not None:
                results.append((i, cached))
            else:
                texts_to_embed.append(text)
                indices_to_embed.append(i)

        # Embed uncached texts
        if texts_to_embed:
            try:
                # Try using OpenAI client first
                response = self.client.embeddings.create(
                    input=texts_to_embed,
                    model=self.model
                )
                embeddings = [item.embedding for item in response.data]

                # Cache results
                for text, embedding in zip(texts_to_embed, embeddings):
                    cache_key = hashlib.md5(text.encode()).hexdigest()
                    self.cache.put(cache_key, embedding)

                # Add to results with correct indices
                for idx, embedding in zip(indices_to_embed, embeddings):
                    results.append((idx, embedding))

            except Exception as e:
                logger.warning(f"OpenAI client failed, trying direct HTTP: {e}")
                # Fallback to direct HTTP request
                embeddings = self._embed_via_http(texts_to_embed)

                # Cache results
                for text, embedding in zip(texts_to_embed, embeddings):
                    cache_key = hashlib.md5(text.encode()).hexdigest()
                    self.cache.put(cache_key, embedding)

                # Add to results with correct indices
                for idx, embedding in zip(indices_to_embed, embeddings):
                    results.append((idx, embedding))

        # Sort by original index and return embeddings only
        results.sort(key=lambda x: x[0])
        return [emb for _, emb in results]

    def _embed_via_http(self, texts: List[str]) -> List[List[float]]:
        """Direct HTTP request for non-standard APIs."""
        # Handle different base_url formats
        base = self.base_url.rstrip('/')
        # If base_url doesn't end with /v1, add it
        if not base.endswith('/v1'):
            base = f"{base}/v1"

        url = f"{base}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": texts,
            "model": self.model
        }

        logger.info(f"Sending embedding request to: {url}")
        response = requests.post(url, headers=headers, json=payload, timeout=60)

        # Log response details for debugging
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        logger.info(f"Response text (first 500 chars): {response.text[:500]}")

        response.raise_for_status()

        # Try to parse JSON
        try:
            result = response.json()
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Full response text: {response.text}")
            raise ValueError(f"API returned non-JSON response. Status: {response.status_code}, Content: {response.text[:200]}")

        # Handle different response formats
        if isinstance(result, dict) and "data" in result:
            return [item["embedding"] for item in result["data"]]
        elif isinstance(result, list):
            return result
        elif isinstance(result, dict) and "embeddings" in result:
            return result["embeddings"]
        else:
            logger.error(f"Unexpected response format: {result}")
            raise ValueError(f"Unsupported embedding response format: {type(result)}")


class CustomPDFProcessor:
    """Custom PDF processor using pypdf."""

    @staticmethod
    def extract_text_from_pdf(pdf_path: Path) -> str:
        """Extract text from PDF using pypdf."""
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(pdf_path))
            text_parts = []

            for page_num, page in enumerate(reader.pages):
                try:
                    text = page.extract_text()
                    if text.strip():
                        text_parts.append(f"--- Page {page_num + 1} ---\n{text}")
                except Exception as e:
                    logger.warning(f"Failed to extract page {page_num + 1}: {e}")
                    continue

            if not text_parts:
                raise ValueError("No text could be extracted from PDF")

            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            raise


class CustomChunker:
    """Custom text chunker."""

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks."""
        if not text:
            return []

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + chunk_size

            # Try to break at sentence boundary
            if end < text_length:
                # Look for sentence endings
                search_start = max(start, end - 100)
                period_pos = text.rfind('. ', search_start, end)
                newline_pos = text.rfind('\n', search_start, end)

                break_pos = max(period_pos, newline_pos)
                if break_pos > start:
                    end = break_pos + 1

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - overlap

        return chunks


class CustomVectorDB:
    """Simple vector database using SQLite."""

    def __init__(self, db_path: str = "custom_rag.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_hash TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

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

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_document_id ON chunks(document_id)
        """)

        # ====== Additional Performance Indexes ======

        # 1. conversation_id index (CRITICAL for session isolation!)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunks_conversation_id
            ON chunks(conversation_id)
        """)

        # 2. Composite index - optimize conversation document queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunks_doc_conv
            ON chunks(document_id, conversation_id)
        """)

        conn.commit()
        conn.close()

    def add_document(self, filename: str, chunks: List[str], embeddings: List[List[float]], conversation_id: int = None) -> int:
        """Add document with chunks and embeddings using optimized bulk insert.

        Args:
            filename: Document filename
            chunks: List of text chunks
            embeddings: List of embedding vectors
            conversation_id: Optional conversation ID for session isolation

        Returns:
            Document ID
        """
        # Calculate file hash to avoid duplicates
        file_hash = hashlib.md5(filename.encode()).hexdigest()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Insert document
            cursor.execute(
                "INSERT OR REPLACE INTO documents (filename, file_hash) VALUES (?, ?)",
                (filename, file_hash)
            )
            doc_id = cursor.lastrowid

            # ====== 优化: 批量插入 (比逐条插入快 10-20 倍) ======
            # 预处理所有数据
            chunk_data = [
                (doc_id, conversation_id, chunk, idx,
                 np.array(embedding, dtype=np.float32).tobytes())
                for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings))
            ]

            # 使用 executemany 批量插入
            cursor.executemany(
                """INSERT INTO chunks
                   (document_id, conversation_id, chunk_text, chunk_index, embedding)
                   VALUES (?, ?, ?, ?, ?)""",
                chunk_data
            )

            conn.commit()
            logger.info(f"Bulk inserted document '{filename}' with {len(chunks)} chunks to conversation {conversation_id}")
            return doc_id
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to add document: {e}")
            raise e
        finally:
            conn.close()

    def search(self, query_embedding: List[float], top_k: int = 5, conversation_id: int = None) -> List[Tuple[str, float]]:
        """优化的向量搜索 - 使用 NumPy 批量计算 + argpartition

        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            conversation_id: Optional conversation ID to filter chunks by session
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # ====== 优化 1: 使用索引过滤 + 动态限制 ======
        if conversation_id is not None:
            # 严格会话隔离 + 索引优化
            # 动态限制：根据 top_k 调整加载数量，避免加载过多数据
            limit = min(500, max(top_k * 50, 100))  # 最少100条，最多500条
            sql = """
                SELECT chunk_text, embedding
                FROM chunks
                WHERE conversation_id = ? AND conversation_id IS NOT NULL
                LIMIT ?
            """
            logger.info(f"STRICT ISOLATION: Searching conversation_id={conversation_id}, loading up to {limit} chunks")
            cursor.execute(sql, (conversation_id, limit))
        else:
            # SECURITY: If no conversation_id provided, return EMPTY results
            logger.warning("SECURITY: Search without conversation_id - returning empty")
            return []

        # ====== 优化 2: 批量加载 + 向量化计算 ======
        query_vec = np.array(query_embedding, dtype=np.float32)
        query_norm = np.linalg.norm(query_vec)

        # 批量加载所有行 (避免逐行处理)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return []

        # ====== 优化 3: NumPy 向量化计算 (取代 Python 循环) ======
        texts = []
        embeddings_list = []

        for chunk_text, embedding_blob in rows:
            texts.append(chunk_text)
            embeddings_list.append(np.frombuffer(embedding_blob, dtype=np.float32))

        # 一次性计算所有相似度
        embeddings_matrix = np.vstack(embeddings_list)  # Shape: (N, D)
        norms = np.linalg.norm(embeddings_matrix, axis=1)  # Shape: (N,)

        # 向量化余弦相似度计算 (添加小值防止除零)
        similarities = np.dot(embeddings_matrix, query_vec) / (norms * query_norm + 1e-8)

        # ====== 优化 4: 使用 argpartition 替代完全排序 ======
        # argpartition 比 argsort 快 3-5 倍 (O(n) vs O(n log n))
        if len(similarities) > top_k:
            # 只部分排序 top_k 个元素
            top_indices = np.argpartition(similarities, -top_k)[-top_k:]
            # 对 top_k 进行精确排序
            top_indices = top_indices[np.argsort(similarities[top_indices])][::-1]
        else:
            # 数据量小于 top_k，直接排序
            top_indices = np.argsort(similarities)[::-1]

        # 返回结果
        results = [(texts[i], float(similarities[i])) for i in top_indices]

        logger.info(f"Vector search completed: {len(rows)} chunks scanned → top {len(results)} results")
        return results

    def get_all_chunks(self) -> List[str]:
        """Get all chunks from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT chunk_text FROM chunks ORDER BY document_id, chunk_index")
        chunks = [row[0] for row in cursor.fetchall()]
        conn.close()
        return chunks


class CustomRAGSystem:
    """Complete custom RAG system with web search capability."""

    def __init__(self, embedder: CustomEmbedder, db_path: str = "custom_rag.db", enable_web_search: bool = True):
        self.embedder = embedder
        self.db = CustomVectorDB(db_path)
        self.pdf_processor = CustomPDFProcessor()
        self.chunker = CustomChunker()
        self.web_search = WebSearchTool()
        self.enable_web_search = enable_web_search

    def add_pdf(self, pdf_path: Path, conversation_id: int = None) -> bool:
        """Process and add a PDF document, optionally bound to a conversation.

        Args:
            pdf_path: Path to PDF file
            conversation_id: Optional conversation ID for session isolation
        """
        try:
            logger.info(f"Processing PDF: {pdf_path} for conversation {conversation_id}")

            # Extract text
            text = self.pdf_processor.extract_text_from_pdf(pdf_path)
            logger.info(f"Extracted {len(text)} characters")

            # Chunk text
            chunks = self.chunker.chunk_text(text, chunk_size=1000, overlap=200)
            logger.info(f"Created {len(chunks)} chunks")

            if not chunks:
                raise ValueError("No chunks created from PDF")

            # Embed chunks in batches
            embeddings = []
            batch_size = 100
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                batch_embeddings = self.embedder.embed_texts(batch)
                embeddings.extend(batch_embeddings)
                logger.info(f"Embedded batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}")

            # Store in database with conversation_id
            self.db.add_document(pdf_path.name, chunks, embeddings, conversation_id)

            return True
        except Exception as e:
            logger.error(f"Failed to process PDF: {e}", exc_info=True)
            return False

    def search(self, query: str, top_k: int = 5, conversation_id: int = None) -> List[Tuple[str, float]]:
        """Search for relevant chunks, optionally filtered by conversation.

        Args:
            query: Search query
            top_k: Number of results
            conversation_id: Optional conversation ID for session-scoped search
        """
        query_embedding = self.embedder.embed_texts([query])[0]
        return self.db.search(query_embedding, top_k=top_k, conversation_id=conversation_id)

    def generate_answer_with_search(self, query: str, llm_client: OpenAI, doc_contexts: List[str], model: str = "gpt-4-turbo") -> str:
        """Generate answer using LLM with document contexts and optional web search."""
        # Check if we should use web search
        needs_web_search = self._should_use_web_search(query, doc_contexts, llm_client, model)

        all_contexts = doc_contexts.copy()

        if needs_web_search and self.enable_web_search:
            logger.info(f"Using web search for query: {query}")
            search_results = self.web_search.search(query, max_results=3)
            if search_results:
                web_context = self.web_search.format_search_results(search_results)
                all_contexts.insert(0, web_context)

        return self.generate_answer(query, llm_client, all_contexts, model)

    def _should_use_web_search(self, query: str, contexts: List[str], llm_client: OpenAI, model: str) -> bool:
        """Determine if web search is needed based on query type."""
        # Keywords that indicate need for current/real-time information
        real_time_keywords = [
            '今天', '今日', '现在', '当前', '最新', '天气', '新闻',
            'today', 'now', 'current', 'latest', 'weather', 'news',
            '实时', 'real-time', '昨天', 'yesterday', '明天', 'tomorrow'
        ]

        query_lower = query.lower()

        # Check if query contains real-time keywords
        for keyword in real_time_keywords:
            if keyword in query_lower:
                logger.info(f"Detected real-time keyword '{keyword}' in query")
                return True

        # If no documents are available, use web search
        if not contexts or all(not ctx.strip() for ctx in contexts):
            logger.info("No document contexts available, using web search")
            return True

        return False

    def generate_answer(self, query: str, llm_client: OpenAI, contexts: List[str], model: str = "gpt-4-turbo") -> str:
        """Generate answer using LLM with retrieved contexts."""
        # CRITICAL: Merge all contexts into ONE seamless text block
        # Remove any separators that might tempt LLM to enumerate them
        context_text = " ".join(contexts) if contexts else ""

        system_prompt = """You are a professional AI assistant. Follow these rules strictly:

CRITICAL - FORBIDDEN PHRASES (NEVER use these):
- "根据上下文" / "根据Context" / "根据文档"
- "根据你提供的" / "根据你的"
- "让我来" / "我来帮你" / "让我为你"
- "这个问题" / "这是什么" / "这个是"
- "Context 1" / "Context 2" / "Context 3" / "Context 4" / "Context 5" (or any Context N)
- "结合Context" / "参考Context" / "查看Context"
- ANY meta-commentary about sources, contexts, or the answering process

REQUIRED BEHAVIOR:
1. Read the provided contexts silently - NEVER mention them in your response
2. Synthesize information naturally as if it's your own knowledge
3. Start with a direct answer - no preamble, no source references
4. Write like a confident human expert, not an AI processing contexts
5. Use declarative statements, provide specific details and examples

RESPONSE STRUCTURE:
- Opening (1-2 sentences): Direct core answer to the question
- Body: Supporting details, examples, step-by-step guidance
- Format: Use Markdown (###, **, lists, code blocks, ---)
- NO source attribution, NO context numbering, NO meta-references

BAD EXAMPLES (NEVER do this):
"根据Context 5的内容，这个问题..."
"结合提供的上下文，我来为你解答..."
"参考Context 1和Context 3..."

GOOD EXAMPLE:
Question: "什么是机器学习？"
Answer: "机器学习是人工智能的核心分支。它让计算机通过数据自主学习模式，而非依赖明确编程。

### 核心方法
- **监督学习**：使用标注数据训练模型
- **无监督学习**：发现数据中的隐藏模式
- **强化学习**：通过试错优化决策"

Write as an expert colleague - professional, direct, informative. NEVER reveal that you're reading from contexts."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Reference Information:\n\n{context_text}\n\n---\n\nUser Question: {query}"}
        ]

        try:
            response = llm_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024
            )

            # Handle standard OpenAI response
            if hasattr(response, 'choices') and hasattr(response.choices[0], 'message'):
                return response.choices[0].message.content
            # Handle string response (non-standard API) - check if it's HTML
            elif isinstance(response, str):
                if response.strip().startswith('<!DOCTYPE') or response.strip().startswith('<html'):
                    logger.warning(f"OpenAI client returned HTML, trying direct HTTP")
                    return self._generate_via_http(llm_client, messages, model)
                return response
            # Handle dict response
            elif isinstance(response, dict):
                if 'choices' in response:
                    return response['choices'][0]['message']['content']
                elif 'content' in response:
                    return response['content']
                else:
                    return str(response)
            else:
                # Unknown response type, try HTTP fallback
                logger.warning(f"Unknown response type from OpenAI client: {type(response)}, trying direct HTTP")
                return self._generate_via_http(llm_client, messages, model)
        except Exception as e:
            logger.warning(f"OpenAI client failed for LLM, trying direct HTTP: {e}")
            # Fallback to direct HTTP request
            return self._generate_via_http(llm_client, messages, model)

    def _generate_via_http(self, llm_client: OpenAI, messages: List[dict], model: str) -> str:
        """Direct HTTP request for LLM when OpenAI client fails."""
        try:
            base = llm_client.base_url
            if isinstance(base, str):
                base_str = base.rstrip('/')
            else:
                base_str = str(base).rstrip('/')

            if not base_str.endswith('/v1'):
                base_str = f"{base_str}/v1"

            url = f"{base_str}/chat/completions"
            headers = {
                "Authorization": f"Bearer {llm_client.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1024
            }

            logger.info(f"Sending LLM request to: {url}")
            logger.info(f"LLM request payload: {json.dumps(payload, ensure_ascii=False)[:500]}")
            response = requests.post(url, headers=headers, json=payload, timeout=120)

            # Log response details
            logger.info(f"LLM Response status: {response.status_code}")
            logger.info(f"LLM Response headers: {dict(response.headers)}")
            logger.info(f"LLM Response text (first 500 chars): {response.text[:500]}")

            response.raise_for_status()

            # Check if response is HTML
            if response.text.strip().startswith('<!DOCTYPE') or response.text.strip().startswith('<html'):
                logger.error(f"LLM API returned HTML instead of JSON. URL: {url}")
                return "Error: The LLM API returned a web page instead of a response. Please check your API configuration."

            result = response.json()

            # Parse response
            if 'choices' in result:
                return result['choices'][0]['message']['content']
            elif 'content' in result:
                return result['content']
            else:
                logger.error(f"Unexpected LLM response format: {result}")
                return f"Error: Unexpected response format"
        except Exception as e:
            logger.error(f"LLM HTTP request failed: {e}", exc_info=True)
            return f"Error generating response: {str(e)}"
