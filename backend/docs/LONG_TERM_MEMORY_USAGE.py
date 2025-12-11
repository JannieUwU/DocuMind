"""
Long-Term Memory Usage Example
演示如何在实际应用中集成长时记忆Features
"""
from memory_rag import MemoryEnhancedRAG
from custom_rag import CustomRAGSystem, CustomEmbedder
from openai import OpenAI

# ==================== initialized示例 ====================

def setup_memory_rag():
    """initialized带记忆的RAG系统"""

    # 1. 创建Embedder
    embedder = CustomEmbedder(
        api_key="your-api-key",
        base_url="https://api.openai.com/v1",
        model="text-embedding-3-large"
    )

    # 2. 创建RAG系统
    rag_system = CustomRAGSystem(
        embedder=embedder,
        db_path="vector_db.db",
        enable_web_search=True
    )

    # 3. 创建带记忆的RAG
    memory_rag = MemoryEnhancedRAG(
        rag_system=rag_system,
        enable_memory=True  # 启用长时记忆
    )

    return memory_rag


# ==================== usage examples ====================

def example_conversation_with_memory():
    """示例: 带记忆的对话"""

    memory_rag = setup_memory_rag()
    llm_client = OpenAI(api_key="your-api-key")

    # 用户信息
    user_id = 1
    conversation_id = 123

    # ===== 第一轮对话 =====
    query1 = "什么是机器学习?"

    result1 = memory_rag.answer_with_memory(
        user_id=user_id,
        conversation_id=conversation_id,
        query=query1,
        llm_client=llm_client,
        model="gpt-4-turbo",
        use_memory=True,      # 检索历史记忆
        save_to_memory=True   # 保存到记忆库
    )

    print(f"问题: {query1}")
    print(f"回答: {result1['answer']}")
    print(f"相关历史记忆: {len(result1['relevant_memories'])} 条")
    print(f"已保存到记忆ID: {result1['memory_id']}\n")


    # ===== 第二轮对话 (新会话) =====
    conversation_id = 124  # 新会话
    query2 = "深度学习和机器学习有什么区别?"

    result2 = memory_rag.answer_with_memory(
        user_id=user_id,
        conversation_id=conversation_id,
        query=query2,
        llm_client=llm_client,
        use_memory=True,  # 会检索到之前关于"机器学习"的对话!
        save_to_memory=True
    )

    print(f"问题: {query2}")
    print(f"回答: {result2['answer']}")
    print(f"相关历史记忆: {len(result2['relevant_memories'])} 条")

    # 显示检索到的历史记忆
    for idx, mem in enumerate(result2['relevant_memories'], 1):
        print(f"\n  历史记忆 {idx}:")
        print(f"  - 问题: {mem['question']}")
        print(f"  - 相似度: {mem['similarity']:.2f}")
        print(f"  - 重要性: {mem['importance']:.2f}")


def example_memory_summary():
    """示例: 获取记忆摘要"""

    memory_rag = setup_memory_rag()

    user_id = 1
    conversation_id = 125

    summary = memory_rag.get_memory_summary(
        user_id=user_id,
        conversation_id=conversation_id
    )

    print("用户记忆摘要:")
    print(f"  总记忆数: {summary['total_memories']}")
    print(f"  平均重要性: {summary['average_importance']}")
    print(f"  最近话题: {summary['recent_topics']}")


# ==================== API集成示例 ====================

"""
在 FastAPI 中集成长时记忆:

from fastapi import FastAPI, Depends
from memory_rag import MemoryEnhancedRAG

app = FastAPI()

# 全局RAG实例
memory_rag = setup_memory_rag()

@app.post("/api/chat/memory")
async def chat_with_memory(
    user_id: int,
    conversation_id: int,
    message: str,
    current_user = Depends(get_current_user)
):
    '''
    带长时记忆的聊天API

    特点:
    1. 自动检索相关历史对话
    2. 自动保存到向量记忆库
    3. 跨会话知识积累
    '''

    result = memory_rag.answer_with_memory(
        user_id=user_id,
        conversation_id=conversation_id,
        query=message,
        llm_client=llm_client,
        use_memory=True,
        save_to_memory=True
    )

    return {
        "answer": result['answer'],
        "relevant_memories": [
            {
                "question": m['question'],
                "similarity": m['similarity']
            }
            for m in result['relevant_memories']
        ],
        "memory_saved": result['memory_id'] is not None
    }


@app.get("/api/user/{user_id}/memory-stats")
async def get_memory_stats(user_id: int):
    '''获取用户记忆统计'''

    summary = memory_rag.get_memory_summary(
        user_id=user_id,
        conversation_id=0  # 不排除任何对话
    )

    return summary
"""


# ==================== 配置选项 ====================

"""
长时记忆配置建议:

1. 启用条件:
   - 适合: 知识密集型对话、技术支持、教育应用
   - 不适合: 一次性查询、隐私敏感对话

2. 性能优化:
   - 定期清理低重要性记忆 (importance < 0.3)
   - 限制检索范围 (最近500条)
   - 使用缓存加速向量检索

3. 隐私保护:
   - 用户可选择禁用记忆
   - 提供记忆删除Features
   - 严格的用户隔离 (user_id过滤)

4. 重要性评分调优:
   - 根据用户反馈调整权重
   - 考虑添加主题分类
   - 时间衰减 (旧记忆降权)
"""

if __name__ == "__main__":
    print("请参考上述示例代码集成长时记忆Features")
    print("\n主要Features:")
    print("1. 自动向量化存储对话")
    print("2. 跨会话语义检索")
    print("3. 重要性自动评分")
    print("4. 记忆统计和摘要")
