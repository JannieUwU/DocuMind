"""
Intelligent Title Generator
智能标题生成模块 - 生成高质量、具有具体性和区分度的对话标题

设计理念：
- 拒绝笼统词汇和空泛标题
- 准确反映对话核心价值
- 具有高信息密度
- 帮助用户快速识别和回忆对话内容
"""

import re
from typing import Dict, List, Tuple, Optional


class IntelligentTitleGenerator:
    """智能标题生成器"""

    # 禁止使用的笼统词汇
    # 注意: "用户"在技术上下文中(如"用户认证"、"用户管理")是允许的,只禁止单独使用
    FORBIDDEN_WORDS = {
        "文档", "讨论", "分析", "问题", "咨询", "对话", "聊天",
        "文件", "内容", "帮助", "关于", "有关", "一些", "某个",
        "客户", "情况", "事情", "东西", "方面", "部分"
    }

    # 无意义的开头词（用于fallback时过滤）
    # 注意：按长度降序排列，优先匹配较长的前缀
    MEANINGLESS_PREFIXES = [
        "我想咨询一下", "请问一下", "想问一下", "咨询一下",
        "帮我看看", "帮我查查", "能否帮忙",
        "你好", "请问", "帮我", "能否", "可以", "想要", "我想",
        "麻烦", "请帮", "帮忙", "请教", "咨询", "问一下", "想问", "一下"
    ]

    # 对话类型识别关键词
    CONVERSATION_TYPES = {
        "技术开发": {
            "keywords": [
                "代码", "编程", "开发", "bug", "调试", "函数", "类", "接口",
                "API", "数据库", "算法", "架构", "框架", "库", "组件",
                "Python", "Java", "JavaScript", "React", "Vue", "Django",
                "SQL", "MongoDB", "Redis", "Git", "Docker", "Kubernetes",
                "实现", "实例", "方法", "函数", "class", "def", "import"
            ],
            "pattern": "[技术名称]+[核心操作]",
            "value_keywords": ["优化", "重构", "实现", "设计", "开发", "构建"]
        },
        "商业分析": {
            "keywords": [
                "数据", "分析", "报表", "财务", "市场", "销售", "用户",
                "增长", "转化", "ROI", "KPI", "策略", "运营", "营销",
                "竞品", "定价", "成本", "利润", "投资", "融资",
                "趋势", "洞察", "模型", "预测"
            ],
            "pattern": "[具体对象]+[分析类型]",
            "value_keywords": ["趋势", "洞察", "策略", "模型", "预测", "方案"]
        },
        "内容创作": {
            "keywords": [
                "写", "撰写", "创作", "设计", "文案", "邮件", "报告",
                "方案", "提案", "演讲", "PPT", "文章", "博客", "视频",
                "UI", "品牌", "Logo", "海报", "广告"
            ],
            "pattern": "[内容主题]+[创作形式]",
            "value_keywords": ["撰写", "设计", "创作", "制作", "编写"]
        },
        "学习咨询": {
            "keywords": [
                "学习", "教程", "原理", "概念", "理解", "解释", "入门",
                "基础", "进阶", "掌握", "区别", "对比", "优缺点", "最佳实践",
                "是什么", "怎么", "如何", "为什么"
            ],
            "pattern": "[核心概念]+[知识类型]",
            "value_keywords": ["原理", "机制", "指南", "教程", "实践"]
        },
        "问题解决": {
            "keywords": [
                "优化", "改进", "解决", "修复", "提升", "加速", "降低",
                "性能", "速度", "效率", "质量", "稳定性", "安全",
                "慢", "卡", "报错", "失败", "异常"
            ],
            "pattern": "[具体对象]+[解决方案]",
            "value_keywords": ["优化", "修复", "改进", "提升", "解决"]
        }
    }

    @classmethod
    def analyze_conversation_semantics(cls, user_question: str, ai_response: str) -> Dict:
        """
        分析对话的语义信息

        Args:
            user_question: 用户问题
            ai_response: AI回复

        Returns:
            Dict: 语义分析结果，包含对话类型、关键实体、核心价值等
        """
        combined_text = user_question + " " + ai_response

        # 识别对话类型
        conversation_type = "通用"
        max_score = 0
        type_scores = {}

        for type_name, type_info in cls.CONVERSATION_TYPES.items():
            score = sum(1 for keyword in type_info["keywords"] if keyword.lower() in combined_text.lower())
            type_scores[type_name] = score
            if score > max_score:
                max_score = score
                conversation_type = type_name

        # 提取技术实体（专有名词、技术栈）
        tech_entities = []
        tech_patterns = [
            r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)*)\b',  # 驼峰命名（如：React、JavaScript）
            r'\b([A-Z]{2,})\b',  # 全大写缩写（如：API、SQL、UI）
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)',  # 两个大写开头的词（如：Machine Learning）
        ]

        for pattern in tech_patterns:
            matches = re.findall(pattern, combined_text)
            tech_entities.extend(matches)

        # 去重并过滤常见词
        common_words = {'The', 'This', 'That', 'What', 'How', 'Why', 'When', 'Where', 'AI', 'I', 'You'}
        tech_entities = list(set([e for e in tech_entities if e not in common_words and len(e) > 2]))

        # 提取中文技术术语
        chinese_tech_terms = []
        tech_term_pattern = r'([\u4e00-\u9fa5]{2,6})(系统|架构|框架|平台|模块|组件|服务|引擎|工具|算法|模型|机制|协议|策略)'
        chinese_matches = re.findall(tech_term_pattern, combined_text)
        chinese_tech_terms = [m[0] + m[1] for m in chinese_matches]

        # 提取核心价值动词
        value_keywords = []
        if conversation_type in cls.CONVERSATION_TYPES:
            value_words = cls.CONVERSATION_TYPES[conversation_type]["value_keywords"]
            value_keywords = [w for w in value_words if w in combined_text]

        return {
            "conversation_type": conversation_type,
            "type_confidence": max_score,
            "type_scores": type_scores,
            "tech_entities": tech_entities[:5],  # 最多保留5个
            "chinese_tech_terms": chinese_tech_terms[:5],
            "value_keywords": value_keywords[:3],  # 最多保留3个价值关键词
            "has_specific_tech": len(tech_entities) > 0 or len(chinese_tech_terms) > 0
        }

    @classmethod
    def extract_ai_value_points(cls, ai_response: str) -> Dict:
        """
        从AI回复中提取核心价值点

        Args:
            ai_response: AI的完整回复

        Returns:
            Dict: AI价值点分析，包含解决方案、关键概念、技术栈等
        """
        # 提取技术栈提及
        tech_stack = []
        tech_keywords = [
            'Django', 'React', 'Vue', 'Python', 'Java', 'JavaScript', 'TypeScript',
            'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Docker', 'Kubernetes',
            'AWS', 'Azure', 'GCP', 'Git', 'Node', 'Express', 'Flask', 'FastAPI'
        ]
        for tech in tech_keywords:
            if tech.lower() in ai_response.lower():
                tech_stack.append(tech)

        # 识别解决方案类型
        solution_patterns = {
            "性能优化": ["优化", "性能", "提升", "加速", "缓存", "索引"],
            "架构设计": ["架构", "设计", "模式", "解耦", "分层", "微服务"],
            "Features实现": ["实现", "开发", "构建", "创建", "添加"],
            "问题修复": ["修复", "解决", "bug", "错误", "异常"],
            "最佳实践": ["最佳实践", "建议", "推荐", "规范", "标准"]
        }

        solution_types = []
        for solution_type, keywords in solution_patterns.items():
            if any(keyword in ai_response for keyword in keywords):
                solution_types.append(solution_type)

        # 提取具体方法（数字列表项）
        methods = re.findall(r'[0-9]\.\s*([^\n]{10,60})', ai_response)

        # 提取关键技术概念（中文+技术词）
        concept_pattern = r'([\u4e00-\u9fa5]{2,6})(管理|处理|机制|原理|模式|方法|策略|技术)'
        concepts = re.findall(concept_pattern, ai_response)
        key_concepts = list(set([c[0] + c[1] for c in concepts]))[:5]

        return {
            "tech_stack": tech_stack[:5],
            "solution_types": solution_types[:3],
            "methods_count": len(methods),
            "key_concepts": key_concepts,
            "response_length": len(ai_response),
            "is_detailed": len(ai_response) > 200  # 回复是否详细
        }

    @classmethod
    def generate_title_prompt(cls, user_question: str, ai_response: str) -> str:
        """
        生成用于调用LLM的标题生成提示词

        Args:
            user_question: 用户的问题
            ai_response: AI的完整回复

        Returns:
            str: 格式化的提示词
        """
        prompt = f"""你是标题生成专家。任务：为AI对话生成一个精准、高价值的标题。

## 对话内容

用户问题：{user_question}

AI完整回复：{ai_response}

---

## 标题生成指令

### 第1步：深度理解AI回复
仔细阅读AI的**完整回复**，提取：
- 提到了哪些具体技术/工具/框架？（如：Django、React、MySQL、Redis）
- 核心解决方案是什么？（如：性能优化、架构设计、Bug修复）
- 重点讨论的概念？（如：状态管理、索引优化、异步处理）
- 提供了什么方法论？（如：缓存策略、重构方案）

### 第2步：识别对话领域
快速判断领域：
- **技术开发**：编程、调试、架构（标题=技术名+Features+操作）
- **商业分析**：数据、财务、市场（标题=对象+分析类型）
- **内容创作**：写作、设计、创意（标题=主题+创作形式）
- **知识咨询**：概念解释、原理学习（标题=概念名+知识类型）
- **问题解决**：优化、改进、修复（标题=对象+解决方向）

### 第3步：构建标题（严格公式）

**中文标题公式（8-10字）：**
[技术名 2-3字] + [Features模块 3-4字] + [核心价值 2-3字]

示例：
- "Django" + "User registered" + "性能优化" = "DjangoUser registered性能优化"
- "React Hooks" + "状态管理" + "原理" = "React Hooks状态管理原理"
- "电商" + "支付系统" + "架构设计" = "电商支付系统架构设计"

**英文标题公式（4-6词）：**
[Technology] + [Feature/Module] + [Action/Value]

示例：
- "React Component Performance Optimization" (4词)
- "Django User Registration Optimization" (4词)

---

## 严格禁止（违反=不合格）

❌ 禁用词：文档、讨论、分析、问题、咨询、对话、聊天、关于、有关
❌ 笼统表达：技术问题、网站开发、数据处理
❌ 数字编号：对话1、新对话2
❌ 过短：少于8个中文字或4个英文词

## 必须满足（全部✓才合格）

✓ 包含具体技术/产品/对象名称
✓ 反映AI提供的核心价值（不只是复述用户问题）
✓ 8-10个中文字（不是4字后加后缀！）
✓ 信息密度高，每个字都有意义

---

## 自检清单

生成标题后，验证：
1. 是否从AI回复中提取了技术名称？
2. 是否包含具体Features/模块？
3. 是否体现了核心价值/操作？
4. 中文标题是否8-10字？
5. 是否避免了所有禁用词？

如不满足任何一条，重新生成！

---

现在，基于AI的完整回复，生成8-10字的标题（仅输出标题，无解释，无标点）："""

        return prompt

    @classmethod
    def validate_and_expand_title(cls, title: str) -> str:
        """
        验证标题长度,如果太短则自动扩展

        Args:
            title: 生成的标题

        Returns:
            str: 扩展后的标题
        """
        import logging
        logger = logging.getLogger(__name__)

        chinese_chars = len([c for c in title if '\u4e00' <= c <= '\u9fff'])

        if chinese_chars > 0:
            # 中文标题
            if chinese_chars < 8:
                # 标题太短,需要扩展
                logger.warning(f"标题太短({chinese_chars}字): '{title}',正在扩展...")

                # 扩展策略:添加后缀
                if chinese_chars <= 4:
                    expanded = title + "完整实践指南"
                elif chinese_chars <= 6:
                    expanded = title + "优化方案"
                else:
                    expanded = title + "详解"

                final_length = len([c for c in expanded if '\u4e00' <= c <= '\u9fff'])
                logger.info(f"扩展后标题: '{expanded}' ({final_length}字)")
                return expanded
        else:
            # 英文标题
            words = title.split()
            if len(words) < 4:
                # 英文标题太短,扩展
                logger.warning(f"Title too short ({len(words)} words): '{title}', expanding...")

                if len(words) <= 2:
                    expanded = title + " Complete Guide"
                else:
                    expanded = title + " Guide"

                logger.info(f"Expanded title: '{expanded}' ({len(expanded.split())} words)")
                return expanded

        return title

    @classmethod
    def extract_meaningful_content(cls, text: str, max_length: int = 12) -> str:
        """
        从文本中提取有意义的内容（用于fallback场景）

        Args:
            text: 原始文本
            max_length: 最大长度

        Returns:
            str: 提取的有意义内容
        """
        # 移除常见的无意义前缀（可能有多个前缀组合）
        cleaned_text = text
        changed = True
        iterations = 0
        max_iterations = 5  # 防止无限循环

        while changed and iterations < max_iterations:
            changed = False
            for prefix in cls.MEANINGLESS_PREFIXES:
                if cleaned_text.startswith(prefix):
                    cleaned_text = cleaned_text[len(prefix):].lstrip("，。！？,.!? ")
                    changed = True
                    break
            iterations += 1

        # 移除标点符号
        cleaned_text = re.sub(r'[，。！？,.!?；;：:""''、]', '', cleaned_text)

        # 如果清理后太短或为空，使用原文
        if not cleaned_text or len(cleaned_text) < 3:
            cleaned_text = text
            # 移除标点
            cleaned_text = re.sub(r'[，。！？,.!?；;：:""''、]', '', cleaned_text)

        # 智能截取：不要在词语中间截断
        if len(cleaned_text) > max_length:
            # 先截取到max_length
            truncated = cleaned_text[:max_length]

            # 检查是否截断了完整词语（对于中英文混合）
            # 如果截断位置后面还有内容，且不是空格/标点，则可能截断了词语
            if len(cleaned_text) > max_length:
                remaining = cleaned_text[max_length:]
                # 如果剩余部分是字母或汉字，说明可能截断了词语
                if remaining and (remaining[0].isalnum() or '\u4e00' <= remaining[0] <= '\u9fff'):
                    # 向前找到最近的分隔点（空格或中英文边界）
                    for i in range(len(truncated) - 1, max(0, len(truncated) - 4), -1):
                        if truncated[i] == ' ':
                            return truncated[:i]
                        # 如果是英文后跟中文，或中文后跟英文，也可以作为边界
                        if i > 0:
                            is_cn_en_boundary = (
                                ('\u4e00' <= truncated[i-1] <= '\u9fff' and truncated[i].isalpha()) or
                                (truncated[i-1].isalpha() and '\u4e00' <= truncated[i] <= '\u9fff')
                            )
                            if is_cn_en_boundary:
                                return truncated[:i]

            return truncated

        return cleaned_text if cleaned_text else text[:max_length]

    @classmethod
    def validate_title(cls, title: str) -> Tuple[bool, Optional[str]]:
        """
        验证标题质量

        Args:
            title: 生成的标题

        Returns:
            Tuple[bool, Optional[str]]: (是否合格, 失败原因)
        """
        # 检查是否包含禁用词
        for forbidden_word in cls.FORBIDDEN_WORDS:
            if forbidden_word in title:
                return False, f"包含禁用词: {forbidden_word}"

        # 检查长度（中文5-12字，英文3-8个单词）
        chinese_chars = len([c for c in title if '\u4e00' <= c <= '\u9fff'])
        if chinese_chars > 0:
            # 中文标题：5字也可接受（如"MySQL索引优化"虽然只有4个汉字，但整体6字符）
            total_chars = len(title)
            if total_chars < 5:
                return False, "标题过短，至少需要5characters"
            if total_chars > 15:
                return False, "标题过长，最多15characters"
        else:
            # 英文标题
            words = title.split()
            if len(words) < 3:
                return False, "标题过短，至少3个单词"
            if len(words) > 8:
                return False, "标题过长，最多8个单词"

        # 检查是否为数字编号
        if re.match(r'^(对话|新对话|会话)\s*\d+$', title):
            return False, "不能使用数字编号"

        # 检查是否过于笼统
        generic_patterns = [
            r'^技术\w+$',
            r'^数据\w+$',
            r'^\w+问题$',
            r'^\w+讨论$',
            r'^\w+咨询$'
        ]
        for pattern in generic_patterns:
            if re.match(pattern, title):
                return False, "标题过于笼统"

        return True, None

    @classmethod
    def post_process_title(cls, title: str) -> str:
        """
        后处理标题：移除引号、标点、多余空格等

        Args:
            title: 原始标题

        Returns:
            str: 处理后的标题
        """
        # 移除引号
        title = title.strip('"\'""''「」『』【】')

        # 移除结尾的标点符号
        title = title.rstrip('。，！？,.!?；;：:')

        # 移除多余空格
        title = re.sub(r'\s+', ' ', title).strip()

        # 智能限制长度
        chinese_chars = len([c for c in title if '\u4e00' <= c <= '\u9fff'])
        if chinese_chars > 0:
            # 中文标题：最多15characters
            if len(title) > 15:
                # 截取到15字符，但避免在词语中间截断
                truncated = title[:15]

                # 如果截断点后还有内容，检查是否截断了词语
                if len(title) > 15:
                    # 向前找最近的安全截断点（空格或中英文边界）
                    for i in range(len(truncated) - 1, max(12, len(truncated) - 3), -1):
                        if truncated[i] == ' ':
                            title = truncated[:i]
                            break
                        if i > 0:
                            # 中英文边界
                            is_boundary = (
                                ('\u4e00' <= truncated[i-1] <= '\u9fff' and truncated[i].isalpha()) or
                                (truncated[i-1].isalpha() and '\u4e00' <= truncated[i] <= '\u9fff')
                            )
                            if is_boundary:
                                title = truncated[:i]
                                break
                    else:
                        # 没找到合适边界，直接截断
                        title = truncated
                else:
                    title = truncated
        else:
            # 英文标题：最多40characters（约6-8个单词）
            if len(title) > 40:
                title = title[:40].rsplit(' ', 1)[0]  # 在单词边界截断

        return title

    @classmethod
    def generate_fallback_title(cls, user_question: str) -> str:
        """
        生成备用标题（当LLM生成失败或质量不合格时）

        Args:
            user_question: 用户问题

        Returns:
            str: 备用标题
        """
        # 提取有意义的内容（最大12字，保持词语完整）
        meaningful_content = cls.extract_meaningful_content(user_question, max_length=12)

        # 如果提取结果为空或过短，使用原始问题的前12characters
        if len(meaningful_content) < 4:
            meaningful_content = user_question[:12]

        return meaningful_content


def create_title_generation_prompt(user_question: str, ai_response: str) -> str:
    """
    创建标题生成提示词（供外部调用）

    Args:
        user_question: 用户问题
        ai_response: AI回复

    Returns:
        str: 提示词
    """
    return IntelligentTitleGenerator.generate_title_prompt(user_question, ai_response)


def validate_and_process_title(title: str, user_question: str) -> str:
    """
    验证并处理标题（供外部调用）

    Args:
        title: LLM生成的标题
        user_question: 用户问题（用于fallback）

    Returns:
        str: 处理后的标题
    """
    import logging
    logger = logging.getLogger(__name__)

    generator = IntelligentTitleGenerator()

    # 后处理标题
    processed_title = generator.post_process_title(title)

    # 验证标题质量
    is_valid, error_reason = generator.validate_title(processed_title)

    if not is_valid:
        # 质量不合格，使用fallback
        logger.warning(f"标题质量不合格: {error_reason}，LLM生成的标题是: '{title}'")
        logger.warning(f"这说明LLM没有遵守提示词要求，需要优化提示词")
        # 使用fallback作为最后手段
        fallback = generator.generate_fallback_title(user_question)
        return fallback

    return processed_title
