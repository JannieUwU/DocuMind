"""
Adaptive Chunking Optimizer
动态分块参数优化器 - 根据文档类型和查询统计自动调整分块参数

特点:
1. 查询长度统计分析
2. 文档类型识别
3. 参数自适应调整
4. A/B测试框架
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging
from collections import defaultdict
import json
import os

logger = logging.getLogger(__name__)


class ChunkingOptimizer:
    """
    分块参数优化器

    Features:
    1. 收集查询统计数据
    2. 分析最优分块参数
    3. 动态调整chunk_size和overlap
    4. A/B测试不同参数组合
    """

    def __init__(self, stats_file: str = "chunking_stats.json"):
        self.stats_file = stats_file
        self.stats = self._load_stats()

        # default参数配置
        self.configs = {
            'pdf': {
                'chunk_size': 1000,
                'overlap': 200,
                'strategy': 'hybrid',
                'description': 'PDF文档 (结构化)'
            },
            'markdown': {
                'chunk_size': 800,
                'overlap': 150,
                'strategy': 'paragraph',
                'description': 'Markdown (标题结构)'
            },
            'code': {
                'chunk_size': 600,
                'overlap': 100,
                'strategy': 'fixed',
                'description': '代码文档 (保持完整性)'
            },
            'dialogue': {
                'chunk_size': 500,
                'overlap': 100,
                'strategy': 'sentence',
                'description': '对话/QA (短问答)'
            },
            'article': {
                'chunk_size': 1200,
                'overlap': 300,
                'strategy': 'paragraph',
                'description': '长文章 (保持主题)'
            }
        }

    def _load_stats(self) -> Dict:
        """加载历史统计数据"""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass

        return {
            'query_lengths': [],
            'chunk_hits': defaultdict(int),
            'total_queries': 0,
            'avg_query_length': 0
        }

    def _save_stats(self):
        """保存统计数据"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save stats: {e}")

    def record_query(self, query: str, retrieved_chunk_size: Optional[int] = None):
        """
        记录查询统计

        Args:
            query: 查询文本
            retrieved_chunk_size: 检索到的chunk大小
        """
        query_len = len(query)
        self.stats['query_lengths'].append(query_len)
        self.stats['total_queries'] += 1

        if retrieved_chunk_size:
            # 记录命中的chunk大小
            size_bucket = (retrieved_chunk_size // 100) * 100
            self.stats['chunk_hits'][str(size_bucket)] += 1

        # 更新平均查询长度
        self.stats['avg_query_length'] = int(
            np.mean(self.stats['query_lengths'][-1000:])  # 最近1000次
        )

        # 定期保存 (每100次查询)
        if self.stats['total_queries'] % 100 == 0:
            self._save_stats()
            logger.info(f"Stats saved: {self.stats['total_queries']} queries")

    def get_optimal_chunk_size(self, doc_type: str = 'pdf') -> int:
        """
        获取最优chunk_size

        规则:
        1. 基于文档类型的default值
        2. 根据平均查询长度调整
        3. 考虑检索命中分布
        """
        # 基础配置
        base_size = self.configs[doc_type]['chunk_size']

        # 如果有统计数据,根据查询长度调整
        if self.stats['total_queries'] > 100:
            avg_query = self.stats['avg_query_length']

            # 查询较短 → chunk也应该短一些
            if avg_query < 50:
                multiplier = 0.8
            elif avg_query < 100:
                multiplier = 1.0
            elif avg_query < 200:
                multiplier = 1.2
            else:
                multiplier = 1.5

            optimized_size = int(base_size * multiplier)

            logger.info(
                f"Optimized chunk_size: {base_size} → {optimized_size} "
                f"(based on avg query length: {avg_query})"
            )

            return optimized_size

        return base_size

    def get_optimal_overlap(self, chunk_size: int, doc_type: str = 'pdf') -> int:
        """
        获取最优overlap

        规则:
        1. overlap = chunk_size * 0.2-0.3
        2. 至少100字符
        3. 最多chunk_size的40%
        """
        base_overlap = self.configs[doc_type]['overlap']

        # 动态计算 (20-30%的chunk_size)
        min_overlap = int(chunk_size * 0.2)
        max_overlap = int(chunk_size * 0.4)

        optimized_overlap = max(
            100,  # 最小100
            min(max_overlap, base_overlap)
        )

        return optimized_overlap

    def get_config(self, doc_type: str = 'pdf') -> Dict:
        """
        获取完整配置

        Args:
            doc_type: 文档类型 (pdf/markdown/code/dialogue/article)

        Returns:
            {
                'chunk_size': int,
                'overlap': int,
                'strategy': str,
                'description': str
            }
        """
        if doc_type not in self.configs:
            logger.warning(f"Unknown doc_type: {doc_type}, using 'pdf'")
            doc_type = 'pdf'

        # 获取优化后的参数
        chunk_size = self.get_optimal_chunk_size(doc_type)
        overlap = self.get_optimal_overlap(chunk_size, doc_type)

        config = self.configs[doc_type].copy()
        config['chunk_size'] = chunk_size
        config['overlap'] = overlap

        return config

    def recommend_params(self, text: str) -> Dict:
        """
        根据文本内容推荐参数

        Args:
            text: 输入文本

        Returns:
            推荐的配置
        """
        # 分析文本特征
        features = self._analyze_text_features(text)

        # 根据特征选择文档类型
        doc_type = self._classify_doc_type(features)

        # 获取配置
        config = self.get_config(doc_type)

        logger.info(
            f"Recommended config for {doc_type}: "
            f"chunk_size={config['chunk_size']}, overlap={config['overlap']}"
        )

        return config

    def _analyze_text_features(self, text: str) -> Dict:
        """分析文本特征"""
        lines = text.split('\n')
        sentences = text.split('.')

        return {
            'length': len(text),
            'lines': len(lines),
            'sentences': len(sentences),
            'avg_line_length': len(text) / max(1, len(lines)),
            'avg_sentence_length': len(text) / max(1, len(sentences)),
            'has_code': '```' in text or 'def ' in text or 'class ' in text,
            'has_markdown_headers': text.count('\n#') > 0,
            'has_paragraphs': text.count('\n\n') > 2,
            'is_dialogue': text.count('?') > len(text) / 200  # 问号密度
        }

    def _classify_doc_type(self, features: Dict) -> str:
        """根据特征分类文档类型"""
        # 规则基础分类
        if features['has_code']:
            return 'code'

        if features['has_markdown_headers']:
            return 'markdown'

        if features['is_dialogue']:
            return 'dialogue'

        if features['has_paragraphs'] and features['avg_sentence_length'] > 150:
            return 'article'

        # defaultPDF
        return 'pdf'

    def run_ab_test(
        self,
        configs: List[Dict],
        test_queries: List[str],
        retrieval_fn
    ) -> Dict:
        """
        运行A/B测试

        Args:
            configs: 配置列表 [{chunk_size, overlap, strategy}]
            test_queries: 测试查询列表
            retrieval_fn: 检索函数 (query, config) -> results

        Returns:
            测试结果
        """
        results = {}

        for idx, config in enumerate(configs):
            logger.info(f"Testing config {idx+1}/{len(configs)}: {config}")

            scores = []
            for query in test_queries:
                # 执行检索
                retrieved = retrieval_fn(query, config)

                # 评分 (这里简化,实际应该有ground truth)
                score = len(retrieved)  # 简化评分
                scores.append(score)

            results[f"config_{idx}"] = {
                'config': config,
                'avg_score': np.mean(scores),
                'std_score': np.std(scores)
            }

        return results

    def get_stats_summary(self) -> Dict:
        """获取统计摘要"""
        if not self.stats['query_lengths']:
            return {
                'total_queries': 0,
                'message': 'No data collected yet'
            }

        query_lens = self.stats['query_lengths'][-1000:]  # 最近1000次

        return {
            'total_queries': self.stats['total_queries'],
            'avg_query_length': int(np.mean(query_lens)),
            'median_query_length': int(np.median(query_lens)),
            'min_query_length': min(query_lens),
            'max_query_length': max(query_lens),
            'query_length_distribution': {
                '<50': sum(1 for x in query_lens if x < 50),
                '50-100': sum(1 for x in query_lens if 50 <= x < 100),
                '100-200': sum(1 for x in query_lens if 100 <= x < 200),
                '>200': sum(1 for x in query_lens if x >= 200)
            },
            'top_chunk_sizes': dict(
                sorted(
                    self.stats['chunk_hits'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
            )
        }


# ==================== 全局优化器实例 ====================

chunking_optimizer = ChunkingOptimizer()


# ==================== usage examples ====================

def example_usage():
    """usage examples"""
    from smart_chunker import SmartChunker

    # 1. 获取文档类型的推荐配置
    config = chunking_optimizer.get_config('pdf')
    print(f"PDF config: {config}")

    # 2. 创建chunker
    chunker = SmartChunker(
        chunk_size=config['chunk_size'],
        overlap=config['overlap']
    )

    # 3. 分块
    text = "Your document text here..."
    chunks = chunker.chunk_text(text, strategy=config['strategy'])

    # 4. 记录查询统计 (在RAG查询时调用)
    query = "User question"
    chunking_optimizer.record_query(query, retrieved_chunk_size=len(chunks[0]))

    # 5. 查看统计
    stats = chunking_optimizer.get_stats_summary()
    print(f"Stats: {stats}")


if __name__ == "__main__":
    print("Chunking Optimizer - usage examples:")
    print("\n1. 获取推荐配置:")

    for doc_type in ['pdf', 'markdown', 'code', 'dialogue', 'article']:
        config = chunking_optimizer.get_config(doc_type)
        print(f"  {doc_type}: chunk_size={config['chunk_size']}, "
              f"overlap={config['overlap']}, strategy={config['strategy']}")

    print("\n2. 文本分析推荐:")
    sample_text = """
# Machine Learning Guide

Machine learning is a subset of AI. It has three main types:

1. Supervised learning
2. Unsupervised learning
3. Reinforcement learning
"""

    recommended = chunking_optimizer.recommend_params(sample_text)
    print(f"  Recommended: {recommended}")
