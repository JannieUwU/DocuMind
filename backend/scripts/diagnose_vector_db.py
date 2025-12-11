"""
向量数据库诊断工具 - 深度排查文档检索问题

使用方法:
    python diagnose_vector_db.py <username> [conversation_id]

示例:
    python diagnose_vector_db.py tomyb
    python diagnose_vector_db.py tomyb 123
"""
import sqlite3
import sys
import os
from pathlib import Path
from datetime import datetime
import json

class VectorDBDiagnostics:
    def __init__(self, username):
        self.username = username
        self.vector_db_path = f"custom_rag_{username}.db"
        self.users_db_path = "users.db"
        self.issues_found = []
        self.warnings = []

    def check_db_exists(self):
        """检查数据库文件是否存在"""
        print("\n" + "="*60)
        print("📁 检查数据库文件")
        print("="*60)

        if not os.path.exists(self.vector_db_path):
            self.issues_found.append(f"❌ 向量数据库不存在: {self.vector_db_path}")
            print(f"❌ 向量数据库不存在: {self.vector_db_path}")
            return False
        else:
            size = os.path.getsize(self.vector_db_path) / 1024 / 1024
            print(f"✅ 向量数据库存在: {self.vector_db_path} ({size:.2f} MB)")

        if not os.path.exists(self.users_db_path):
            self.issues_found.append(f"❌ 用户数据库不存在: {self.users_db_path}")
            print(f"❌ 用户数据库不存在: {self.users_db_path}")
            return False
        else:
            size = os.path.getsize(self.users_db_path) / 1024 / 1024
            print(f"✅ 用户数据库存在: {self.users_db_path} ({size:.2f} MB)")

        return True

    def check_schema(self):
        """检查数据库表结构"""
        print("\n" + "="*60)
        print("🏗️  检查数据库表结构")
        print("="*60)

        # 检查向量数据库
        conn = sqlite3.connect(self.vector_db_path)
        cursor = conn.cursor()

        # 检查 chunks 表是否有 conversation_id
        cursor.execute("PRAGMA table_info(chunks)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        print(f"\n📋 chunks 表字段:")
        for col, dtype in columns.items():
            print(f"   - {col}: {dtype}")

        if 'conversation_id' not in columns:
            self.issues_found.append("❌ chunks 表缺少 conversation_id 字段!")
            print("\n❌ 缺少 conversation_id 字段 - 需要运行迁移脚本!")
        else:
            print("\n✅ conversation_id 字段存在")

        conn.close()

        # 检查用户数据库
        conn = sqlite3.connect(self.users_db_path)
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(user_documents)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        print(f"\n📋 user_documents 表字段:")
        for col, dtype in columns.items():
            print(f"   - {col}: {dtype}")

        if 'conversation_id' not in columns:
            self.issues_found.append("❌ user_documents 表缺少 conversation_id 字段!")
            print("\n❌ 缺少 conversation_id 字段 - 需要运行迁移脚本!")
        else:
            print("\n✅ conversation_id 字段存在")

        conn.close()

    def analyze_chunks_distribution(self):
        """分析 chunks 的分布情况"""
        print("\n" + "="*60)
        print("📊 分析文档块 (chunks) 分布")
        print("="*60)

        conn = sqlite3.connect(self.vector_db_path)
        cursor = conn.cursor()

        # 总块数
        cursor.execute("SELECT COUNT(*) FROM chunks")
        total_chunks = cursor.fetchone()[0]
        print(f"\n总块数: {total_chunks}")

        if total_chunks == 0:
            self.warnings.append("⚠️  向量数据库中没有任何文档块!")
            print("⚠️  向量数据库为空!")
            conn.close()
            return

        # 按 conversation_id 分组统计
        cursor.execute("""
            SELECT
                conversation_id,
                COUNT(*) as chunk_count,
                MIN(chunk_index) as min_index,
                MAX(chunk_index) as max_index
            FROM chunks
            GROUP BY conversation_id
            ORDER BY conversation_id
        """)

        print("\n按对话ID分组:")
        print(f"{'对话ID':<15} {'块数量':<10} {'索引范围':<15}")
        print("-" * 45)

        null_conversation_chunks = 0
        for row in cursor.fetchall():
            conv_id = row[0] if row[0] is not None else "NULL (旧数据)"
            chunk_count = row[1]
            index_range = f"{row[2]}-{row[3]}"
            print(f"{str(conv_id):<15} {chunk_count:<10} {index_range:<15}")

            if row[0] is None:
                null_conversation_chunks = chunk_count

        if null_conversation_chunks > 0:
            self.warnings.append(
                f"⚠️  发现 {null_conversation_chunks} 个未绑定对话的旧块 (conversation_id IS NULL)"
            )
            print(f"\n⚠️  发现 {null_conversation_chunks} 个旧块未绑定到任何对话")
            print("   这些块会在所有搜索中出现,可能导致污染!")

        conn.close()

    def analyze_documents(self):
        """分析文档记录"""
        print("\n" + "="*60)
        print("📄 分析用户文档记录")
        print("="*60)

        conn = sqlite3.connect(self.users_db_path)
        cursor = conn.cursor()

        # 获取用户ID
        cursor.execute("SELECT id FROM users WHERE username = ?", (self.username,))
        user_row = cursor.fetchone()
        if not user_row:
            print(f"❌ 用户不存在: {self.username}")
            conn.close()
            return

        user_id = user_row[0]
        print(f"用户ID: {user_id}")

        # 文档统计
        cursor.execute("""
            SELECT
                id, filename, conversation_id,
                datetime(uploaded_at, 'localtime') as upload_time
            FROM user_documents
            WHERE user_id = ?
            ORDER BY uploaded_at DESC
        """, (user_id,))

        docs = cursor.fetchall()

        if not docs:
            print("\n⚠️  该用户没有上传任何文档!")
            conn.close()
            return

        print(f"\n文档总数: {len(docs)}")
        print("\n最近上传的文档:")
        print(f"{'文档ID':<10} {'文件名':<30} {'对话ID':<15} {'上传时间':<20}")
        print("-" * 80)

        null_conversation_docs = 0
        for doc in docs[:10]:  # 只显示最近10个
            conv_id = doc[2] if doc[2] is not None else "NULL (未绑定)"
            print(f"{doc[0]:<10} {doc[1]:<30} {str(conv_id):<15} {doc[3]:<20}")

            if doc[2] is None:
                null_conversation_docs += 1

        if null_conversation_docs > 0:
            self.warnings.append(
                f"⚠️  发现 {null_conversation_docs} 个文档未绑定到对话"
            )

        conn.close()

    def test_search_query(self, conversation_id=None):
        """模拟搜索查询,检查SQL执行"""
        print("\n" + "="*60)
        print("🔍 模拟搜索查询")
        print("="*60)

        conn = sqlite3.connect(self.vector_db_path)
        cursor = conn.cursor()

        if conversation_id:
            print(f"\n搜索范围: 对话 #{conversation_id}")
            cursor.execute("""
                SELECT COUNT(*)
                FROM chunks
                WHERE conversation_id = ? OR conversation_id IS NULL
            """, (conversation_id,))
        else:
            print(f"\n搜索范围: 所有文档 (无会话过滤)")
            cursor.execute("SELECT COUNT(*) FROM chunks")

        count = cursor.fetchone()[0]
        print(f"可搜索的块数量: {count}")

        if count == 0:
            self.issues_found.append(
                f"❌ 对话 {conversation_id} 没有任何可搜索的文档块!"
            )
            print(f"❌ 该对话没有文档!")

        # 检查是否有 NULL conversation_id 的块
        cursor.execute("SELECT COUNT(*) FROM chunks WHERE conversation_id IS NULL")
        null_count = cursor.fetchone()[0]

        if null_count > 0:
            print(f"\n⚠️  警告: 发现 {null_count} 个未绑定对话的块")
            print(f"   这些块会在所有搜索中出现,可能是旧数据污染源!")

            # 显示未绑定块的来源文档
            cursor.execute("""
                SELECT DISTINCT d.filename
                FROM chunks c
                JOIN documents d ON c.document_id = d.id
                WHERE c.conversation_id IS NULL
                LIMIT 5
            """)

            print("\n   未绑定块的来源文档:")
            for row in cursor.fetchall():
                print(f"   - {row[0]}")

        conn.close()

    def check_embedding_cache(self):
        """检查嵌入缓存状态"""
        print("\n" + "="*60)
        print("💾 检查嵌入缓存")
        print("="*60)

        # 检查是否有嵌入缓存文件
        cache_patterns = [
            "embedding_cache.pkl",
            f"embedding_cache_{self.username}.pkl",
            ".embedding_cache"
        ]

        found_cache = False
        for pattern in cache_patterns:
            if os.path.exists(pattern):
                size = os.path.getsize(pattern) / 1024
                print(f"⚠️  发现缓存文件: {pattern} ({size:.2f} KB)")
                print(f"   缓存可能导致使用旧的嵌入向量!")
                found_cache = True

        if not found_cache:
            print("✅ 未发现嵌入缓存文件")

    def suggest_fixes(self):
        """建议修复方案"""
        print("\n" + "="*60)
        print("🛠️  修复建议")
        print("="*60)

        if not self.issues_found and not self.warnings:
            print("\n✅ 没有发现严重问题!")
            return

        if self.issues_found:
            print("\n❌ 严重问题:")
            for i, issue in enumerate(self.issues_found, 1):
                print(f"   {i}. {issue}")

        if self.warnings:
            print("\n⚠️  警告:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")

        print("\n" + "="*60)
        print("💡 建议的修复步骤:")
        print("="*60)

        # 根据问题提供针对性建议
        if any("缺少 conversation_id" in issue for issue in self.issues_found):
            print("\n1️⃣  运行数据库迁移:")
            print("   python migrate_session_isolation.py")

        if any("未绑定对话" in warning for warning in self.warnings):
            print("\n2️⃣  清理未绑定的旧数据:")
            print("   python cleanup_orphan_chunks.py")

        if any("向量数据库为空" in warning for warning in self.warnings):
            print("\n3️⃣  重新上传文档:")
            print("   - 创建新对话")
            print("   - 上传 PDF 文档")
            print("   - 验证文档是否正确处理")

        print("\n4️⃣  验证修复:")
        print("   python test_session_isolation.py")

    def run_full_diagnosis(self, conversation_id=None):
        """运行完整诊断"""
        print("\n" + "🔬"*30)
        print("向量数据库深度诊断工具")
        print("🔬"*30)
        print(f"\n用户: {self.username}")
        if conversation_id:
            print(f"对话ID: {conversation_id}")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if not self.check_db_exists():
            print("\n❌ 数据库文件缺失,无法继续诊断")
            return

        self.check_schema()
        self.analyze_chunks_distribution()
        self.analyze_documents()
        self.test_search_query(conversation_id)
        self.check_embedding_cache()
        self.suggest_fixes()

        # 生成诊断报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "username": self.username,
            "conversation_id": conversation_id,
            "issues": self.issues_found,
            "warnings": self.warnings
        }

        report_file = f"diagnosis_report_{self.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print("\n" + "="*60)
        print(f"📋 诊断报告已保存: {report_file}")
        print("="*60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python diagnose_vector_db.py <username> [conversation_id]")
        print("示例: python diagnose_vector_db.py tomyb")
        print("示例: python diagnose_vector_db.py tomyb 123")
        sys.exit(1)

    username = sys.argv[1]
    conversation_id = int(sys.argv[2]) if len(sys.argv) > 2 else None

    diagnostics = VectorDBDiagnostics(username)
    diagnostics.run_full_diagnosis(conversation_id)
