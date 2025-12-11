"""
构建学术术语数据库
从DomainWordsDict导入10万+术语到SQLite数据库

数据库设计:
- academic_terms 表: 存储所有术语
  - id: 主键
  - term: 术语名称 (索引)
  - category: 所属领域
  - weight: 权重分数
  - definition: 定义
  - domain: 原始领域名称
"""

import os
import sqlite3
from typing import List, Tuple
from collections import defaultdict

# DomainWordsDict路径
DOMAIN_DICT_PATH = r"C:\Users\tomyb\Downloads\DomainWordsDict-master\DomainWordsDict-master\data"

# 数据库文件路径
DATABASE_PATH = r"C:\Users\tomyb\Desktop\vue3-rag-frontend2\backend\academic_terms.db"

# 所有68个领域的映射
ALL_DOMAINS = {
    '计算机业': 'computer_science',
    '网络游戏': 'gaming',
    '电子工程': 'electronics',
    '通信工程': 'communication',
    '化学化工': 'chemistry',
    '物理科学': 'physics',
    '数学科学': 'mathematics',
    '医药医学': 'medicine',
    '人力招聘': 'recruitment',
    '天文科学': 'astronomy',
    '餐饮食品': 'food',
    '外语学习': 'language',
    '电影影视': 'film',
    '环境科学': 'environment',
    '钢铁冶金': 'metallurgy',
    '印刷印染': 'printing',
    '美容美发': 'beauty',
    '法律诉讼': 'law',
    '水利工程': 'hydraulic',
    '手机数码': 'mobile',
    '音乐歌曲': 'music',
    '地产开发': 'realestate',
    '汉语言学': 'linguistics',
    '网络文学': 'literature',
    '休闲活动': 'leisure',
    '交通运输': 'transport',
    '矿业勘探': 'mining',
    '地点名称': 'location',
    '船舶工程': 'ship',
    '敏感用词': 'sensitive',
    '旅游交通': 'tourism',
    '机械工程': 'mechanical',
    '考古挖掘': 'archaeology',
    '人文政治': 'politics',
    '电力电气': 'power',
    '纺织服装': 'textile',
    '办公文教': 'office',
    '组织机构': 'organization',
    '诗词歌赋': 'poetry',
    '社会科学': 'social',
    '军事情报': 'military',
    '农林牧渔': 'agriculture',
    '文学名著': 'classic',
    '新番动漫': 'anime',
    '网络用语': 'internet',
    '市场购物': 'shopping',
    '金融财经': 'finance',
    '古代历史': 'history',
    '世界哲学': 'philosophy',
    '人物名称': 'person',
    '世界宗教': 'religion',
    '地理测绘': 'geography',
    '民间习俗': 'folklore',
    '书法艺术': 'calligraphy',
    '期货期权': 'futures',
    '土木工程': 'civil',
    '安全工程': 'safety',
    '材料包装': 'material',
    '教育教学': 'education',
    '家居装饰': 'home',
    '工业设计': 'design',
    '体育运动': 'sports',
    '航空航天': 'aerospace',
    '建筑装潢': 'architecture',
    '广告传媒': 'media',
    '汽车行业': 'automobile',
    '管理科学': 'management',
    '动植生物': 'biology',
}

# 最小权重阈值
MIN_WEIGHT = 5  # 降低阈值以获取更多术语

# 每个领域最大术语数
MAX_TERMS_PER_DOMAIN = 2000  # 68个领域 * 2000 = 最多136,000术语


def create_database():
    """创建数据库和表结构"""
    print("[*] 创建数据库...")

    # 删除旧数据库
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
        print(f"[*] 删除旧数据库: {DATABASE_PATH}")

    # 创建连接
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # 创建术语表
    cursor.execute('''
        CREATE TABLE academic_terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT NOT NULL,
            category TEXT NOT NULL,
            weight INTEGER NOT NULL,
            definition TEXT,
            domain TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 创建索引以加速查询
    cursor.execute('CREATE INDEX idx_term ON academic_terms(term)')
    cursor.execute('CREATE INDEX idx_category ON academic_terms(category)')
    cursor.execute('CREATE INDEX idx_weight ON academic_terms(weight DESC)')
    cursor.execute('CREATE INDEX idx_domain ON academic_terms(domain)')

    conn.commit()
    conn.close()

    print("[OK] 数据库创建成功!")
    print(f"[*] 数据库路径: {DATABASE_PATH}")


def load_domain_terms(domain_name: str, min_weight: int = MIN_WEIGHT) -> List[Tuple[str, int]]:
    """
    加载指定领域的术语

    Args:
        domain_name: 领域名称
        min_weight: 最小权重

    Returns:
        List of (term, weight) tuples
    """
    file_path = os.path.join(DOMAIN_DICT_PATH, f"{domain_name}.txt")

    if not os.path.exists(file_path):
        print(f"[!] 文件不存在: {domain_name}.txt")
        return []

    terms = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                parts = line.split('\t')
                if len(parts) != 2:
                    continue

                term, weight_str = parts[0], parts[1]
                try:
                    weight = int(weight_str)
                except ValueError:
                    continue

                # 只保留满足权重要求的术语
                if weight >= min_weight:
                    terms.append((term, weight))

                # 限制每个领域的术语数
                if len(terms) >= MAX_TERMS_PER_DOMAIN:
                    break

    except Exception as e:
        print(f"[!] 读取失败 {domain_name}: {e}")
        return []

    return terms


def filter_term(term: str) -> bool:
    """
    过滤无效术语

    规则:
    1. 长度在2-20之间
    2. 不是纯数字
    3. 不包含过多特殊字符
    """
    # 长度检查
    if len(term) < 2 or len(term) > 20:
        return False

    # 纯数字过滤
    if term.isdigit():
        return False

    # 特殊字符检查
    special_count = sum(1 for c in term if not c.isalnum() and c not in ['-', '_', '.', '/', '+', '·'])
    if special_count > 3:
        return False

    return True


def generate_definition(term: str, category: str, domain: str) -> str:
    """生成术语定义"""
    # 简化定义生成
    category_names = {
        'computer_science': '计算机科学',
        'gaming': '网络游戏',
        'electronics': '电子工程',
        'communication': '通信工程',
        'chemistry': '化学',
        'physics': '物理学',
        'mathematics': '数学',
        'medicine': '医学',
        'recruitment': '人力资源',
        'astronomy': '天文学',
        'food': '餐饮食品',
        'language': '外语',
        'film': '影视',
        'environment': '环境科学',
        'metallurgy': '冶金',
        'printing': '印刷',
        'beauty': '美容',
        'law': '法律',
        'hydraulic': '水利',
        'mobile': '数码',
        'music': '音乐',
        'realestate': '地产',
        'linguistics': '语言学',
        'literature': '文学',
        'leisure': '休闲',
        'transport': '交通',
        'mining': '矿业',
        'location': '地理',
        'ship': '船舶',
        'tourism': '旅游',
        'mechanical': '机械',
        'archaeology': '考古',
        'politics': '政治',
        'power': '电力',
        'textile': '纺织',
        'office': '办公',
        'organization': '组织',
        'poetry': '诗词',
        'social': '社会科学',
        'military': '军事',
        'agriculture': '农业',
        'classic': '文学',
        'anime': '动漫',
        'internet': '网络',
        'shopping': '购物',
        'finance': '金融',
        'history': '历史',
        'philosophy': '哲学',
        'person': '人物',
        'religion': '宗教',
        'geography': '地理',
        'folklore': '民俗',
        'calligraphy': '书法',
        'futures': '期货',
        'civil': '土木',
        'safety': '安全',
        'material': '材料',
        'education': '教育',
        'home': '家居',
        'design': '设计',
        'sports': '体育',
        'aerospace': '航空航天',
        'architecture': '建筑',
        'media': '传媒',
        'automobile': '汽车',
        'management': '管理',
        'biology': '生物',
    }

    cat_name = category_names.get(category, category)
    return f'{term}是{cat_name}领域的专业术语'


def import_all_domains():
    """导入所有领域的术语到数据库"""
    print("\n" + "="*70)
    print("开始导入术语到数据库")
    print("="*70)

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    total_imported = 0
    stats = defaultdict(int)

    for i, (domain_name, category) in enumerate(ALL_DOMAINS.items(), 1):
        print(f"\n[{i}/68] 处理: {domain_name} ({category})")

        # 加载术语
        terms = load_domain_terms(domain_name, min_weight=MIN_WEIGHT)
        print(f"   加载了 {len(terms)} 个术语 (权重>={MIN_WEIGHT})")

        if not terms:
            print(f"   [!] 跳过空领域")
            continue

        # 过滤并插入数据库
        imported_count = 0
        for term, weight in terms:
            if not filter_term(term):
                continue

            definition = generate_definition(term, category, domain_name)

            try:
                cursor.execute('''
                    INSERT INTO academic_terms (term, category, weight, definition, domain)
                    VALUES (?, ?, ?, ?, ?)
                ''', (term, category, weight, definition, domain_name))
                imported_count += 1
            except sqlite3.IntegrityError:
                # 重复术语跳过
                pass

        stats[category] = imported_count
        total_imported += imported_count

        print(f"   [OK] 导入 {imported_count} 个术语")

        # 每处理10个领域提交一次
        if i % 10 == 0:
            conn.commit()
            print(f"\n[*] 已提交 {i}/68 个领域, 共 {total_imported} 个术语")

    # 最终提交
    conn.commit()
    conn.close()

    # 打印统计
    print("\n" + "="*70)
    print("导入统计")
    print("="*70)

    for category, count in sorted(stats.items(), key=lambda x: x[1], reverse=True)[:20]:
        print(f"{category:20} : {count:6} 个术语")

    print(f"\n[OK] 总计导入: {total_imported:,} 个术语")
    print(f"[OK] 数据库大小: {os.path.getsize(DATABASE_PATH) / 1024 / 1024:.2f} MB")


def verify_database():
    """验证数据库内容"""
    print("\n" + "="*70)
    print("数据库验证")
    print("="*70)

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # 总术语数
    cursor.execute('SELECT COUNT(*) FROM academic_terms')
    total = cursor.fetchone()[0]
    print(f"\n[*] 总术语数: {total:,}")

    # 按类别统计
    cursor.execute('''
        SELECT category, COUNT(*) as cnt
        FROM academic_terms
        GROUP BY category
        ORDER BY cnt DESC
        LIMIT 10
    ''')
    print("\n[*] TOP 10 类别:")
    for category, count in cursor.fetchall():
        print(f"   {category:20} : {count:6} 个术语")

    # 高权重术语示例
    cursor.execute('''
        SELECT term, category, weight
        FROM academic_terms
        ORDER BY weight DESC
        LIMIT 20
    ''')
    print("\n[*] 高权重术语示例 (TOP 20):")
    for i, (term, category, weight) in enumerate(cursor.fetchall(), 1):
        print(f"   {i:2}. {term:30} ({category:15}, 权重:{weight})")

    conn.close()


def main():
    """主函数"""
    print("="*70)
    print("学术术语数据库构建工具")
    print("从DomainWordsDict导入10万+术语")
    print("="*70)

    # 步骤1: 创建数据库
    create_database()

    # 步骤2: 导入所有领域
    import_all_domains()

    # 步骤3: 验证数据库
    verify_database()

    print("\n" + "="*70)
    print("[OK] 数据库构建完成!")
    print(f"[*] 数据库路径: {DATABASE_PATH}")
    print("="*70)


if __name__ == '__main__':
    main()
