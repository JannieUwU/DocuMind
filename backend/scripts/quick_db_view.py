"""
Quick Database Viewer - 快速查看数据库内容
Run: python quick_db_view.py
"""
import sqlite3
import os
import sys
from tabulate import tabulate

# Fix Windows encoding issue
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")

def quick_view():
    """Quick overview of database"""
    if not os.path.exists(DB_PATH):
        print(f"错误: 数据库文件不存在: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n" + "="*80)
    print("快速数据库概览 - RAG Chat 应用")
    print("="*80)

    # Statistics
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM conversations")
    conv_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM messages")
    msg_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM user_documents")
    doc_count = cursor.fetchone()[0]

    print(f"\n📊 statistics:")
    print(f"  - 用户数: {user_count}")
    print(f"  - 对话数: {conv_count}")
    print(f"  - 消息数: {msg_count}")
    print(f"  - 文档数: {doc_count}")

    # Users
    print(f"\n👥 用户列表:")
    cursor.execute("""
        SELECT u.id, u.username, u.email,
               COUNT(DISTINCT c.id) as conversations,
               COUNT(DISTINCT d.id) as documents,
               u.created_at
        FROM users u
        LEFT JOIN conversations c ON u.id = c.user_id
        LEFT JOIN user_documents d ON u.id = d.user_id
        GROUP BY u.id
        ORDER BY u.created_at DESC
    """)
    users = cursor.fetchall()

    if users:
        headers = ["ID", "username", "邮箱", "对话数", "文档数", "注册时间"]
        print(tabulate(users, headers=headers, tablefmt="simple"))
    else:
        print("  没有用户")

    # Recent conversations
    print(f"\n💬 最近的对话:")
    cursor.execute("""
        SELECT c.id, u.username, c.title,
               COUNT(m.id) as msg_count,
               c.updated_at
        FROM conversations c
        JOIN users u ON c.user_id = u.id
        LEFT JOIN messages m ON c.id = m.conversation_id
        GROUP BY c.id
        ORDER BY c.updated_at DESC
        LIMIT 10
    """)
    recent_convs = cursor.fetchall()

    if recent_convs:
        headers = ["对话ID", "用户", "标题", "消息数", "最后更新"]
        print(tabulate(recent_convs, headers=headers, tablefmt="simple"))
    else:
        print("  没有对话")

    # Database info
    db_size = os.path.getsize(DB_PATH) / 1024
    print(f"\n💾 数据库信息:")
    print(f"  - 文件路径: {DB_PATH}")
    print(f"  - 文件大小: {db_size:.2f} KB")

    print("\n" + "="*80)
    print("💡 提示: 运行 'python db_manager.py' 进行详细管理")
    print("="*80 + "\n")

    conn.close()

if __name__ == "__main__":
    quick_view()
