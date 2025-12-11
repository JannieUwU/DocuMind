"""
SQLite Database Management Tool
Run: python db_manager.py
"""
import sqlite3
import os
import sys
from datetime import datetime
from tabulate import tabulate

# Fix Windows encoding issue
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")

def get_connection():
    """Get database connection"""
    return sqlite3.connect(DB_PATH)

def show_menu():
    """Display main menu"""
    print("\n" + "="*60)
    print("SQLite Database Manager - RAG Chat Application")
    print("="*60)
    print("Database:", DB_PATH)
    print("\n选项:")
    print("1. 查看所有用户")
    print("2. 查看用户详情")
    print("3. 查看所有对话")
    print("4. 查看对话消息")
    print("5. 查看用户文档")
    print("6. 删除用户")
    print("7. 删除对话")
    print("8. 执行自定义 SQL 查询")
    print("9. 数据库统计")
    print("0. 退出")
    print("="*60)

def list_users():
    """List all users"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, email, created_at, updated_at
        FROM users
        ORDER BY created_at DESC
    """)
    users = cursor.fetchall()
    conn.close()

    if users:
        headers = ["ID", "username", "邮箱", "创建时间", "更新时间"]
        print("\n" + tabulate(users, headers=headers, tablefmt="grid"))
        print(f"\n总计: {len(users)} 个用户")
    else:
        print("\n没有找到用户")

def show_user_details():
    """Show detailed user information"""
    username = input("\n输入username: ").strip()

    conn = get_connection()
    cursor = conn.cursor()

    # Get user info
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if not user:
        print(f"\n用户 '{username}' 不存在")
        conn.close()
        return

    user_id = user[0]
    print(f"\n{'='*60}")
    print(f"用户信息:")
    print(f"{'='*60}")
    print(f"ID: {user[0]}")
    print(f"username: {user[1]}")
    print(f"邮箱: {user[2]}")
    print(f"创建时间: {user[4]}")
    print(f"更新时间: {user[5]}")

    # Get conversation count
    cursor.execute("SELECT COUNT(*) FROM conversations WHERE user_id = ?", (user_id,))
    conv_count = cursor.fetchone()[0]
    print(f"对话数量: {conv_count}")

    # Get document count
    cursor.execute("SELECT COUNT(*) FROM user_documents WHERE user_id = ?", (user_id,))
    doc_count = cursor.fetchone()[0]
    print(f"文档数量: {doc_count}")

    # Get total message count
    cursor.execute("""
        SELECT COUNT(*) FROM messages m
        JOIN conversations c ON m.conversation_id = c.id
        WHERE c.user_id = ?
    """, (user_id,))
    msg_count = cursor.fetchone()[0]
    print(f"总消息数: {msg_count}")

    conn.close()

def list_conversations():
    """List all conversations"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, u.username, c.title, c.created_at, c.updated_at,
               COUNT(m.id) as message_count
        FROM conversations c
        JOIN users u ON c.user_id = u.id
        LEFT JOIN messages m ON c.id = m.conversation_id
        GROUP BY c.id
        ORDER BY c.updated_at DESC
    """)
    conversations = cursor.fetchall()
    conn.close()

    if conversations:
        headers = ["对话ID", "用户", "标题", "创建时间", "更新时间", "消息数"]
        print("\n" + tabulate(conversations, headers=headers, tablefmt="grid"))
        print(f"\n总计: {len(conversations)} 个对话")
    else:
        print("\n没有找到对话")

def show_conversation_messages():
    """Show messages in a conversation"""
    conv_id = input("\n输入对话ID: ").strip()

    try:
        conv_id = int(conv_id)
    except ValueError:
        print("\n无效的对话ID")
        return

    conn = get_connection()
    cursor = conn.cursor()

    # Get conversation info
    cursor.execute("""
        SELECT c.title, u.username
        FROM conversations c
        JOIN users u ON c.user_id = u.id
        WHERE c.id = ?
    """, (conv_id,))
    conv_info = cursor.fetchone()

    if not conv_info:
        print(f"\n对话 ID {conv_id} 不存在")
        conn.close()
        return

    print(f"\n{'='*60}")
    print(f"对话: {conv_info[0]}")
    print(f"用户: {conv_info[1]}")
    print(f"{'='*60}\n")

    # Get messages
    cursor.execute("""
        SELECT id, role, content, created_at
        FROM messages
        WHERE conversation_id = ?
        ORDER BY created_at ASC
    """, (conv_id,))
    messages = cursor.fetchall()

    if messages:
        for msg in messages:
            role_label = "用户" if msg[1] == "user" else "AI"
            print(f"[{msg[3]}] {role_label}:")
            print(f"  {msg[2][:200]}{'...' if len(msg[2]) > 200 else ''}\n")
        print(f"总计: {len(messages)} 条消息")
    else:
        print("该对话没有消息")

    conn.close()

def list_documents():
    """List user documents"""
    username = input("\n输入username（留空显示所有）: ").strip()

    conn = get_connection()
    cursor = conn.cursor()

    if username:
        cursor.execute("""
            SELECT d.id, u.username, d.filename, d.file_path, d.uploaded_at
            FROM user_documents d
            JOIN users u ON d.user_id = u.id
            WHERE u.username = ?
            ORDER BY d.uploaded_at DESC
        """, (username,))
    else:
        cursor.execute("""
            SELECT d.id, u.username, d.filename, d.file_path, d.uploaded_at
            FROM user_documents d
            JOIN users u ON d.user_id = u.id
            ORDER BY d.uploaded_at DESC
        """)

    documents = cursor.fetchall()
    conn.close()

    if documents:
        headers = ["ID", "用户", "文件名", "路径", "上传时间"]
        print("\n" + tabulate(documents, headers=headers, tablefmt="grid"))
        print(f"\n总计: {len(documents)} 个文档")
    else:
        print("\n没有找到文档")

def delete_user():
    """Delete a user and all associated data"""
    username = input("\n输入要删除的username: ").strip()

    conn = get_connection()
    cursor = conn.cursor()

    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if not user:
        print(f"\n用户 '{username}' 不存在")
        conn.close()
        return

    confirm = input(f"\n确定要删除用户 '{username}' 及其所有数据吗？(yes/no): ").strip().lower()

    if confirm == 'yes':
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        print(f"\n用户 '{username}' 已删除（包括所有对话、消息和文档记录）")
    else:
        print("\n取消删除")

    conn.close()

def delete_conversation():
    """Delete a conversation"""
    conv_id = input("\n输入要删除的对话ID: ").strip()

    try:
        conv_id = int(conv_id)
    except ValueError:
        print("\n无效的对话ID")
        return

    conn = get_connection()
    cursor = conn.cursor()

    # Check if conversation exists
    cursor.execute("SELECT title FROM conversations WHERE id = ?", (conv_id,))
    conv = cursor.fetchone()

    if not conv:
        print(f"\n对话 ID {conv_id} 不存在")
        conn.close()
        return

    confirm = input(f"\n确定要删除对话 '{conv[0]}' 及其所有消息吗？(yes/no): ").strip().lower()

    if confirm == 'yes':
        cursor.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
        conn.commit()
        print(f"\n对话 ID {conv_id} 已删除（包括所有消息）")
    else:
        print("\n取消删除")

    conn.close()

def execute_custom_query():
    """Execute custom SQL query"""
    print("\n输入 SQL 查询（输入 'exit' 退出）:")
    query = input("> ").strip()

    if query.lower() == 'exit':
        return

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(query)

        if query.strip().upper().startswith("SELECT"):
            results = cursor.fetchall()
            if results:
                # Get column names
                columns = [desc[0] for desc in cursor.description]
                print("\n" + tabulate(results, headers=columns, tablefmt="grid"))
                print(f"\n返回 {len(results)} 行")
            else:
                print("\n查询没有返回结果")
        else:
            conn.commit()
            print(f"\n查询执行成功，影响 {cursor.rowcount} 行")
    except Exception as e:
        print(f"\n错误: {e}")
    finally:
        conn.close()

def show_statistics():
    """Show database statistics"""
    conn = get_connection()
    cursor = conn.cursor()

    print(f"\n{'='*60}")
    print("数据库统计")
    print(f"{'='*60}")

    # User count
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    print(f"用户总数: {user_count}")

    # Conversation count
    cursor.execute("SELECT COUNT(*) FROM conversations")
    conv_count = cursor.fetchone()[0]
    print(f"对话总数: {conv_count}")

    # Message count
    cursor.execute("SELECT COUNT(*) FROM messages")
    msg_count = cursor.fetchone()[0]
    print(f"消息总数: {msg_count}")

    # Document count
    cursor.execute("SELECT COUNT(*) FROM user_documents")
    doc_count = cursor.fetchone()[0]
    print(f"文档总数: {doc_count}")

    # Most active user
    cursor.execute("""
        SELECT u.username, COUNT(c.id) as conv_count
        FROM users u
        LEFT JOIN conversations c ON u.id = c.user_id
        GROUP BY u.id
        ORDER BY conv_count DESC
        LIMIT 1
    """)
    active_user = cursor.fetchone()
    if active_user:
        print(f"最活跃用户: {active_user[0]} ({active_user[1]} 个对话)")

    # Database size
    db_size = os.path.getsize(DB_PATH) / 1024  # KB
    print(f"数据库大小: {db_size:.2f} KB")

    print(f"{'='*60}")

    conn.close()

def main():
    """Main function"""
    if not os.path.exists(DB_PATH):
        print(f"\n错误: 数据库文件不存在: {DB_PATH}")
        return

    while True:
        show_menu()
        choice = input("\n请选择操作 (0-9): ").strip()

        try:
            if choice == '1':
                list_users()
            elif choice == '2':
                show_user_details()
            elif choice == '3':
                list_conversations()
            elif choice == '4':
                show_conversation_messages()
            elif choice == '5':
                list_documents()
            elif choice == '6':
                delete_user()
            elif choice == '7':
                delete_conversation()
            elif choice == '8':
                execute_custom_query()
            elif choice == '9':
                show_statistics()
            elif choice == '0':
                print("\n再见！")
                break
            else:
                print("\n无效的选择，请重试")
        except Exception as e:
            print(f"\n发生错误: {e}")

        input("\n按 Enter 继续...")

if __name__ == "__main__":
    main()
