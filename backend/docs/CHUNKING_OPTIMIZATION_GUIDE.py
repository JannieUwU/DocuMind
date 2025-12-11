"""
分块参数优化完整指南
Complete Guide to Chunking Parameter Optimization

本文档总结了所有分块优化Features和最佳实践。
"""

# ============================================================
# 第一部分: 参数推荐配置表
# ============================================================

RECOMMENDED_CONFIGS = {
    '文档类型': {
        'PDF文档 (技术/学术)': {
            'chunk_size': 1000,
            'overlap': 200,
            'strategy': 'hybrid',
            'embedding_model': 'text-embedding-3-large (1536维)',
            '原因': '结构化好,段落清晰,需要保持主题完整性'
        },

        'Markdown (博客/文档)': {
            'chunk_size': 800,
            'overlap': 150,
            'strategy': 'paragraph',
            'embedding_model': 'text-embedding-3-large (1536维)',
            '原因': '有标题结构,按段落分块更合理'
        },

        '代码文档': {
            'chunk_size': 600,
            'overlap': 100,
            'strategy': 'fixed',
            'embedding_model': 'text-embedding-3-large (1536维)',
            '原因': '代码需要保持语法完整,不宜太大'
        },

        '对话/QA': {
            'chunk_size': 500,
            'overlap': 100,
            'strategy': 'sentence',
            'embedding_model': 'text-embedding-3-large (1536维)',
            '原因': '短问答,快速精确定位'
        },

        '长文章/博客': {
            'chunk_size': 1200,
            'overlap': 300,
            'strategy': 'paragraph',
            'embedding_model': 'text-embedding-3-large (1536维)',
            '原因': '需要更多上下文,保持主题连贯'
        }
    },

    '查询长度优化': {
        '短查询 (<50字)': {
            'chunk_size': '800-1000',
            'overlap': 150,
            '建议': '较小chunk,精确匹配'
        },

        '中等查询 (50-100字)': {
            'chunk_size': '1000-1200',
            'overlap': 200,
            '建议': '标准配置'
        },

        '长查询 (100-200字)': {
            'chunk_size': '1200-1500',
            'overlap': 300,
            '建议': '较大chunk,保持上下文'
        },

        '超长查询 (>200字)': {
            'chunk_size': '1500-2000',
            'overlap': 400,
            '建议': '大chunk,完整上下文'
        }
    },

    'Embedding模型选择': {
        'text-embedding-3-small (512维)': {
            'chunk_size': '500-800',
            'overlap': 100,
            '适用': '轻量应用,成本敏感'
        },

        'text-embedding-3-large (1536维)': {
            'chunk_size': '800-1500',
            'overlap': 200,
            '适用': '推荐配置,平衡性能和成本'
        },

        'text-embedding-ada-002 (1536维)': {
            'chunk_size': '800-1200',
            'overlap': 200,
            '适用': '通用场景'
        }
    }
}


# ============================================================
# 第二部分: 实际usage examples
# ============================================================

def example_1_basic_usage():
    """示例1: 基础使用"""
    from chunking_optimizer import chunking_optimizer
    from smart_chunker import SmartChunker

    # 1. 获取PDF的推荐配置
    config = chunking_optimizer.get_config('pdf')

    print(f"PDF推荐配置:")
    print(f"  chunk_size: {config['chunk_size']}")
    print(f"  overlap: {config['overlap']}")
    print(f"  strategy: {config['strategy']}")

    # 2. 创建chunker
    chunker = SmartChunker(
        chunk_size=config['chunk_size'],
        overlap=config['overlap']
    )

    # 3. 分块
    text = "你的文档内容..."
    chunks = chunker.chunk_text(text, strategy=config['strategy'])

    print(f"生成了 {len(chunks)} 个chunks")


def example_2_auto_optimization():
    """示例2: 自动优化 (基于查询统计)"""
    from chunking_optimizer import chunking_optimizer

    # 模拟收集100个查询
    sample_queries = [
        "What is machine learning?",
        "Explain neural networks",
        "How to implement backpropagation?",
        # ... 更多查询
    ]

    # 记录查询
    for query in sample_queries:
        chunking_optimizer.record_query(query)

    # 查看统计
    stats = chunking_optimizer.get_stats_summary()
    print(f"查询统计: {stats}")

    # 根据统计获取优化后的配置
    optimized_config = chunking_optimizer.get_config('pdf')
    print(f"优化后配置: {optimized_config}")


def example_3_adaptive_chunking():
    """示例3: 自适应分块 (根据文本特征)"""
    from chunking_optimizer import chunking_optimizer
    from smart_chunker import SmartChunker

    # 文本样本
    markdown_text = """
# 标题1
内容...

## 标题2
更多内容...
"""

    code_text = """
def function_name():
    return True

class MyClass:
    pass
"""

    # 自动推荐配置
    md_config = chunking_optimizer.recommend_params(markdown_text)
    code_config = chunking_optimizer.recommend_params(code_text)

    print(f"Markdown配置: {md_config}")
    print(f"Code配置: {code_config}")


def example_4_ab_testing():
    """示例4: A/B测试不同参数"""
    from chunking_optimizer import chunking_optimizer

    # 定义测试配置
    configs = [
        {'chunk_size': 800, 'overlap': 150, 'strategy': 'sentence'},
        {'chunk_size': 1000, 'overlap': 200, 'strategy': 'hybrid'},
        {'chunk_size': 1200, 'overlap': 300, 'strategy': 'paragraph'}
    ]

    test_queries = [
        "What is deep learning?",
        "Explain transformers",
        # ... 更多测试查询
    ]

    # 定义检索函数 (示例)
    def retrieval_fn(query, config):
        # 这里应该调用实际的RAG检索
        # 返回检索结果
        return []

    # 运行A/B测试
    results = chunking_optimizer.run_ab_test(configs, test_queries, retrieval_fn)

    print("A/B测试结果:")
    for name, result in results.items():
        print(f"{name}: score={result['avg_score']:.3f}")


# ============================================================
# 第三部分: 最佳实践和建议
# ============================================================

BEST_PRACTICES = """
最佳实践总结
===============

1. chunk_size选择原则:
   ✓ default1000字符,适合大多数场景
   ✓ 技术文档: 800-1200 (保持概念完整)
   ✓ 对话QA: 500-800 (快速定位)
   ✓ 长文章: 1200-1500 (更多上下文)
   ✗ 避免 <500 (上下文不足)
   ✗ 避免 >2000 (检索粒度太粗)

2. overlap选择原则:
   ✓ 一般为chunk_size的20-30%
   ✓ 最小100字符
   ✓ 最大chunk_size的40%
   ✓ 重要文档可增加至30-40% (更多上下文)

3. strategy选择:
   - auto: 让系统自动选择 (推荐!)
   - sentence: 短文本,问答类
   - paragraph: 有标题结构的文档
   - hybrid: 通用场景 (default)
   - fixed: 代码等特殊场景

4. 动态优化流程:
   Step 1: 初期使用default配置
   Step 2: 收集查询统计 (100+条)
   Step 3: 根据统计调整参数
   Step 4: A/B测试验证效果
   Step 5: 持续监控和优化

5. 常见问题和解决:

   Q: 检索结果不准确?
   A: 减小chunk_size,提高精确度

   Q: 上下文不连贯?
   A: 增大overlap (200 → 300)

   Q: 速度太慢?
   A: 减小chunk_size,减少向量数量

   Q: 如何选择embedding模型?
   A: text-embedding-3-large (推荐)
      - 1536维,性能最佳
      - 适合chunk_size: 800-1500

6. 性能优化建议:
   ✓ 使用SmartChunker的auto模式
   ✓ 定期查看chunking_optimizer统计
   ✓ 根据用户反馈调整参数
   ✓ 对不同类型文档使用不同配置
   ✓ 监控检索准确率和响应时间

7. 测试和验证:
   - 准备测试集 (50+个典型查询)
   - 使用A/B测试对比配置
   - 监控关键指标:
     * 检索准确率
     * 平均响应时间
     * 用户满意度
     * chunk命中分布

8. 生产环境配置推荐:
   default配置:
   {
       'chunk_size': 1000,
       'overlap': 200,
       'strategy': 'auto'
   }

   高质量场景 (成本不敏感):
   {
       'chunk_size': 1200,
       'overlap': 300,
       'strategy': 'hybrid'
   }

   快速响应场景 (速度优先):
   {
       'chunk_size': 800,
       'overlap': 150,
       'strategy': 'sentence'
   }
"""


# ============================================================
# 第四部分: 参数调优检查清单
# ============================================================

TUNING_CHECKLIST = """
参数调优检查清单
=================

□ 1. 数据收集
  □ 收集至少100条真实查询
  □ 统计平均查询长度
  □ 分析查询类型分布
  □ 记录用户反馈

□ 2. 文档分析
  □ 确定主要文档类型
  □ 分析文档结构特点
  □ 测量平均段落长度
  □ 检查是否有标题/章节

□ 3. 初始配置
  □ 根据文档类型选择基础配置
  □ 使用SmartChunker的auto模式
  □ 启用chunking_optimizer统计收集

□ 4. 测试验证
  □ 准备50+测试查询
  □ 运行A/B测试
  □ 对比不同配置效果
  □ 记录准确率和响应时间

□ 5. 优化调整
  □ 根据测试结果调整参数
  □ 查询短 → 减小chunk_size
  □ 上下文断裂 → 增大overlap
  □ 检索不准 → 调整strategy

□ 6. 部署监控
  □ 部署最优配置
  □ 持续收集统计数据
  □ 定期(每月)审查性能
  □ 根据反馈微调参数

□ 7. 长期维护
  □ 每季度进行A/B测试
  □ 关注新的embedding模型
  □ 优化分块算法
  □ 更新最佳实践
"""


if __name__ == "__main__":
    print("=" * 70)
    print("分块参数优化完整指南")
    print("=" * 70)
    print(BEST_PRACTICES)
    print("\n" + TUNING_CHECKLIST)
    print("\n运行示例:")
    example_1_basic_usage()
