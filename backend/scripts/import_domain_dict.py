"""
导入DomainWordsDict词典到学术术语提取系统

从916万词的DomainWordsDict中提取技术相关领域的高权重术语,
转换为我们的知识库格式,大幅扩展术语覆盖范围。
"""

import os
from typing import Dict, List, Tuple
from collections import defaultdict

# DomainWordsDict路径
DOMAIN_DICT_PATH = r"C:\Users\tomyb\Downloads\DomainWordsDict-master\DomainWordsDict-master\data"

# 我们关注的技术领域及其映射
TECH_DOMAINS = {
    '计算机业': 'computer_science',
    '网络游戏': 'gaming',  # 包含技术术语
    '电子工程': 'electronics',
    '通信工程': 'communication',
    '化学化工': 'chemistry',
    '物理科学': 'physics',
    '数学科学': 'mathematics',
    '医药医学': 'medicine',
}

# 最小权重阈值 (只提取高权重词汇)
MIN_WEIGHT_THRESHOLD = 10


def load_domain_dict(domain_name: str, min_weight: int = 10) -> List[Tuple[str, int]]:
    """
    加载指定领域的词典

    Args:
        domain_name: 领域名称 (如"计算机业")
        min_weight: 最小权重阈值

    Returns:
        List of (term, weight) tuples
    """
    file_path = os.path.join(DOMAIN_DICT_PATH, f"{domain_name}.txt")

    if not os.path.exists(file_path):
        print(f"[!] 文件不存在: {file_path}")
        return []

    terms = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split('\t')
            if len(parts) != 2:
                continue

            term, weight = parts[0], int(parts[1])

            # 只保留高权重术语
            if weight >= min_weight:
                terms.append((term, weight))

    return terms


def filter_tech_terms(terms: List[Tuple[str, int]]) -> List[Tuple[str, int]]:
    """
    过滤技术相关术语

    过滤规则:
    1. 长度2-15字符
    2. 不包含特殊字符
    3. 不是纯数字
    4. 不是无意义词
    """
    filtered = []

    # 无意义词列表
    stopwords = {
        '的', '了', '和', '是', '在', '有', '与', '等', '及', '或',
        '用', '为', '以', '对', '于', '由', '从', '到', '将', '被'
    }

    for term, weight in terms:
        # 1. 长度检查
        if len(term) < 2 or len(term) > 15:
            continue

        # 2. 跳过纯数字
        if term.isdigit():
            continue

        # 3. 跳过停用词
        if term in stopwords:
            continue

        # 4. 跳过包含过多特殊字符的
        special_char_count = sum(1 for c in term if not c.isalnum() and c not in ['-', '_', '.', '/', '+'])
        if special_char_count > 2:
            continue

        filtered.append((term, weight))

    return filtered


def categorize_terms(domain_name: str) -> str:
    """
    根据领域名称返回术语分类
    """
    category_map = {
        '计算机业': '计算机科学',
        '网络游戏': '网络技术',
        '电子工程': '电子工程',
        '通信工程': '通信工程',
        '化学化工': '化学',
        '物理科学': '物理',
        '数学科学': '数学',
        '医药医学': '医学',
    }
    return category_map.get(domain_name, '专业术语')


def generate_definition(term: str, category: str) -> str:
    """
    为术语生成定义
    """
    # 简单规则生成定义
    if '算法' in term:
        return f'{term}是一种计算算法或技术方法'
    elif any(x in term for x in ['网络', 'Net', 'net']):
        return f'{term}是一种网络技术或架构'
    elif any(x in term for x in ['数据', 'Data', 'data']):
        return f'{term}是数据处理或存储相关的技术概念'
    elif any(x in term for x in ['系统', 'System', 'system']):
        return f'{term}是一种系统架构或技术体系'
    else:
        return f'{term}是{category}领域的专业术语'


def main():
    """主函数"""
    print("="*70)
    print("DomainWordsDict 词典导入工具")
    print("="*70)

    all_tech_terms = defaultdict(list)
    total_terms = 0

    # 遍历所有技术领域
    for domain_name in TECH_DOMAINS.keys():
        print(f"\n[*] 处理领域: {domain_name}")

        # 加载词典
        terms = load_domain_dict(domain_name, min_weight=MIN_WEIGHT_THRESHOLD)
        print(f"   加载了 {len(terms)} 个高权重术语 (权重>={MIN_WEIGHT_THRESHOLD})")

        # 过滤技术术语
        filtered = filter_tech_terms(terms)
        print(f"   过滤后剩余 {len(filtered)} 个技术术语")

        # 分类
        category = categorize_terms(domain_name)

        # 存储
        for term, weight in filtered[:500]:  # 每个领域最多取500个
            all_tech_terms[category].append({
                'term': term,
                'weight': weight,
                'category': category,
                'definition': generate_definition(term, category)
            })

        total_terms += min(len(filtered), 500)

    # 输出统计
    print("\n" + "="*70)
    print("导入统计")
    print("="*70)

    for category, terms in sorted(all_tech_terms.items()):
        print(f"[*] {category}: {len(terms)} 个术语")

    print(f"\n[OK] 总计提取: {total_terms} 个高质量技术术语")

    # 生成Python代码格式的知识库
    print("\n" + "="*70)
    print("生成知识库代码")
    print("="*70)

    output_file = "domain_knowledge_base.py"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('"""\n')
        f.write('从DomainWordsDict提取的技术领域知识库\n')
        f.write(f'总计 {total_terms} 个高质量技术术语\n')
        f.write('"""\n\n')
        f.write('DOMAIN_KNOWLEDGE_BASE = {\n')

        for category in sorted(all_tech_terms.keys()):
            terms = all_tech_terms[category]

            # 按权重排序
            terms_sorted = sorted(terms, key=lambda x: x['weight'], reverse=True)

            for term_info in terms_sorted[:100]:  # 每个类别最多输出100个
                term = term_info['term']
                definition = term_info['definition']
                category = term_info['category']

                # 转义特殊字符
                term_escaped = term.replace("'", "\\'")
                definition_escaped = definition.replace("'", "\\'")

                f.write(f"    '{term_escaped}': {{\n")
                f.write(f"        'category': '{category}',\n")
                f.write(f"        'definition': '{definition_escaped}',\n")
                f.write(f"        'keywords': []\n")
                f.write(f"    }},\n")

        f.write('}\n')

    print(f"[OK] 已生成: {output_file}")
    print(f"   包含最高权重的术语")

    # 显示示例
    print("\n" + "="*70)
    print("示例术语 (计算机科学领域前20个)")
    print("="*70)

    if '计算机科学' in all_tech_terms:
        computer_terms = sorted(all_tech_terms['计算机科学'], key=lambda x: x['weight'], reverse=True)
        for i, term_info in enumerate(computer_terms[:20], 1):
            print(f"{i:2}. {term_info['term']:20} (权重: {term_info['weight']})")


if __name__ == '__main__':
    main()
