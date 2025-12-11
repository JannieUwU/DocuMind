"""
学术术语数据库查询接口
提供高效的术语查询和匹配Features
"""

import sqlite3
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# 数据库路径
DATABASE_PATH = Path(__file__).parent / "academic_terms.db"


class TermDatabase:
    """术语数据库查询类"""

    def __init__(self, db_path: str = None):
        """
        initialized数据库连接

        Args:
            db_path: 数据库文件路径,default使用academic_terms.db
        """
        self.db_path = db_path or str(DATABASE_PATH)
        self._conn = None

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

    def connect(self):
        """建立数据库连接"""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row  # 返回字典格式
        return self._conn

    def close(self):
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._conn = None

    def search_exact(self, term: str) -> Optional[Dict]:
        """
        精确搜索术语

        Args:
            term: 术语名称

        Returns:
            术语信息字典或None
        """
        cursor = self._conn.cursor()
        cursor.execute('''
            SELECT term, category, weight, definition, domain
            FROM academic_terms
            WHERE term = ?
            ORDER BY weight DESC
            LIMIT 1
        ''', (term,))

        row = cursor.fetchone()
        if row:
            return {
                'term': row['term'],
                'category': row['category'],
                'weight': row['weight'],
                'definition': row['definition'],
                'domain': row['domain']
            }
        return None

    def search_fuzzy(self, term: str, limit: int = 10) -> List[Dict]:
        """
        模糊搜索术语

        Args:
            term: 术语名称(支持模糊匹配)
            limit: 返回结果数量限制

        Returns:
            术语信息列表
        """
        cursor = self._conn.cursor()
        cursor.execute('''
            SELECT term, category, weight, definition, domain
            FROM academic_terms
            WHERE term LIKE ?
            ORDER BY weight DESC
            LIMIT ?
        ''', (f'%{term}%', limit))

        results = []
        for row in cursor.fetchall():
            results.append({
                'term': row['term'],
                'category': row['category'],
                'weight': row['weight'],
                'definition': row['definition'],
                'domain': row['domain']
            })
        return results

    def search_by_category(self, category: str, limit: int = 100) -> List[Dict]:
        """
        按类别搜索术语

        Args:
            category: 类别名称
            limit: 返回结果数量限制

        Returns:
            术语信息列表
        """
        cursor = self._conn.cursor()
        cursor.execute('''
            SELECT term, category, weight, definition, domain
            FROM academic_terms
            WHERE category = ?
            ORDER BY weight DESC
            LIMIT ?
        ''', (category, limit))

        results = []
        for row in cursor.fetchall():
            results.append({
                'term': row['term'],
                'category': row['category'],
                'weight': row['weight'],
                'definition': row['definition'],
                'domain': row['domain']
            })
        return results

    def batch_search(self, terms: List[str]) -> Dict[str, Dict]:
        """
        批量搜索术语

        Args:
            terms: 术语名称列表

        Returns:
            {term: info} 字典
        """
        if not terms:
            return {}

        cursor = self._conn.cursor()

        # 构建IN查询
        placeholders = ','.join('?' * len(terms))
        cursor.execute(f'''
            SELECT term, category, weight, definition, domain
            FROM academic_terms
            WHERE term IN ({placeholders})
        ''', terms)

        results = {}
        for row in cursor.fetchall():
            term = row['term']
            results[term] = {
                'term': term,
                'category': row['category'],
                'weight': row['weight'],
                'definition': row['definition'],
                'domain': row['domain']
            }

        return results

    def get_high_weight_terms(self, min_weight: int = 50, limit: int = 1000) -> List[Dict]:
        """
        获取高权重术语

        Args:
            min_weight: 最小权重
            limit: 返回结果数量限制

        Returns:
            术语信息列表
        """
        cursor = self._conn.cursor()
        cursor.execute('''
            SELECT term, category, weight, definition, domain
            FROM academic_terms
            WHERE weight >= ?
            ORDER BY weight DESC
            LIMIT ?
        ''', (min_weight, limit))

        results = []
        for row in cursor.fetchall():
            results.append({
                'term': row['term'],
                'category': row['category'],
                'weight': row['weight'],
                'definition': row['definition'],
                'domain': row['domain']
            })
        return results

    def get_statistics(self) -> Dict:
        """
        获取数据库statistics

        Returns:
            statistics字典
        """
        cursor = self._conn.cursor()

        # 总术语数
        cursor.execute('SELECT COUNT(*) as total FROM academic_terms')
        total = cursor.fetchone()['total']

        # 按类别统计
        cursor.execute('''
            SELECT category, COUNT(*) as count
            FROM academic_terms
            GROUP BY category
            ORDER BY count DESC
        ''')
        categories = {row['category']: row['count'] for row in cursor.fetchall()}

        # 权重分布
        cursor.execute('''
            SELECT
                AVG(weight) as avg_weight,
                MAX(weight) as max_weight,
                MIN(weight) as min_weight
            FROM academic_terms
        ''')
        weight_stats = cursor.fetchone()

        return {
            'total_terms': total,
            'categories': categories,
            'avg_weight': weight_stats['avg_weight'],
            'max_weight': weight_stats['max_weight'],
            'min_weight': weight_stats['min_weight']
        }

    def search_in_text(self, text: str, min_weight: int = 10) -> List[Dict]:
        """
        在文本中查找匹配的术语

        Args:
            text: 输入文本
            min_weight: 最小权重阈值

        Returns:
            匹配的术语列表
        """
        # 策略: 使用全文检索或遍历术语
        # 为了性能,我们采用分词+批量查询的方式

        # 简单分词(实际可以用jieba等工具)
        # 这里我们提取所有可能的2-10字片段
        candidates = set()
        text_len = len(text)

        for length in range(2, min(11, text_len + 1)):
            for i in range(text_len - length + 1):
                fragment = text[i:i + length]
                # 过滤纯标点/空格
                if fragment.strip() and not all(not c.isalnum() for c in fragment):
                    candidates.add(fragment)

        # 批量查询
        if not candidates:
            return []

        cursor = self._conn.cursor()
        placeholders = ','.join('?' * len(candidates))
        cursor.execute(f'''
            SELECT term, category, weight, definition, domain
            FROM academic_terms
            WHERE term IN ({placeholders})
            AND weight >= ?
            ORDER BY weight DESC
        ''', list(candidates) + [min_weight])

        results = []
        for row in cursor.fetchall():
            results.append({
                'term': row['term'],
                'category': row['category'],
                'weight': row['weight'],
                'definition': row['definition'],
                'domain': row['domain']
            })

        return results


# global singleton instance
_db_instance = None


def get_database() -> TermDatabase:
    """
    获取全局数据库实例

    Returns:
        TermDatabase实例
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = TermDatabase()
        _db_instance.connect()
    return _db_instance


def search_term(term: str) -> Optional[Dict]:
    """
    搜索术语(便捷函数)

    Args:
        term: 术语名称

    Returns:
        术语信息或None
    """
    db = get_database()
    return db.search_exact(term)


def search_terms_in_text(text: str, min_weight: int = 10) -> List[Dict]:
    """
    在文本中查找术语(便捷函数)

    Args:
        text: 输入文本
        min_weight: 最小权重

    Returns:
        匹配的术语列表
    """
    db = get_database()
    return db.search_in_text(text, min_weight)


# 测试代码
if __name__ == '__main__':
    print("="*70)
    print("术语数据库查询接口测试")
    print("="*70)

    with TermDatabase() as db:
        # 测试1: Get statistics
        print("\n[测试1] 数据库统计:")
        stats = db.get_statistics()
        print(f"  总术语数: {stats['total_terms']:,}")
        print(f"  类别数: {len(stats['categories'])}")
        print(f"  平均权重: {stats['avg_weight']:.2f}")
        print(f"  最大权重: {stats['max_weight']}")

        # 测试2: 精确搜索
        print("\n[测试2] 精确搜索:")
        test_terms = ['string', '排序', '神经网络', 'TensorFlow']
        for term in test_terms:
            result = db.search_exact(term)
            if result:
                print(f"  {term}: {result['definition']} (权重:{result['weight']})")
            else:
                print(f"  {term}: 未找到")

        # 测试3: 模糊搜索
        print("\n[测试3] 模糊搜索 '学习':")
        results = db.search_fuzzy('学习', limit=5)
        for i, r in enumerate(results, 1):
            print(f"  {i}. {r['term']} ({r['category']}, 权重:{r['weight']})")

        # 测试4: 按类别搜索
        print("\n[测试4] 计算机科学类别 (TOP 10):")
        results = db.search_by_category('computer_science', limit=10)
        for i, r in enumerate(results, 1):
            print(f"  {i}. {r['term']} (权重:{r['weight']})")

        # 测试5: 文本中查找术语
        print("\n[测试5] 文本中查找术语:")
        test_text = "深度学习使用TensorFlow框架进行神经网络训练"
        results = db.search_in_text(test_text, min_weight=5)
        print(f"  在文本中找到 {len(results)} 个术语:")
        for r in results[:10]:
            print(f"    - {r['term']} ({r['category']}, 权重:{r['weight']})")

    print("\n" + "="*70)
    print("[OK] 测试完成!")
