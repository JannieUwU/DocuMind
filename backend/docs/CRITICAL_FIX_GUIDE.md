# 🔥 关键问题诊断与修复 - 搜索返回旧内容

## 问题根源分析

### 🎯 核心问题定位

经过深度代码分析，发现了**导致新文档搜索仍返回旧内容的3个关键原因**:

---

## ❌ 问题1: 搜索查询包含 NULL 对话ID的旧数据

### 问题代码位置

**文件**: `backend/custom_rag.py:363`

```python
# 当前代码 (有问题)
if conversation_id is not None:
    cursor.execute(
        "SELECT chunk_text, embedding FROM chunks
         WHERE conversation_id = ? OR conversation_id IS NULL  # ❌ 这里!!!
         LIMIT 1000",
        (conversation_id,)
    )
```

### 问题说明

这行代码的意图是向后兼容旧数据，但**副作用**是:
- 所有 `conversation_id IS NULL` 的旧块都会被包含在搜索中
- 即使你在对话A中，也会搜索到对话B/C/D的旧文档
- 这导致**上下文污染**，新文档被旧文档覆盖

### 修复方案A: 严格隔离 (推荐)

```python
# 修复后 - 严格隔离
if conversation_id is not None:
    cursor.execute(
        "SELECT chunk_text, embedding FROM chunks
         WHERE conversation_id = ?  # ✅ 仅当前对话
         LIMIT 1000",
        (conversation_id,)
    )
```

**优点**:
- ✅ 完全隔离，每个对话独立
- ✅ 不受旧数据污染
- ✅ 符合会话隔离设计

**缺点**:
- ❌ 旧数据 (conversation_id IS NULL) 无法被搜索到

### 修复方案B: 兼容模式 (可选)

```python
# 修复后 - 兼容旧数据但优先级低
if conversation_id is not None:
    # 首先搜索当前对话的文档
    cursor.execute(
        "SELECT chunk_text, embedding,
                CASE WHEN conversation_id = ? THEN 1 ELSE 0 END as priority
         FROM chunks
         WHERE conversation_id = ? OR conversation_id IS NULL
         ORDER BY priority DESC
         LIMIT 1000",
        (conversation_id, conversation_id)
    )
```

**建议**: 使用**方案A (严格隔离)** 并清理旧数据。

---

## ❌ 问题2: 旧数据未清理

### 现象

运行诊断工具可能会发现:

```
⚠️  发现 1500 个未绑定对话的旧块 (conversation_id IS NULL)
   这些块会在所有搜索中出现,可能导致污染!
```

### 解决方法

```bash
# 1. 诊断
python diagnose_vector_db.py tomyb

# 2. 清理 (先模拟)
python cleanup_orphan_chunks.py tomyb --dry-run

# 3. 实际清理
python cleanup_orphan_chunks.py tomyb
```

---

## ❌ 问题3: 嵌入缓存未失效

### 问题说明

`CustomEmbedder` 类有一个 LRU 缓存:

```python
class CustomEmbedder:
    def __init__(self, ...):
        self.cache = EmbeddingCache(max_size=200)  # 缓存
```

**潜在问题**:
- 如果服务器长时间运行，缓存可能保留旧文档的嵌入
- 相同文本的新上传会直接使用缓存，导致匹配到旧 chunks

### 解决方法

**方案1**: 重启服务器清除缓存

```bash
# 停止服务器 (Ctrl+C)
# 重新启动
python main.py
```

**方案2**: 在文档上传后清除缓存 (代码修复)

在 `main.py` 的文档上传端点添加:

```python
# 文件: main.py, 行: ~880
# 在文档上传成功后
if success:
    # 清除嵌入缓存,强制重新计算
    if user_config.get("embedder"):
        user_config["embedder"].cache = EmbeddingCache(max_size=200)
        logger.info("Cleared embedding cache after document upload")
```

---

## ❌ 问题4: 数据库连接复用导致的查询缓存

### 问题说明

SQLite 在某些情况下会缓存查询结果，特别是在使用同一个连接时。

### 解决方法

确保每次搜索都创建新连接 (当前代码已正确实现):

```python
def search(self, query_embedding, top_k=5, conversation_id=None):
    conn = sqlite3.connect(self.db_path)  # ✅ 每次新建连接
    cursor = conn.cursor()
    # ... 搜索逻辑
    conn.close()  # ✅ 及时关闭
```

---

## 🛠️ 完整修复流程

### Step 1: 应用代码修复

编辑 `backend/custom_rag.py`:

```python
# 行 361-365
if conversation_id is not None:
    cursor.execute(
        "SELECT chunk_text, embedding FROM chunks
         WHERE conversation_id = ?  # 移除 OR conversation_id IS NULL
         LIMIT 1000",
        (conversation_id,)
    )
```

### Step 2: 运行诊断

```bash
cd backend
python diagnose_vector_db.py tomyb
```

检查输出中的:
- ❌ "发现 XXX 个未绑定对话的旧块"
- ❌ "缺少 conversation_id 字段"

### Step 3: 运行迁移 (如需要)

```bash
python migrate_session_isolation.py
```

### Step 4: 清理旧数据

```bash
# 先模拟
python cleanup_orphan_chunks.py tomyb --dry-run

# 确认后执行
python cleanup_orphan_chunks.py tomyb
```

### Step 5: 重启服务器

```bash
# 停止现有服务器 (Ctrl+C)
python main.py
```

### Step 6: 验证修复

```bash
python test_session_isolation.py tomyb
```

预期输出:
```
✅ PASS: conversation_id 字段存在
✅ PASS: 所有块都已绑定到对话
✅ PASS: 不同对话的搜索结果已隔离
✅ PASS: 没有旧数据污染
```

### Step 7: 功能测试

1. **创建对话A** → 上传 `test1.pdf` → 提问 "文档讲了什么?"
   - ✅ 应基于 test1.pdf 回答

2. **创建对话B** → 上传 `test2.pdf` → 提问 "文档讲了什么?"
   - ✅ 应基于 test2.pdf 回答
   - ❌ **不应该** 提到 test1.pdf 的内容

3. **切回对话A** → 提问 "继续解释"
   - ✅ 应基于 test1.pdf 回答
   - ❌ **不应该** 提到 test2.pdf 的内容

---

## 🔍 深度调试技巧

### 查看实际执行的SQL

在 `custom_rag.py` 的 `search` 方法中添加日志:

```python
def search(self, query_embedding, top_k=5, conversation_id=None):
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()

    if conversation_id is not None:
        sql = """SELECT chunk_text, embedding FROM chunks
                 WHERE conversation_id = ?
                 LIMIT 1000"""
        logger.info(f"🔍 Search SQL: {sql}")
        logger.info(f"   conversation_id: {conversation_id}")
        cursor.execute(sql, (conversation_id,))

    # 记录搜索到的块数
    results = cursor.fetchall()
    logger.info(f"   Found {len(results)} chunks for conversation {conversation_id}")
```

### 手动验证数据库

```bash
sqlite3 custom_rag_tomyb.db
```

```sql
-- 查看所有块的分布
SELECT
    conversation_id,
    COUNT(*) as count
FROM chunks
GROUP BY conversation_id;

-- 查看特定对话的块
SELECT
    chunk_text,
    conversation_id
FROM chunks
WHERE conversation_id = 123
LIMIT 5;

-- 查找 NULL 对话的块
SELECT
    d.filename,
    COUNT(*) as chunk_count
FROM chunks c
JOIN documents d ON c.document_id = d.id
WHERE c.conversation_id IS NULL
GROUP BY d.filename;
```

---

## 📊 常见问题排查

### Q1: 新对话仍然返回旧文档内容

**可能原因**:
1. ✅ 搜索查询包含 `OR conversation_id IS NULL` → 修复SQL
2. ✅ 旧数据未清理 → 运行 `cleanup_orphan_chunks.py`
3. ✅ 嵌入缓存 → 重启服务器

### Q2: 上传文档后搜索不到

**可能原因**:
1. ❌ 文档未正确处理 → 检查后端日志
2. ❌ conversation_id 未传递 → 检查上传API日志
3. ❌ 向量嵌入失败 → 检查 API key 配置

**检查方法**:
```bash
# 查看最近上传
sqlite3 custom_rag_tomyb.db "
SELECT d.filename, c.conversation_id, COUNT(*)
FROM documents d
JOIN chunks c ON d.id = c.document_id
GROUP BY d.id
ORDER BY d.created_at DESC
LIMIT 5;
"
```

### Q3: 不同对话的文档混在一起

**检查**:
```python
# 在 main.py 的 /api/chat/message 端点
logger.info(f"Searching with conversation_id: {message.conversationId}")

search_results = rag_system.search(
    message.content,
    top_k=10,
    conversation_id=message.conversationId  # 确保传递
)

logger.info(f"Found {len(search_results)} results")
```

---

## ⚡ 性能优化建议

### 添加索引

```sql
-- 在 custom_rag.py 的 _init_db 方法中添加
CREATE INDEX IF NOT EXISTS idx_chunks_conversation_id
ON chunks(conversation_id);

CREATE INDEX IF NOT EXISTS idx_chunks_document_conversation
ON chunks(document_id, conversation_id);
```

### 限制搜索范围

```python
# 当前: LIMIT 1000
# 优化: 根据对话的块数动态调整

def search(self, query_embedding, top_k=5, conversation_id=None):
    # 先统计该对话的块数
    cursor.execute(
        "SELECT COUNT(*) FROM chunks WHERE conversation_id = ?",
        (conversation_id,)
    )
    chunk_count = cursor.fetchone()[0]

    # 动态 LIMIT
    limit = min(chunk_count, 1000)
```

---

## 📋 最终检查清单

在修复完成后，验证:

- [ ] 代码修复: 移除 `OR conversation_id IS NULL`
- [ ] 数据库迁移: conversation_id 字段存在
- [ ] 旧数据清理: 无孤立块 (或 <5%)
- [ ] 服务器重启: 清除缓存
- [ ] 诊断工具: 所有测试通过
- [ ] 功能测试: 对话A/B不互相污染
- [ ] 日志验证: 搜索SQL正确执行

---

## 🎯 总结

新文档搜索返回旧内容的**根本原因**是:

1. **搜索查询包含未绑定对话的旧块** (`OR conversation_id IS NULL`)
2. **旧数据未清理** (迁移前上传的文档)
3. **嵌入缓存** (服务器长时间运行)

**核心修复**:
- 修改 `custom_rag.py:363` 移除 `OR conversation_id IS NULL`
- 运行 `cleanup_orphan_chunks.py` 清理旧数据
- 重启服务器清除缓存

修复后，每个对话将拥有**完全隔离**的文档上下文! 🎉
