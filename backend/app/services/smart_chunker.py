"""
Smart Text Chunker - 智能语义分块器
支持多种分块策略,自动选择最优方案

策略:
1. 固定长度分块 (传统方法)
2. 句子边界分块 (保持语义完整)
3. 段落边界分块 (保持主题连贯)
4. 语义分块 (基于相似度)
5. 混合分块 (综合多种策略)
"""
import re
from typing import List, Tuple, Optional
import logging
import numpy as np

logger = logging.getLogger(__name__)


class SmartChunker:
    """
    智能文本分块器

    特点:
    1. 多策略支持 (固定/句子/段落/语义)
    2. 自动选择最优策略
    3. 保持语义完整性
    4. 智能重叠处理
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        overlap: int = 200,
        min_chunk_size: int = 100,
        max_chunk_size: int = 2000
    ):
        """
        Args:
            chunk_size: 目标分块大小
            overlap: 重叠字符数
            min_chunk_size: 最小分块大小
            max_chunk_size: 最大分块大小
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

        # 句子结束标记 (中英文)
        self.sentence_endings = r'[。.!?！？]\s*'

        # 段落分隔符
        self.paragraph_separators = r'\n\s*\n+'

    def chunk_text(
        self,
        text: str,
        strategy: str = 'auto'
    ) -> List[str]:
        """
        智能分块

        Args:
            text: 输入文本
            strategy: 分块策略
                - 'auto': 自动选择
                - 'fixed': 固定长度
                - 'sentence': 句子边界
                - 'paragraph': 段落边界
                - 'hybrid': 混合策略

        Returns:
            分块列表
        """
        if not text or not text.strip():
            return []

        # 清理文本
        text = self._clean_text(text)

        # 选择策略
        if strategy == 'auto':
            strategy = self._select_strategy(text)
            logger.info(f"Auto-selected chunking strategy: {strategy}")

        # 执行分块
        if strategy == 'sentence':
            chunks = self._chunk_by_sentences(text)
        elif strategy == 'paragraph':
            chunks = self._chunk_by_paragraphs(text)
        elif strategy == 'hybrid':
            chunks = self._chunk_hybrid(text)
        else:  # 'fixed'
            chunks = self._chunk_fixed_length(text)

        # 后处理
        chunks = self._post_process_chunks(chunks)

        logger.info(
            f"Chunked text: {len(text)} chars → {len(chunks)} chunks "
            f"(avg: {len(text)//len(chunks) if chunks else 0} chars/chunk)"
        )

        return chunks

    def _select_strategy(self, text: str) -> str:
        """
        自动选择分块策略

        规则:
        1. 短文本 (<500字) → 不分块
        2. 有明显段落结构 → 段落分块
        3. 句子较长 → 句子分块
        4. 其他 → 混合分块
        """
        text_len = len(text)

        # 短文本不分块
        if text_len < 500:
            return 'fixed'

        # 检测段落结构
        paragraphs = re.split(self.paragraph_separators, text)
        avg_para_len = np.mean([len(p) for p in paragraphs if p.strip()])

        if len(paragraphs) > 3 and 300 < avg_para_len < 1500:
            return 'paragraph'

        # 检测句子长度
        sentences = re.split(self.sentence_endings, text)
        avg_sent_len = np.mean([len(s) for s in sentences if s.strip()])

        if avg_sent_len < 200:
            return 'sentence'

        # default混合策略
        return 'hybrid'

    def _chunk_fixed_length(self, text: str) -> List[str]:
        """
        固定长度分块 (改进版)

        改进点:
        1. 尝试在句子边界分割
        2. 避免分割单词
        3. 保持标点符号完整
        """
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + self.chunk_size, text_length)

            # 寻找最佳分割点
            if end < text_length:
                # 1. 尝试句子边界
                best_break = self._find_sentence_boundary(text, start, end)

                # 2. 尝试段落边界
                if best_break == end:
                    best_break = self._find_paragraph_boundary(text, start, end)

                # 3. 尝试空格
                if best_break == end:
                    best_break = self._find_word_boundary(text, start, end)

                end = best_break

            chunk = text[start:end].strip()
            if chunk and len(chunk) >= self.min_chunk_size:
                chunks.append(chunk)

            # 重叠处理
            start = max(start + 1, end - self.overlap)

        return chunks

    def _chunk_by_sentences(self, text: str) -> List[str]:
        """
        按句子分块

        优点:
        - 保持语义完整
        - 不会截断句子

        策略:
        - 累积句子直到达到目标大小
        - 超过最大大小时强制分割
        """
        # 分割句子
        sentences = re.split(self.sentence_endings, text)
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sent_len = len(sentence)

            # 单句过长,强制分割
            if sent_len > self.max_chunk_size:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_size = 0

                # 分割长句
                sub_chunks = self._split_long_sentence(sentence)
                chunks.extend(sub_chunks)
                continue

            # 累积句子
            if current_size + sent_len <= self.chunk_size:
                current_chunk.append(sentence)
                current_size += sent_len
            else:
                # 达到目标大小,保存当前chunk
                if current_chunk:
                    chunks.append(' '.join(current_chunk))

                # 开始新chunk (带重叠)
                overlap_sentences = self._get_overlap_sentences(
                    current_chunk,
                    self.overlap
                )
                current_chunk = overlap_sentences + [sentence]
                current_size = sum(len(s) for s in current_chunk)

        # 保存最后一个chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def _chunk_by_paragraphs(self, text: str) -> List[str]:
        """
        按段落分块

        优点:
        - 保持主题连贯
        - 适合结构化文档

        策略:
        - 尽量不分割段落
        - 段落过大时在句子边界分割
        """
        # 分割段落
        paragraphs = re.split(self.paragraph_separators, text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        chunks = []
        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para_len = len(para)

            # 段落过大,按句子分割
            if para_len > self.max_chunk_size:
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_size = 0

                # 分割大段落
                para_chunks = self._chunk_by_sentences(para)
                chunks.extend(para_chunks)
                continue

            # 累积段落
            if current_size + para_len <= self.chunk_size:
                current_chunk.append(para)
                current_size += para_len
            else:
                # 保存当前chunk
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))

                current_chunk = [para]
                current_size = para_len

        # 保存最后一个chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks

    def _chunk_hybrid(self, text: str) -> List[str]:
        """
        混合策略分块

        结合:
        1. 段落边界 (优先)
        2. 句子边界 (次优)
        3. 固定长度 (保底)
        """
        # 先按段落分割
        paragraphs = re.split(self.paragraph_separators, text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        chunks = []

        for para in paragraphs:
            para_len = len(para)

            if para_len <= self.chunk_size:
                # 段落适中,直接使用
                chunks.append(para)
            elif para_len <= self.max_chunk_size:
                # 段落稍大,按句子分割
                sent_chunks = self._chunk_by_sentences(para)
                chunks.extend(sent_chunks)
            else:
                # 段落过大,固定长度分割
                fixed_chunks = self._chunk_fixed_length(para)
                chunks.extend(fixed_chunks)

        return chunks

    def _find_sentence_boundary(
        self,
        text: str,
        start: int,
        end: int
    ) -> int:
        """寻找句子边界"""
        # 在end附近搜索句子结束符
        search_window = 100
        search_start = max(start, end - search_window)

        matches = list(re.finditer(self.sentence_endings, text[search_start:end]))
        if matches:
            last_match = matches[-1]
            return search_start + last_match.end()

        return end

    def _find_paragraph_boundary(
        self,
        text: str,
        start: int,
        end: int
    ) -> int:
        """寻找段落边界"""
        search_window = 100
        search_start = max(start, end - search_window)

        matches = list(re.finditer(self.paragraph_separators, text[search_start:end]))
        if matches:
            last_match = matches[-1]
            return search_start + last_match.end()

        return end

    def _find_word_boundary(
        self,
        text: str,
        start: int,
        end: int
    ) -> int:
        """寻找单词边界 (空格)"""
        search_window = 50
        search_start = max(start, end - search_window)

        # 从后往前找空格
        for i in range(end - 1, search_start, -1):
            if text[i] in ' \t\n':
                return i + 1

        return end

    def _split_long_sentence(self, sentence: str) -> List[str]:
        """分割过长的句子"""
        chunks = []
        words = sentence.split()
        current = []
        current_len = 0

        for word in words:
            word_len = len(word) + 1  # +1 for space
            if current_len + word_len <= self.chunk_size:
                current.append(word)
                current_len += word_len
            else:
                if current:
                    chunks.append(' '.join(current))
                current = [word]
                current_len = word_len

        if current:
            chunks.append(' '.join(current))

        return chunks

    def _get_overlap_sentences(
        self,
        sentences: List[str],
        target_overlap: int
    ) -> List[str]:
        """获取重叠的句子"""
        if not sentences:
            return []

        overlap_sentences = []
        current_overlap = 0

        # 从后往前取句子
        for sent in reversed(sentences):
            sent_len = len(sent)
            if current_overlap + sent_len <= target_overlap:
                overlap_sentences.insert(0, sent)
                current_overlap += sent_len
            else:
                break

        return overlap_sentences

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 移除多余换行 (保留段落结构)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _post_process_chunks(self, chunks: List[str]) -> List[str]:
        """后处理分块"""
        processed = []

        for chunk in chunks:
            # 移除过小的chunk
            if len(chunk) < self.min_chunk_size:
                continue

            # 截断过大的chunk
            if len(chunk) > self.max_chunk_size:
                chunk = chunk[:self.max_chunk_size]

            processed.append(chunk.strip())

        return processed

    def analyze_chunks(self, chunks: List[str]) -> dict:
        """分析分块质量"""
        if not chunks:
            return {}

        chunk_lens = [len(c) for c in chunks]

        return {
            'total_chunks': len(chunks),
            'avg_chunk_size': int(np.mean(chunk_lens)),
            'min_chunk_size': min(chunk_lens),
            'max_chunk_size': max(chunk_lens),
            'std_chunk_size': int(np.std(chunk_lens)),
            'total_chars': sum(chunk_lens)
        }
