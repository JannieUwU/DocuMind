"""
清理孤立的文档块 (Orphan Chunks)

这些块没有绑定到任何对话 (conversation_id IS NULL),
会在所有搜索中出现,导致上下文污染。

使用方法:
    python cleanup_orphan_chunks.py <username> [--dry-run]

参数:
    username: username
    --dry-run: 仅显示将要删除的内容,不实际删除
"""
import sqlite3
import sys
import os
from datetime import datetime

class OrphanChunkCleaner:
    def __init__(self, username, dry_run=False):
        self.username = username
        self.vector_db_path = f"custom_rag_{username}.db"
        self.dry_run = dry_run

    def analyze_orphans(self):
        """分析孤立块"""
        print("\n" + "="*60)
        print("🔍 分析孤立的文档块")
        print("="*60)

        if not os.path.exists(self.vector_db_path):
            print(f"❌ 数据库不存在: {self.vector_db_path}")
            return None

        conn = sqlite3.connect(self.vector_db_path)
        cursor = conn.cursor()

        # 统计孤立块
        cursor.execute("""
            SELECT COUNT(*)
            FROM chunks
            WHERE conversation_id IS NULL
        """)
        orphan_count = cursor.fetchone()[0]

        if orphan_count == 0:
            print("✅ 没有发现孤立块!")
            conn.close()
            return 0

        print(f"\n发现 {orphan_count} 个孤立块 (conversation_id IS NULL)")

        # 获取孤立块的来源文档
        cursor.execute("""
            SELECT
                d.id,
                d.filename,
                COUNT(c.id) as chunk_count,
                MIN(datetime(d.created_at, 'localtime')) as created_time
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE c.conversation_id IS NULL
            GROUP BY d.id, d.filename
            ORDER BY d.created_at DESC
        """)

        orphan_docs = cursor.fetchall()

        print(f"\n这些块来自 {len(orphan_docs)} 个文档:")
        print(f"\n{'文档ID':<10} {'文件名':<40} {'块数':<10} {'创建时间':<20}")
        print("-" * 85)

        for doc in orphan_docs:
            print(f"{doc[0]:<10} {doc[1]:<40} {doc[2]:<10} {doc[3]:<20}")

        conn.close()
        return orphan_count

    def clean_orphans(self):
        """清理孤立块"""
        print("\n" + "="*60)
        if self.dry_run:
            print("🧪 模拟清理 (DRY RUN)")
        else:
            print("🧹 执行清理")
        print("="*60)

        conn = sqlite3.connect(self.vector_db_path)
        cursor = conn.cursor()

        try:
            # 获取将要删除的块ID
            cursor.execute("""
                SELECT id, document_id, chunk_index
                FROM chunks
                WHERE conversation_id IS NULL
                ORDER BY document_id, chunk_index
                LIMIT 10
            """)

            sample_chunks = cursor.fetchall()

            if sample_chunks:
                print("\n示例 - 将要删除的块 (前10个):")
                print(f"{'块ID':<10} {'文档ID':<10} {'块索引':<10}")
                print("-" * 35)
                for chunk in sample_chunks:
                    print(f"{chunk[0]:<10} {chunk[1]:<10} {chunk[2]:<10}")

            if self.dry_run:
                print("\n⚠️  DRY RUN 模式 - 未实际删除任何数据")
                print("   移除 --dry-run 参数来执行实际清理")
            else:
                # 实际删除
                print("\n⚠️  即将删除所有孤立块...")
                response = input("确认删除? (yes/no): ")

                if response.lower() != 'yes':
                    print("❌ 已取消")
                    conn.close()
                    return

                cursor.execute("""
                    DELETE FROM chunks
                    WHERE conversation_id IS NULL
                """)

                deleted_count = cursor.rowcount
                conn.commit()

                print(f"\n✅ 已删除 {deleted_count} 个孤立块")

                # 清理没有块的文档
                cursor.execute("""
                    DELETE FROM documents
                    WHERE id NOT IN (SELECT DISTINCT document_id FROM chunks)
                """)

                deleted_docs = cursor.rowcount
                conn.commit()

                if deleted_docs > 0:
                    print(f"✅ cleaned {deleted_docs} 个空文档记录")

                # VACUUM 优化数据库
                print("\n🔧 优化数据库...")
                cursor.execute("VACUUM")
                conn.commit()

                # 显示清理后的统计
                cursor.execute("SELECT COUNT(*) FROM chunks")
                remaining_chunks = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM documents")
                remaining_docs = cursor.fetchone()[0]

                print(f"\n📊 清理后统计:")
                print(f"   剩余块数: {remaining_chunks}")
                print(f"   剩余文档: {remaining_docs}")

        except Exception as e:
            conn.rollback()
            print(f"\n❌ 清理失败: {e}")
            raise
        finally:
            conn.close()

    def backup_database(self):
        """备份数据库"""
        if self.dry_run:
            return

        backup_path = f"{self.vector_db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"\n💾 创建备份: {backup_path}")

        import shutil
        shutil.copy2(self.vector_db_path, backup_path)
        print(f"✅ 备份完成")

    def run(self):
        """执行清理流程"""
        print("\n" + "🧹"*30)
        print("孤立块清理工具")
        print("🧹"*30)
        print(f"\n用户: {self.username}")
        print(f"模式: {'DRY RUN (模拟)' if self.dry_run else 'ACTUAL (实际清理)'}")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        orphan_count = self.analyze_orphans()

        if orphan_count is None or orphan_count == 0:
            return

        if not self.dry_run:
            self.backup_database()

        self.clean_orphans()

        print("\n" + "="*60)
        print("✅ 清理完成!")
        print("="*60)
        print("\n建议下一步:")
        print("1. 运行诊断工具验证: python diagnose_vector_db.py", self.username)
        print("2. 测试搜索Features是否正常")
        print("3. 如有问题,可从备份恢复")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python cleanup_orphan_chunks.py <username> [--dry-run]")
        print("\n示例:")
        print("  python cleanup_orphan_chunks.py tomyb --dry-run  # 模拟运行")
        print("  python cleanup_orphan_chunks.py tomyb            # 实际清理")
        sys.exit(1)

    username = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    cleaner = OrphanChunkCleaner(username, dry_run)
    cleaner.run()
