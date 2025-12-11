"""
诊断脚本：检查对话和文件的绑定情况

运行方式：
cd backend
venv/Scripts/python.exe diagnose_conversation.py <username>
"""
import sqlite3
import sys
from pathlib import Path

def diagnose_conversations(username="testuser"):
    """诊断对话隔离问题"""

    # 1. 检查用户数据库
    users_db = "users.db"
    rag_db = f"custom_rag_{username}.db"

    print(f"\n{'='*60}")
    print(f"诊断用户: {username}")
    print(f"{'='*60}\n")

    # 2. 检查users.db中的对话和文档
    if not Path(users_db).exists():
        print(f"❌ 用户数据库不存在: {users_db}")
        return

    conn_users = sqlite3.connect(users_db)
    cursor_users = conn_users.cursor()

    # 获取用户ID
    cursor_users.execute("SELECT id FROM users WHERE username = ?", (username,))
    user_row = cursor_users.fetchone()
    if not user_row:
        print(f"❌ 用户不存在: {username}")
        return

    user_id = user_row[0]
    print(f"[OK] User ID: {user_id}\n")

    # 检查对话
    print("Conversations:")
    cursor_users.execute("""
        SELECT id, title, created_at, updated_at
        FROM conversations
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))

    conversations = cursor_users.fetchall()
    if not conversations:
        print("  没有找到对话\n")
    else:
        for conv_id, title, created, updated in conversations:
            cursor_users.execute("""
                SELECT COUNT(*) FROM messages WHERE conversation_id = ?
            """, (conv_id,))
            msg_count = cursor_users.fetchone()[0]
            print(f"  - ID {conv_id}: {title}")
            print(f"    消息数: {msg_count}")
            print(f"    创建时间: {created}")
            print(f"    更新时间: {updated}\n")

    # 检查文档绑定
    print("📄 文档绑定情况:")
    cursor_users.execute("""
        SELECT id, filename, conversation_id, uploaded_at
        FROM user_documents
        WHERE user_id = ?
        ORDER BY uploaded_at DESC
    """, (user_id,))

    documents = cursor_users.fetchall()
    if not documents:
        print("  没有找到文档\n")
    else:
        for doc_id, filename, conv_id, uploaded in documents:
            status = f"绑定到对话 {conv_id}" if conv_id else "❌ 未绑定对话 (NULL)"
            print(f"  - {filename}")
            print(f"    文档ID: {doc_id}")
            print(f"    {status}")
            print(f"    上传时间: {uploaded}\n")

    conn_users.close()

    # 3. 检查RAG数据库中的chunks
    if not Path(rag_db).exists():
        print(f"⚠️  RAG数据库不存在: {rag_db}")
        print("   (如果没有上传过文件，这是正常的)\n")
        return

    conn_rag = sqlite3.connect(rag_db)
    cursor_rag = conn_rag.cursor()

    print(f"🔍 RAG数据库分析 ({rag_db}):")

    # 检查所有conversation_id
    cursor_rag.execute("""
        SELECT conversation_id, COUNT(*) as chunk_count
        FROM chunks
        GROUP BY conversation_id
        ORDER BY conversation_id
    """)

    rag_conversations = cursor_rag.fetchall()
    if not rag_conversations:
        print("  没有找到chunks\n")
    else:
        print("\n  按对话ID分组的chunks数量:")
        for conv_id, count in rag_conversations:
            if conv_id is None:
                print(f"  ❌ NULL (未绑定对话): {count} chunks")
            else:
                # 检查是否匹配user_documents中的conversation_id
                cursor_users = sqlite3.connect(users_db).cursor()
                cursor_users.execute("""
                    SELECT COUNT(*) FROM user_documents
                    WHERE user_id = ? AND conversation_id = ?
                """, (user_id, conv_id))
                doc_count = cursor_users.fetchone()[0]

                match_status = "✓ 匹配" if doc_count > 0 else "⚠️  未匹配user_documents"
                print(f"  - 对话 {conv_id}: {count} chunks ({match_status})")
        print()

    # 检查NULL conversation_id的chunks
    cursor_rag.execute("""
        SELECT COUNT(*) FROM chunks WHERE conversation_id IS NULL
    """)
    null_count = cursor_rag.fetchone()[0]

    if null_count > 0:
        print(f"⚠️  发现 {null_count} 个未绑定对话的chunks (conversation_id=NULL)")
        print("   这些chunks可能导致跨对话数据泄漏\n")

        # 显示NULL chunks的来源文档
        cursor_rag.execute("""
            SELECT DISTINCT document_id, COUNT(*) as count
            FROM chunks
            WHERE conversation_id IS NULL
            GROUP BY document_id
        """)
        null_docs = cursor_rag.fetchall()
        if null_docs:
            print("   来源文档:")
            for doc_id, count in null_docs:
                cursor_rag.execute("""
                    SELECT filename FROM documents WHERE id = ?
                """, (doc_id,))
                filename_row = cursor_rag.fetchone()
                filename = filename_row[0] if filename_row else "未知"
                print(f"   - 文档ID {doc_id} ({filename}): {count} chunks")
            print()

    conn_rag.close()

    # 4. 总结
    print(f"{'='*60}")
    print("诊断总结:")
    print(f"{'='*60}\n")

    if null_count > 0:
        print("❌ 发现问题:")
        print(f"   - {null_count} 个chunks没有绑定conversation_id")
        print("   - 这可能导致新对话搜索到旧文件的内容")
        print("\n建议:")
        print("   1. 运行清理脚本删除NULL chunks")
        print("   2. 确保上传文件时传递conversation_id")
        print("   3. 测试新对话是否仍然能搜到旧文件\n")
    else:
        if not conversations:
            print("✓ 没有发现问题（但也没有对话数据）\n")
        else:
            print("✓ 所有chunks都已正确绑定conversation_id")
            print("✓ 对话隔离机制正常\n")

if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else input("请输入username: ").strip()
    if username:
        diagnose_conversations(username)
    else:
        print("错误: username不能为空")
