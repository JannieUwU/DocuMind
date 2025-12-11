"""
学术术语提取服务
Intelligent Academic Term Extraction Service

采用多层识别策略:
1. NLP规则引擎 - 快速模式匹配
2. AI语义分析 - LLM深度理解
3. 知识库增强 - 专业术语验证
"""

import re
from typing import List, Dict, Optional
import logging

# 导入数据库查询接口
try:
    from term_database import get_database, search_terms_in_text
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    logging.warning("术语数据库不可用,将只使用规则引擎")

logger = logging.getLogger(__name__)


class AcademicTermExtractor:
    """智能学术术语提取器"""

    # 学术术语模式（中文）
    CHINESE_PATTERNS = [
        # ========== 专有术语枚举（精确匹配）==========
        # 机器学习/深度学习
        r'(深度学习|机器学习|强化学习|监督学习|无监督学习|迁移学习|联邦学习)',
        r'(神经网络|卷积神经网络|循环神经网络|生成对抗网络|注意力机制)',
        r'(过拟合|欠拟合|正则化|归一化|标准化|批量归一化|数据增强)',
        r'(梯度下降|反向传播|激活函数|损失函数|优化算法)',

        # 自然语言处理
        r'(自然语言处理|命名实体识别|情感分析|机器翻译|文本分类|分词)',
        r'(词性标注|语义分析|语音识别|语音合成)',

        # 计算机视觉
        r'(计算机视觉|图像分类|目标检测|图像分割|实例分割|语义分割)',
        r'(边缘检测|特征提取|图像增强)',

        # 数据科学
        r'(特征工程|数据清洗|数据可视化|模型评估|交叉验证)',
        r'(准确率|召回率|精确率|F1得分|ROC曲线|AUC)',

        # 算法
        r'(快速排序|归并排序|堆排序|冒泡排序|选择排序|插入排序)',
        r'(二分查找|深度优先搜索|广度优先搜索|动态规划|贪心算法|分治算法)',
        r'(哈希表|红黑树|B树|二叉树|链表|栈|队列)',

        # 数据库
        r'(关系型数据库|非关系型数据库|NoSQL数据库|数据库索引|事务管理|查询优化)',
        r'(主键|外键|索引|事务|锁|视图|存储过程)',

        # Web开发
        r'(前端开发|后端开发|全栈开发|单页应用|服务端渲染|客户端渲染)',
        r'(状态管理|路由管理|响应式设计|组件化开发)',

        # 架构与部署
        r'(微服务架构|单体架构|分布式系统|负载均衡|服务发现|API网关)',
        r'(容器化|容器编排|持续集成|持续部署|自动化部署)',

        # 网络安全
        r'(身份认证|授权|加密|解密|数字签名|哈希算法|对称加密|非对称加密)',

        # 区块链
        r'(区块链技术|智能合约|共识机制|工作量证明|权益证明|分布式账本)',

        # ========== 技术框架枚举 ==========
        r'(TensorFlow|PyTorch|Keras|Scikit-learn|Pandas|NumPy|OpenCV|Matplotlib)',
        r'(Transformer|BERT|GPT|ResNet|VGG|LSTM|GRU|CNN|RNN|U-Net|YOLO)',
        r'(React|Vue|Angular|Redux|Vuex|Next\.js|Nuxt\.js|Webpack|Vite)',
        r'(Node\.js|Express|Django|Flask|FastAPI|Spring|Spring Boot)',
        r'(MySQL|PostgreSQL|MongoDB|Redis|Elasticsearch|Hadoop|Spark|Kafka)',
        r'(Docker|Kubernetes|Jenkins|GitLab CI|Prometheus|Grafana|Nginx)',
        r'(Swift|Kotlin|Flutter|React Native|SwiftUI|Jetpack Compose|Android|iOS)',

        # ========== 通用后缀模式（保守匹配）==========
        # 只匹配2-4个汉字的术语（避免过长片段）
        r'([\\u4e00-\\u9fa5]{2,4})(算法|模型|架构|框架|协议)',
        r'([\\u4e00-\\u9fa5]{2,4})(学习|网络|计算)',
    ]

    # 英文技术术语模式
    ENGLISH_PATTERNS = [
        # ========== 常见技术缩写（精确枚举）==========
        r'\b(AI|ML|DL|NLP|CV|CNN|RNN|LSTM|GRU|GAN|VAE)\b',
        r'\b(API|SDK|REST|RESTful|GraphQL|gRPC|HTTP|HTTPS|TCP|UDP|IP)\b',
        r'\b(JSON|XML|YAML|HTML|CSS|SQL|NoSQL)\b',
        r'\b(AWS|GCP|Azure|S3|EC2|RDS)\b',
        r'\b(CI|CD|DevOps|MLOps|GitOps)\b',
        r'\b(JWT|OAuth|SSO|SAML|LDAP)\b',
        r'\b(GPU|CPU|TPU|FPGA|ASIC)\b',
        r'\b(UI|UX|MVP|POC|QA)\b',

        # ========== 驼峰命名技术（精确枚举）==========
        r'\b(TensorFlow|PyTorch|JavaScript|TypeScript|CoffeeScript)\b',
        r'\b(React|ReactNative|Vue|VueRouter|Angular|AngularJS)\b',
        r'\b(Redux|Vuex|MobX|RxJS)\b',
        r'\b(Node|NodeJS|Express|Koa|Fastify)\b',
        r'\b(Django|Flask|FastAPI|Tornado)\b',
        r'\b(Spring|SpringBoot|SpringCloud|Hibernate)\b',
        r'\b(MySQL|PostgreSQL|MongoDB|Redis|Elasticsearch)\b',
        r'\b(Docker|Kubernetes|Jenkins|GitLab|GitHub)\b',
        r'\b(Nginx|Apache|Tomcat|IIS)\b',
        r'\b(Swift|Kotlin|Java|Python|Golang|Rust)\b',
        r'\b(NumPy|Pandas|Matplotlib|Scikit|SciPy)\b',
        r'\b(Transformer|BERT|GPT|ResNet|VGG|Inception|MobileNet)\b',
        r'\b(Hadoop|Spark|Flink|Kafka|RabbitMQ)\b',
        r'\b(Prometheus|Grafana|Kibana|Logstash|Jaeger)\b',

        # ========== 通用驼峰模式（保守匹配）==========
        # 只匹配明显的驼峰命名（首字母大写+至少一个大写字母）
        r'\b([A-Z][a-z]+[A-Z][a-z]+(?:[A-Z][a-z]+)*)\b',

        # ========== 特殊格式 ==========
        r'\b(Next\.js|Nuxt\.js|D3\.js|Three\.js|Chart\.js|Moment\.js)\b',
        r'\b(C\+\+|C#|F#|\.NET|ASP\.NET)\b',
    ]

    # 停用术语（太常见或无意义的片段，不算学术词）
    STOPWORDS = {
        # 通用词汇
        '系统', '平台', '工具', '方法', '技术', '方案', '问题', '情况',
        '内容', '文档', '数据', '信息', '结果', '过程', '步骤',
        '方式', '形式', '类型', '种类', '部分', '方面',

        # 动词短语（无意义片段）
        '需要考虑', '可以使用', '进行处理', '实现Features', '提供服务',
        '支持多种', '包括多个', '具有良好', '保证系统', '确保数据',
        '采用先进', '基于现代', '使用最新', '通过优化', '利用高效',

        # 形容词短语（太宽泛）
        '高性能', '高可用', '高并发', '分布式', '集中式',
        '实时性', '稳定性', '可靠性', '安全性', '扩展性',

        # 组合词（无实际意义）
        '优化技术', '处理方法', '管理系统', '控制平台', '分析工具',
        '查询性能', '存储模型', '计算框架', '开发环境', '运行时',

        # 无用片段（从测试中发现）
        '索引优化', '查询性能', '事务管理', '数据存储', '性能优化'
    }

    # 专业术语知识库 (200+ terms)
    TERM_KNOWLEDGE_BASE = {
        # ========== 机器学习/深度学习 (30+ terms) ==========
        '机器学习': {
            'category': '人工智能',
            'definition': '让计算机从数据中自动学习规律和模式的技术',
            'keywords': ['算法', '模型', '训练', '预测']
        },
        '深度学习': {
            'category': '机器学习',
            'definition': '基于多层神经网络的机器学习方法',
            'keywords': ['神经网络', '深层', '表征学习']
        },
        '神经网络': {
            'category': '深度学习',
            'definition': '模仿生物神经元结构的计算模型',
            'keywords': ['节点', '权重', '激活', '层']
        },
        '卷积神经网络': {
            'category': '深度学习',
            'definition': '专门用于处理网格结构数据（如图像）的神经网络',
            'keywords': ['卷积', '池化', '特征图', 'CNN']
        },
        '循环神经网络': {
            'category': '深度学习',
            'definition': '能够处理序列数据的神经网络',
            'keywords': ['时序', '循环', '记忆', 'RNN']
        },
        '强化学习': {
            'category': '机器学习',
            'definition': '通过与环境交互学习最优策略的方法',
            'keywords': ['奖励', '策略', '智能体', '环境']
        },
        '监督学习': {
            'category': '机器学习',
            'definition': '从标注数据中学习输入到输出映射的方法',
            'keywords': ['标签', '训练集', '预测']
        },
        '无监督学习': {
            'category': '机器学习',
            'definition': '从无标注数据中发现隐藏模式的方法',
            'keywords': ['聚类', '降维', '异常检测']
        },
        '迁移学习': {
            'category': '机器学习',
            'definition': '将在一个任务上学到的知识应用到另一个任务',
            'keywords': ['预训练', '微调', '领域适应']
        },
        '联邦学习': {
            'category': '机器学习',
            'definition': '多方协作训练模型而无需共享原始数据的方法',
            'keywords': ['隐私保护', '分布式', '协作学习']
        },

        # 优化与训练 (15+ terms)
        '梯度下降': {
            'category': '优化算法',
            'definition': '通过计算梯度来迭代优化模型参数的方法',
            'keywords': ['梯度', '学习率', '优化', '收敛']
        },
        'SGD': {
            'category': '优化算法',
            'definition': '随机梯度下降，每次使用部分样本更新参数',
            'keywords': ['随机', '批量', '优化']
        },
        'Adam': {
            'category': '优化算法',
            'definition': '自适应学习率优化算法',
            'keywords': ['动量', '自适应', '学习率']
        },
        'RMSprop': {
            'category': '优化算法',
            'definition': '使用移动平均的梯度平方来调整学习率',
            'keywords': ['自适应', '学习率', '梯度']
        },
        '反向传播': {
            'category': '训练算法',
            'definition': '计算神经网络中参数梯度的高效算法',
            'keywords': ['链式法则', '梯度', '误差', '传播']
        },
        '过拟合': {
            'category': '模型问题',
            'definition': '模型在训练数据上表现好但泛化能力差的现象',
            'keywords': ['泛化', '过度学习', '复杂度']
        },
        '欠拟合': {
            'category': '模型问题',
            'definition': '模型过于简单，无法捕捉数据的真实规律',
            'keywords': ['简单', '欠学习', '偏差']
        },
        '正则化': {
            'category': '优化技术',
            'definition': '防止模型过拟合的技术手段',
            'keywords': ['L1', 'L2', '惩罚项', '约束']
        },
        '归一化': {
            'category': '数据处理',
            'definition': '将数据缩放到特定范围的技术',
            'keywords': ['标准化', '缩放', '预处理']
        },
        '批量归一化': {
            'category': '训练技术',
            'definition': '在每个批次上标准化激活值的技术',
            'keywords': ['Batch Normalization', '训练', '稳定']
        },
        'Dropout': {
            'category': '正则化技术',
            'definition': '训练时随机丢弃部分神经元以防止过拟合',
            'keywords': ['丢弃', '随机', '正则化']
        },
        '数据增强': {
            'category': '数据处理',
            'definition': '通过变换生成更多训练样本的技术',
            'keywords': ['变换', '扩充', '泛化']
        },

        # ========== 深度学习框架 (10+ terms) ==========
        'TensorFlow': {
            'category': '深度学习框架',
            'definition': 'Google开发的开源深度学习框架',
            'keywords': ['张量', '计算图', 'Google']
        },
        'PyTorch': {
            'category': '深度学习框架',
            'definition': 'Facebook开发的动态图深度学习框架',
            'keywords': ['动态图', '张量', 'Facebook']
        },
        'Keras': {
            'category': '深度学习框架',
            'definition': '高层神经网络API，运行在TensorFlow之上',
            'keywords': ['高层API', '简洁', 'Python']
        },
        'JAX': {
            'category': '深度学习框架',
            'definition': 'Google的高性能数值计算库',
            'keywords': ['自动微分', 'JIT编译', 'NumPy']
        },
        'MXNet': {
            'category': '深度学习框架',
            'definition': 'Apache的灵活高效深度学习框架',
            'keywords': ['分布式', '高效', 'Apache']
        },

        # ========== 自然语言处理 (20+ terms) ==========
        'Transformer': {
            'category': '自然语言处理',
            'definition': '基于自注意力机制的序列处理架构',
            'keywords': ['注意力', '编码器', '解码器']
        },
        'BERT': {
            'category': '预训练模型',
            'definition': '双向编码器表示模型，用于自然语言理解',
            'keywords': ['预训练', '微调', '掩码语言模型']
        },
        'GPT': {
            'category': '预训练模型',
            'definition': '生成式预训练Transformer模型',
            'keywords': ['生成', '自回归', '语言模型']
        },
        'T5': {
            'category': '预训练模型',
            'definition': 'Text-to-Text Transfer Transformer统一框架',
            'keywords': ['文本到文本', '统一', 'Google']
        },
        'RoBERTa': {
            'category': '预训练模型',
            'definition': '优化的BERT训练方法',
            'keywords': ['鲁棒', 'BERT变体', '优化']
        },
        'ELECTRA': {
            'category': '预训练模型',
            'definition': '使用判别器训练的高效预训练模型',
            'keywords': ['判别器', '高效', '预训练']
        },
        'LSTM': {
            'category': '循环神经网络',
            'definition': '长短期记忆网络，解决RNN梯度消失问题',
            'keywords': ['记忆单元', '门控', '长依赖']
        },
        'GRU': {
            'category': '循环神经网络',
            'definition': '门控循环单元，简化版的LSTM',
            'keywords': ['门控', '简化', '循环']
        },
        'Word2Vec': {
            'category': '词嵌入',
            'definition': '将词映射到向量空间的方法',
            'keywords': ['词向量', '嵌入', '语义']
        },
        'GloVe': {
            'category': '词嵌入',
            'definition': '基于全局词频统计的词向量方法',
            'keywords': ['全局', '词向量', '共现']
        },
        'TF-IDF': {
            'category': '文本表示',
            'definition': '词频-逆文档频率，评估词的重要性',
            'keywords': ['词频', '重要性', '文本']
        },
        'NLP': {
            'category': '自然语言处理',
            'definition': '自然语言处理，让计算机理解和生成人类语言',
            'keywords': ['语言', '理解', '生成']
        },
        '分词': {
            'category': '文本处理',
            'definition': '将连续文本切分为词语序列',
            'keywords': ['切分', '词语', '预处理']
        },
        '命名实体识别': {
            'category': '信息抽取',
            'definition': '识别文本中的人名、地名、机构名等实体',
            'keywords': ['NER', '实体', '抽取']
        },
        '情感分析': {
            'category': '文本分类',
            'definition': '判断文本表达的情感倾向',
            'keywords': ['情感', '分类', '极性']
        },
        '机器翻译': {
            'category': '自然语言处理',
            'definition': '自动将一种语言翻译成另一种语言',
            'keywords': ['翻译', '多语言', 'seq2seq']
        },

        # ========== 计算机视觉 (20+ terms) ==========
        'ResNet': {
            'category': '计算机视觉',
            'definition': '深度残差网络，通过跳跃连接解决深层网络训练问题',
            'keywords': ['残差', '跳跃连接', '深层网络']
        },
        'VGG': {
            'category': '计算机视觉',
            'definition': '使用小卷积核的深度卷积网络',
            'keywords': ['小卷积核', '深度', '图像分类']
        },
        'Inception': {
            'category': '计算机视觉',
            'definition': '使用多尺度卷积的网络架构',
            'keywords': ['多尺度', '并行', 'GoogLeNet']
        },
        'MobileNet': {
            'category': '计算机视觉',
            'definition': '面向移动设备的轻量级卷积网络',
            'keywords': ['轻量', '移动', '高效']
        },
        'YOLO': {
            'category': '目标检测',
            'definition': 'You Only Look Once，实时目标检测算法',
            'keywords': ['实时', '检测', '单阶段']
        },
        'Faster R-CNN': {
            'category': '目标检测',
            'definition': '基于区域的卷积神经网络目标检测方法',
            'keywords': ['区域', '两阶段', '检测']
        },
        'SSD': {
            'category': '目标检测',
            'definition': 'Single Shot Detector，单次检测多尺度目标',
            'keywords': ['单次', '多尺度', '检测']
        },
        'U-Net': {
            'category': '图像分割',
            'definition': 'U型编码解码器网络，用于图像分割',
            'keywords': ['分割', '医学图像', 'U型']
        },
        'Mask R-CNN': {
            'category': '实例分割',
            'definition': '在Faster R-CNN基础上添加掩码分支',
            'keywords': ['实例分割', '掩码', '检测']
        },
        '目标检测': {
            'category': '计算机视觉',
            'definition': '识别图像中物体的位置和类别的技术',
            'keywords': ['边界框', '分类', '定位']
        },
        '图像分割': {
            'category': '计算机视觉',
            'definition': '将图像划分为多个语义区域',
            'keywords': ['像素级', '分割', '语义']
        },
        '图像分类': {
            'category': '计算机视觉',
            'definition': '判断图像所属类别的任务',
            'keywords': ['分类', '识别', '类别']
        },
        'OpenCV': {
            'category': '计算机视觉库',
            'definition': '开源计算机视觉和机器学习库',
            'keywords': ['图像处理', '视觉', '开源']
        },
        'GAN': {
            'category': '生成模型',
            'definition': '生成对抗网络，通过对抗训练生成数据',
            'keywords': ['生成', '对抗', '判别器']
        },
        'VAE': {
            'category': '生成模型',
            'definition': '变分自编码器，概率生成模型',
            'keywords': ['变分', '编码器', '生成']
        },

        # ========== Web开发框架 (25+ terms) ==========
        'React': {
            'category': 'Web框架',
            'definition': '用于构建用户界面的JavaScript库',
            'keywords': ['组件', '虚拟DOM', '状态管理']
        },
        'Vue': {
            'category': 'Web框架',
            'definition': '渐进式JavaScript框架',
            'keywords': ['响应式', '组件', '指令']
        },
        'Angular': {
            'category': 'Web框架',
            'definition': 'Google开发的TypeScript前端框架',
            'keywords': ['TypeScript', '组件', 'Google']
        },
        'Redux': {
            'category': '状态管理',
            'definition': 'JavaScript应用的可预测状态容器',
            'keywords': ['状态管理', '单向数据流', 'React']
        },
        'Vuex': {
            'category': '状态管理',
            'definition': 'Vue.js的状态管理模式和库',
            'keywords': ['状态管理', 'Vue', '集中式']
        },
        'Next.js': {
            'category': 'Web框架',
            'definition': 'React的服务端渲染框架',
            'keywords': ['SSR', 'React', '服务端渲染']
        },
        'Nuxt.js': {
            'category': 'Web框架',
            'definition': 'Vue.js的服务端渲染框架',
            'keywords': ['SSR', 'Vue', '服务端渲染']
        },
        'Webpack': {
            'category': '构建工具',
            'definition': '现代JavaScript应用的模块打包工具',
            'keywords': ['打包', '模块', '构建']
        },
        'Vite': {
            'category': '构建工具',
            'definition': '新一代前端构建工具，基于ES模块',
            'keywords': ['快速', '构建', 'ESM']
        },
        'TypeScript': {
            'category': '编程语言',
            'definition': 'JavaScript的超集，添加了静态类型',
            'keywords': ['类型', 'JavaScript', '静态']
        },
        'Node.js': {
            'category': '运行时',
            'definition': '基于Chrome V8的JavaScript运行时',
            'keywords': ['服务端', 'JavaScript', '异步']
        },
        'Express': {
            'category': 'Web框架',
            'definition': 'Node.js的简洁Web应用框架',
            'keywords': ['Node.js', '中间件', 'Web']
        },
        'Django': {
            'category': 'Web框架',
            'definition': 'Python的高级Web框架',
            'keywords': ['MTV', 'ORM', 'Python']
        },
        'Flask': {
            'category': 'Web框架',
            'definition': 'Python的轻量级Web框架',
            'keywords': ['微框架', 'Python', '轻量']
        },
        'FastAPI': {
            'category': 'Web框架',
            'definition': '现代、快速的Python Web框架',
            'keywords': ['异步', 'Python', 'API']
        },
        'Spring': {
            'category': 'Web框架',
            'definition': 'Java企业级应用开发框架',
            'keywords': ['Java', '企业级', '依赖注入']
        },
        'Spring Boot': {
            'category': 'Web框架',
            'definition': '简化Spring应用开发的框架',
            'keywords': ['Spring', '快速开发', '约定']
        },
        'GraphQL': {
            'category': 'API技术',
            'definition': 'Facebook开发的API查询语言',
            'keywords': ['查询', 'API', '灵活']
        },
        'REST': {
            'category': 'API设计',
            'definition': '表述性状态转移的架构风格',
            'keywords': ['HTTP', 'RESTful', '资源']
        },
        'RESTful': {
            'category': 'API设计',
            'definition': '遵循REST原则的API设计风格',
            'keywords': ['REST', 'HTTP', 'API']
        },
        'JWT': {
            'category': '身份认证',
            'definition': 'JSON Web Token，用于身份验证的令牌',
            'keywords': ['令牌', '认证', 'JSON']
        },
        'OAuth': {
            'category': '身份认证',
            'definition': '开放授权标准，允许第三方访问',
            'keywords': ['授权', '第三方', '安全']
        },

        # ========== 数据库 (20+ terms) ==========
        'MySQL': {
            'category': '数据库',
            'definition': '开源关系型数据库管理系统',
            'keywords': ['SQL', '关系型', '数据库']
        },
        'PostgreSQL': {
            'category': '数据库',
            'definition': 'Features强大的开源关系型数据库',
            'keywords': ['SQL', '关系型', '开源']
        },
        'MongoDB': {
            'category': '数据库',
            'definition': '面向文档的NoSQL数据库',
            'keywords': ['NoSQL', '文档', 'JSON']
        },
        'Redis': {
            'category': '数据库',
            'definition': '内存中的数据结构存储系统，用作数据库、缓存',
            'keywords': ['缓存', '键值', '内存']
        },
        'Elasticsearch': {
            'category': '搜索引擎',
            'definition': '分布式搜索和分析引擎',
            'keywords': ['搜索', '全文检索', '分布式']
        },
        'NoSQL': {
            'category': '数据库类型',
            'definition': '非关系型数据库的统称',
            'keywords': ['非关系型', '灵活', '扩展']
        },
        'SQL': {
            'category': '查询语言',
            'definition': '结构化查询语言，用于管理关系型数据库',
            'keywords': ['查询', '关系型', '数据库']
        },
        'ORM': {
            'category': '数据映射',
            'definition': '对象关系映射，将对象模型映射到数据库',
            'keywords': ['映射', '对象', '数据库']
        },
        'ACID': {
            'category': '数据库特性',
            'definition': '原子性、一致性、隔离性、持久性',
            'keywords': ['事务', '一致性', '数据库']
        },
        '索引': {
            'category': '数据库优化',
            'definition': '加速数据检索的数据结构',
            'keywords': ['查询', '优化', '性能']
        },
        '事务': {
            'category': '数据库操作',
            'definition': '作为单个逻辑工作单元的操作序列',
            'keywords': ['ACID', '原子性', '一致性']
        },
        '主键': {
            'category': '数据库设计',
            'definition': '唯一标识表中每行记录的字段',
            'keywords': ['唯一', '标识', '主键']
        },
        '外键': {
            'category': '数据库设计',
            'definition': '建立表间关系的字段',
            'keywords': ['关系', '约束', '外键']
        },

        # ========== 大数据与数据科学 (15+ terms) ==========
        'Hadoop': {
            'category': '大数据',
            'definition': '分布式存储和计算框架',
            'keywords': ['分布式', 'MapReduce', 'HDFS']
        },
        'Spark': {
            'category': '大数据',
            'definition': '快速通用的大数据处理引擎',
            'keywords': ['内存计算', '分布式', '快速']
        },
        'Kafka': {
            'category': '消息队列',
            'definition': '分布式流处理平台',
            'keywords': ['消息', '流处理', '分布式']
        },
        'Pandas': {
            'category': '数据分析',
            'definition': 'Python数据分析和处理库',
            'keywords': ['DataFrame', 'Python', '数据分析']
        },
        'NumPy': {
            'category': '科学计算',
            'definition': 'Python数值计算基础库',
            'keywords': ['数组', '数值计算', 'Python']
        },
        'Matplotlib': {
            'category': '数据可视化',
            'definition': 'Python绘图库',
            'keywords': ['绘图', '可视化', 'Python']
        },
        'Scikit-learn': {
            'category': '机器学习库',
            'definition': 'Python机器学习工具包',
            'keywords': ['机器学习', 'Python', '工具包']
        },
        '特征工程': {
            'category': '数据科学',
            'definition': '从原始数据中提取和构造特征的过程',
            'keywords': ['特征', '预处理', '提取']
        },
        '数据清洗': {
            'category': '数据处理',
            'definition': '处理和修正数据中的错误和不一致',
            'keywords': ['清洗', '预处理', '质量']
        },
        '交叉验证': {
            'category': '模型评估',
            'definition': '评估模型泛化能力的技术',
            'keywords': ['验证', '评估', '泛化']
        },

        # ========== 云计算与DevOps (20+ terms) ==========
        'Docker': {
            'category': '容器化',
            'definition': '应用容器引擎，用于打包、分发应用',
            'keywords': ['容器', '镜像', '隔离']
        },
        'Kubernetes': {
            'category': '容器编排',
            'definition': '容器编排平台，用于自动部署、扩展应用',
            'keywords': ['编排', '集群', '容器']
        },
        'AWS': {
            'category': '云平台',
            'definition': 'Amazon Web Services，亚马逊云服务',
            'keywords': ['云', 'Amazon', '基础设施']
        },
        'Azure': {
            'category': '云平台',
            'definition': '微软的云计算平台',
            'keywords': ['云', 'Microsoft', '服务']
        },
        'GCP': {
            'category': '云平台',
            'definition': 'Google Cloud Platform，谷歌云平台',
            'keywords': ['云', 'Google', '计算']
        },
        'CI/CD': {
            'category': 'DevOps',
            'definition': '持续集成和持续部署',
            'keywords': ['自动化', '部署', '集成']
        },
        'Jenkins': {
            'category': 'CI/CD',
            'definition': '开源自动化服务器',
            'keywords': ['自动化', 'CI', '构建']
        },
        'GitLab CI': {
            'category': 'CI/CD',
            'definition': 'GitLab内置的持续集成工具',
            'keywords': ['CI', 'GitLab', '自动化']
        },
        'Prometheus': {
            'category': '监控',
            'definition': '开源监控和告警系统',
            'keywords': ['监控', '时序数据', '告警']
        },
        'Grafana': {
            'category': '可视化',
            'definition': '开源指标分析和可视化平台',
            'keywords': ['可视化', '监控', '仪表板']
        },
        'Nginx': {
            'category': 'Web服务器',
            'definition': '高性能HTTP服务器和反向代理',
            'keywords': ['服务器', '反向代理', '负载均衡']
        },
        '微服务': {
            'category': '架构模式',
            'definition': '将应用拆分为小型独立服务的架构',
            'keywords': ['服务', '解耦', '独立']
        },
        '负载均衡': {
            'category': '系统架构',
            'definition': '将请求分发到多个服务器的技术',
            'keywords': ['分发', '高可用', '性能']
        },
        'API网关': {
            'category': '微服务',
            'definition': '微服务架构中的统一入口',
            'keywords': ['网关', '路由', '微服务']
        },

        # ========== 移动开发 (10+ terms) ==========
        'Swift': {
            'category': '编程语言',
            'definition': 'Apple开发的iOS应用编程语言',
            'keywords': ['iOS', 'Apple', '移动开发']
        },
        'Kotlin': {
            'category': '编程语言',
            'definition': 'Android官方推荐的开发语言',
            'keywords': ['Android', 'JVM', '移动开发']
        },
        'Flutter': {
            'category': '移动框架',
            'definition': 'Google的跨平台UI框架',
            'keywords': ['跨平台', 'Dart', 'Google']
        },
        'React Native': {
            'category': '移动框架',
            'definition': '使用React构建原生移动应用',
            'keywords': ['跨平台', 'React', 'JavaScript']
        },
        'SwiftUI': {
            'category': 'UI框架',
            'definition': 'Apple的声明式UI框架',
            'keywords': ['声明式', 'iOS', 'UI']
        },
        'Android': {
            'category': '移动平台',
            'definition': 'Google开发的移动操作系统',
            'keywords': ['移动', 'Google', '系统']
        },
        'iOS': {
            'category': '移动平台',
            'definition': 'Apple的移动操作系统',
            'keywords': ['移动', 'Apple', '系统']
        },

        # ========== 算法与数据结构 (15+ terms) ==========
        '快速排序': {
            'category': '排序算法',
            'definition': '基于分治的高效排序算法',
            'keywords': ['分治', '排序', 'O(nlogn)']
        },
        '归并排序': {
            'category': '排序算法',
            'definition': '稳定的分治排序算法',
            'keywords': ['分治', '稳定', '排序']
        },
        '堆排序': {
            'category': '排序算法',
            'definition': '基于堆数据结构的排序算法',
            'keywords': ['堆', '排序', '选择']
        },
        '二分查找': {
            'category': '查找算法',
            'definition': '在有序数组中查找元素的高效算法',
            'keywords': ['有序', '查找', 'O(logn)']
        },
        '哈希表': {
            'category': '数据结构',
            'definition': '通过哈希函数实现快速查找的数据结构',
            'keywords': ['哈希', '键值', 'O(1)']
        },
        '红黑树': {
            'category': '数据结构',
            'definition': '自平衡的二叉搜索树',
            'keywords': ['平衡', '树', '搜索']
        },
        'B树': {
            'category': '数据结构',
            'definition': '多路平衡查找树，用于数据库索引',
            'keywords': ['多路', '平衡', '索引']
        },
        '动态规划': {
            'category': '算法思想',
            'definition': '通过保存子问题解来优化的算法思想',
            'keywords': ['优化', '子问题', '记忆化']
        },
        '贪心算法': {
            'category': '算法思想',
            'definition': '每步选择局部最优解的算法',
            'keywords': ['局部最优', '贪心', '选择']
        },
        'Dijkstra': {
            'category': '图算法',
            'definition': '计算单源最短路径的算法',
            'keywords': ['最短路径', '图', '贪心']
        },
        'Floyd': {
            'category': '图算法',
            'definition': '计算所有顶点对最短路径的算法',
            'keywords': ['最短路径', '动态规划', '图']
        },

        # ========== 区块链 (8+ terms) ==========
        '区块链': {
            'category': '分布式技术',
            'definition': '分布式账本技术，数据以区块链式存储',
            'keywords': ['分布式', '账本', '不可篡改']
        },
        '比特币': {
            'category': '加密货币',
            'definition': '第一个去中心化的加密货币',
            'keywords': ['加密', '去中心化', '货币']
        },
        '以太坊': {
            'category': '区块链平台',
            'definition': '支持智能合约的区块链平台',
            'keywords': ['智能合约', '区块链', '平台']
        },
        '智能合约': {
            'category': '区块链',
            'definition': '在区块链上自动执行的合约',
            'keywords': ['自动执行', '合约', '区块链']
        },
        'PoW': {
            'category': '共识机制',
            'definition': '工作量证明共识机制',
            'keywords': ['共识', '挖矿', '工作量']
        },
        'PoS': {
            'category': '共识机制',
            'definition': '权益证明共识机制',
            'keywords': ['共识', '权益', '质押']
        },
        'AES': {
            'category': '加密算法',
            'definition': '高级加密标准，对称加密算法',
            'keywords': ['对称', '加密', '标准']
        },
        'RSA': {
            'category': '加密算法',
            'definition': '非对称加密算法',
            'keywords': ['非对称', '公钥', '加密']
        },
        'SHA-256': {
            'category': '哈希函数',
            'definition': '安全哈希算法，输出256位',
            'keywords': ['哈希', '安全', '256位']
        },
    }

    @classmethod
    def extract_terms(cls, text: str, use_ai: bool = True) -> List[Dict]:
        """
        提取文本中的学术术语 - 纯AI模式

        Args:
            text: 输入文本
            use_ai: 是否使用AI（现在总是True，保留参数用于兼容）

        Returns:
            List[Dict]: 术语列表，每个术语包含 term, definition, category, isFavorite
        """
        if not text or len(text.strip()) < 10:
            return []

        # 使用AI提取学术术语（返回格式化的列表）
        # 注意：实际的AI调用应该在API endpoint中完成
        # 这里只是占位符，实际会被main.py中的LLM调用替代
        return []

    @classmethod
    def _extract_by_rules(cls, text: str) -> List[str]:
        """使用规则引擎提取候选术语"""
        candidates = set()

        # 提取中文术语
        for pattern in cls.CHINESE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    term = ''.join(match)
                else:
                    term = match

                # 严格过滤：停用词 + 最小长度 + 不能是纯数字
                if (term not in cls.STOPWORDS and
                    len(term) >= 2 and
                    not term.isdigit() and
                    cls._is_valid_term(term)):
                    candidates.add(term)

        # 提取英文术语
        for pattern in cls.ENGLISH_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, str) and len(match) >= 2:
                    # 过滤常见词和无意义词
                    common_words = {'THE', 'AND', 'OR', 'BUT', 'FOR', 'WITH', 'FROM',
                                    'TO', 'IN', 'ON', 'AT', 'BY', 'AS', 'IS', 'WAS',
                                    'ARE', 'WERE', 'BE', 'BEEN', 'BEING', 'HAVE', 'HAS', 'HAD'}
                    if match.upper() not in common_words and cls._is_valid_term(match):
                        candidates.add(match)

        return list(candidates)

    @classmethod
    def _is_valid_term(cls, term: str) -> bool:
        """验证术语是否有效

        过滤规则:
        1. 不能包含无意义的连接词片段
        2. 中文术语至少2characters
        3. 英文术语至少2characters
        4. 不能是纯数字或符号
        """
        # 过滤无意义的连接词片段
        invalid_fragments = [
            '需要', '可以', '进行', '实现', '提供', '支持', '包括', '具有',
            '保证', '确保', '采用', '基于', '使用', '通过', '利用'
        ]

        for fragment in invalid_fragments:
            if term.startswith(fragment):
                return False

        # 中文术语长度检查
        chinese_chars = sum(1 for c in term if '\u4e00' <= c <= '\u9fa5')
        if chinese_chars > 0 and chinese_chars < 2:
            return False

        # 英文术语长度检查
        english_chars = sum(1 for c in term if c.isalpha() and ord(c) < 128)
        if english_chars > 0 and english_chars < 2:
            return False

        # 不能是纯符号
        if all(not c.isalnum() for c in term):
            return False

        return True

    @classmethod
    def _enrich_with_knowledge_base(cls, candidates: List[str], context: str) -> List[Dict]:
        """使用知识库丰富术语信息"""
        enriched = []

        for term in candidates:
            term_info = {
                'term': term,
                'definition': '',
                'category': '专业术语',
                'example': '',
                'context': cls._extract_context(term, context),
                'isFavorite': False
            }

            # 从知识库中查找定义
            if term in cls.TERM_KNOWLEDGE_BASE:
                kb_info = cls.TERM_KNOWLEDGE_BASE[term]
                term_info['definition'] = kb_info['definition']
                term_info['category'] = kb_info['category']
                term_info['example'] = cls._generate_example(term, kb_info.get('keywords', []))
            else:
                # 生成通用定义
                term_info['definition'] = cls._generate_generic_definition(term, context)
                term_info['example'] = cls._generate_example(term, [])

            enriched.append(term_info)

        return enriched

    @classmethod
    def _extract_context(cls, term: str, text: str, window_size: int = 50) -> str:
        """提取术语在文本中的上下文"""
        # 找到术语出现的位置
        idx = text.find(term)
        if idx == -1:
            idx = text.lower().find(term.lower())

        if idx == -1:
            return ''

        # 提取前后文本
        start = max(0, idx - window_size)
        end = min(len(text), idx + len(term) + window_size)
        context = text[start:end]

        # 清理
        if start > 0:
            context = '...' + context
        if end < len(text):
            context = context + '...'

        return context.strip()

    @classmethod
    def _generate_generic_definition(cls, term: str, context: str) -> str:
        """生成通用定义"""
        # 基于术语结构推断定义
        if '学习' in term:
            return f'{term}是一种机器学习方法'
        elif '网络' in term:
            return f'{term}是一种神经网络架构'
        elif '算法' in term:
            return f'{term}是一种计算算法'
        elif '模型' in term:
            return f'{term}是一种数学或计算模型'
        elif re.match(r'^[A-Z]{2,}$', term):
            return f'{term}是一个专业技术术语'
        elif re.match(r'^[A-Z][a-z]+(?:[A-Z][a-z]+)+$', term):
            return f'{term}是一个技术框架或工具'
        else:
            return f'{term}是一个专业概念'

    @classmethod
    def _generate_example(cls, term: str, keywords: List[str]) -> str:
        """生成示例"""
        if keywords:
            keyword = keywords[0]
            return f'在{keyword}中，{term}是重要的概念'
        else:
            return f'{term}在该领域中有广泛应用'

    @classmethod
    def _extract_by_ai_prompt(cls, text: str) -> List[Dict]:
        """使用AI提示词提取术语（占位符，实际需要调用LLM）"""
        # 这里返回空列表，实际应该调用LLM API
        # 将在后续的API endpoint中实现
        return []

    @classmethod
    def _extract_from_database(cls, text: str) -> List[Dict]:
        """
        从数据库中查找文本中的术语

        Args:
            text: 输入文本

        Returns:
            匹配的术语列表
        """
        try:
            # 使用数据库查询接口
            db_results = search_terms_in_text(text, min_weight=8)

            # 转换为统一格式
            enriched = []
            for db_term in db_results:
                term_info = {
                    'term': db_term['term'],
                    'definition': db_term['definition'],
                    'category': db_term['category'],
                    'example': f"{db_term['term']}在{db_term['domain']}领域中应用广泛",
                    'context': cls._extract_context(db_term['term'], text),
                    'isFavorite': False,
                    'weight': db_term['weight']  # 保留权重用于排序
                }
                enriched.append(term_info)

            logger.info(f"数据库查询找到 {len(enriched)} 个术语")
            return enriched

        except Exception as e:
            logger.error(f"数据库查询失败: {e}")
            return []

    @classmethod
    def _deduplicate_and_rank(cls, terms: List[Dict], text: str) -> List[Dict]:
        """去重并按重要性排序"""
        # 去重（基于术语名称）
        unique_map = {}
        for term_info in terms:
            term = term_info['term']
            if term not in unique_map:
                unique_map[term] = term_info

        # 计算重要性分数
        for term, info in unique_map.items():
            score = 0

            # 因素1：术语在文本中的出现次数
            count = text.lower().count(term.lower())
            score += count * 10

            # 因素2：术语长度（更长的通常更专业）
            score += len(term) * 2

            # 因素3：是否在知识库中（更可靠）
            if term in cls.TERM_KNOWLEDGE_BASE:
                score += 50

            # 因素4：是否为全大写缩写
            if re.match(r'^[A-Z]{2,}$', term):
                score += 20

            # 因素5：数据库权重（如果有）
            if 'weight' in info:
                score += info['weight'] * 2  # 数据库权重乘以2

            info['_score'] = score

        # 按分数排序
        sorted_terms = sorted(unique_map.values(), key=lambda x: x.get('_score', 0), reverse=True)

        # 移除分数字段和weight字段
        for term in sorted_terms:
            term.pop('_score', None)
            term.pop('weight', None)  # 移除内部weight字段

        return sorted_terms


def create_ai_extraction_prompt(text: str) -> str:
    """
    创建用于LLM提取学术术语的提示词 - 基于智能判断的版本

    Args:
        text: 输入文本

    Returns:
        str: 提示词
    """
    prompt = f"""你是一位专业的学术术语识别助手。你的任务是从文本中**尽可能多地提取**具有专业性和学术性的术语。

## 📄 待分析文本

{text}

---

## 🎯 提取原则

**核心原则**: 宽松识别，倾向于多提取而非漏掉。如果一个词有一定的专业性或技术性，就应该提取。

### ✅ 应该提取的术语类型：

1. **明确的专业术语**: 如"量子纠缠"、"神经网络"、"傅里叶变换"
2. **技术概念**: 如"分布式系统"、"数据库索引"、"API接口"
3. **学科名称**: 如"机器学习"、"量子物理"、"认知心理学"
4. **方法论**: 如"深度学习"、"回归分析"、"实验设计"
5. **专有技术**: 如"Transformer"、"BERT"、"ResNet"
6. **算法名称**: 如"快速排序"、"梯度下降"、"动态规划"
7. **理论框架**: 如"博弈论"、"进化论"、"相对论"
8. **技术标准**: 如"RESTful"、"TCP/IP"、"OAuth"
9. **专业工具**: 如"TensorFlow"、"PyTorch"、"Docker"
10. **专业现象**: 如"过拟合"、"光合作用"、"黑洞"

### ❌ 仍应排除的词（仅排除明显的非术语）：

1. **纯粹形容词**: "重要的"、"复杂的"、"简单的"
2. **日常动词**: "使用"、"处理"、"分析"
3. **极度通用词**: "问题"、"方法"、"情况"、"内容"

---

## 💡 示例对照

### ✅ 应该提取（采用宽松标准）：

| 术语 | 为什么提取 |
|------|-----------|
| 神经网络 | 专业技术概念 |
| 机器学习 | 学科名称 |
| 深度学习 | 专业方法 |
| 数据库 | 技术领域 |
| 算法 | 专业概念 |
| Transformer | 专有架构 |
| API | 技术标准 |
| 过拟合 | 专业现象 |
| 卷积层 | 技术组件 |
| 优化器 | 专业工具 |
| 分布式系统 | 技术架构 ✅ (即使有"系统"也提取，因为整体是专业概念) |
| 数据预处理 | 专业步骤 ✅ (即使是组合词，但在技术领域有特定含义) |
| 梯度下降 | 算法名称 |
| 反向传播 | 专业技术 |
| 注意力机制 | 技术机制 |

### ❌ 应该排除（仅限明显非术语）：

| 词语 | 为什么排除 |
|------|-----------|
| 重要的 | 纯形容词 |
| 进行处理 | 日常动词短语 |
| 主要问题 | 过于通用 |
| 基本概念 | 太宽泛 |

---

## 📋 输出格式

提取**尽可能多**的学术术语，严格按照以下JSON数组格式输出：

```json
[
  {{
    "term": "术语名称（中文或英文）",
    "definition": "简明定义（15-50字）",
    "category": "所属领域",
    "example": "应用示例或补充说明"
  }}
]
```

---

## ✅ 质量要求

1. **宽松提取**: 倾向于**多提取**而非遗漏，如果有疑问就提取
2. **完整覆盖**: 提取文本中所有可能的专业术语
3. **准确定义**: 定义要准确，但不必过度严格
4. **全领域开放**: 任何学科领域的术语都应识别

**重要**: 如果一个词在某个专业领域有特定含义，即使它看起来像组合词或通用词，也应该提取。例如：
- "数据挖掘" → ✅ 提取（数据科学专业术语）
- "云计算" → ✅ 提取（计算领域专业术语）
- "人工智能" → ✅ 提取（学科名称）

---

请**积极提取**文本中所有具有专业性的术语。直接返回JSON数组，不要任何其他文字说明。"""

    return prompt
