<template>
  <div class="demo-page" :style="pageStyle">
    <div class="demo-container">
      <!-- Top control bar -->
      <div class="demo-header" :style="headerStyle">
        <h1 class="demo-title">AI Reply Interaction System Demo</h1>
        <div class="controls">
          <button
            class="theme-toggle"
            :style="toggleStyle"
            @click="toggleTheme"
          >
            <i :class="isDark ? 'fa fa-sun-o' : 'fa fa-moon-o'"></i>
            <span>{{ isDark ? 'Light Mode' : 'Dark Mode' }}</span>
          </button>
        </div>
      </div>

      <!-- Feature description -->
      <div class="feature-info" :style="infoStyle">
        <h2 class="info-title">
          <i class="fa fa-info-circle"></i>
          Features
        </h2>
        <ul class="feature-list">
          <li>
            <i class="fa fa-check-circle"></i>
            <strong>Copy按钮：</strong>一键CopyAI回复Content
          </li>
          <li>
            <i class="fa fa-check-circle"></i>
            <strong>Regenerate：</strong>在原位置Regenerate回答
          </li>
          <li>
            <i class="fa fa-check-circle"></i>
            <strong>提取学术词：</strong>智能识别并展示专业术语
          </li>
          <li>
            <i class="fa fa-check-circle"></i>
            <strong>术语Search：</strong>快速查找特定术语
          </li>
          <li>
            <i class="fa fa-check-circle"></i>
            <strong>术语收藏：</strong>标记重要术语到个人词库
          </li>
        </ul>
      </div>

      <!-- 消息列表 -->
      <div class="messages-section" :style="messagesStyle">
        <h2 class="section-title">Chat示例</h2>
        <div class="messages-container">
          <ChatMessage
            v-for="message in demoMessages"
            :key="message.id"
            :message="message"
            :is-dark="isDark"
            @regenerate="handleRegenerate"
            @show-history="handleShowHistory"
          />
        </div>
      </div>

      <!-- 快速ActionsTips -->
      <div class="quick-tips" :style="tipsStyle">
        <h3 class="tips-title">
          <i class="fa fa-lightbulb-o"></i>
          快速Tips
        </h3>
        <div class="tips-grid">
          <div class="tip-card" :style="tipCardStyle">
            <i class="fa fa-mouse-pointer tip-icon"></i>
            <p>点击任意AI回复下方的"提取学术词"查看术语词典</p>
          </div>
          <div class="tip-card" :style="tipCardStyle">
            <i class="fa fa-star tip-icon"></i>
            <p>在术语词典中点击星标收藏重要术语</p>
          </div>
          <div class="tip-card" :style="tipCardStyle">
            <i class="fa fa-search tip-icon"></i>
            <p>使用Search框快速定位特定术语</p>
          </div>
          <div class="tip-card" :style="tipCardStyle">
            <i class="fa fa-download tip-icon"></i>
            <p>Export术语为PDF方便Offline学习</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import ChatMessage from '@/components/dashboard/ChatMessage.vue'

// 主题Status
const isDark = ref(false)

// 切换主题
const toggleTheme = () => {
  isDark.value = !isDark.value
}

// 演示消息数据
const demoMessages = ref([
  {
    id: 'demo-1',
    sender: 'user',
    content: '请介绍一下机器学习的基本概念和Apply',
    timestamp: new Date(Date.now() - 120000)
  },
  {
    id: 'demo-2',
    sender: 'ai',
    content: `# 机器学习简介

机器学习(Machine Learning)是人工智能的一个重要分支,它使计算机系统能够从数据中自动学习和改进,而无需明确编程。

## 核心概念

### 1. 监督学习
在监督学习中,我们使用标记的训练数据来训练模型。常见Apply包括:
- 图像分类
- Speech Recognition
- 垃圾邮件Filter

### 2. 非监督学习
非监督学习处理未标记的数据,寻找隐藏的模式。主要技术包括:
- 聚类分析
- 降维技术
- 异常检测

### 3. 强化学习
通过与环境交互学习最优策略,广泛Apply于:
- 游戏AI
- 机器人控制
- 推荐系统

## 关键技术

**神经网络**: 模仿人脑结构的计算模型,特别是深度神经网络在图像和语音处理方面取得了突破性进展。

**梯度下降**: 优化算法的核心,通过迭代调整参数来最小化损失函数。

**正则化**: 防止过拟合的重要技术,如L1、L2正则化和Dropout。

## 实际Apply

1. **医疗诊断**: 辅助医生识别疾病
2. **金融风控**: 信用评分和欺诈检测
3. **自动驾驶**: 环境感知和决策
4. **自然语言处理**: 机器翻译和文本生成

机器学习正在深刻改变我们的生活和工作方式。`,
    timestamp: new Date(Date.now() - 60000)
  },
  {
    id: 'demo-3',
    sender: 'user',
    content: '深度学习和传统机器学习有什么区别？',
    timestamp: new Date(Date.now() - 30000)
  },
  {
    id: 'demo-4',
    sender: 'ai',
    content: `深度学习与传统机器学习的主要区别:

## 1. 特征工程

**传统机器学习**: 需要人工设计和提取特征,依赖领域专家知识。

**深度学习**: 自动学习特征表示,减少人工干预。

## 2. 数据需求

**传统机器学习**:
- 适用于小到中等规模数据集
- 特征质量比Count更重要

**深度学习**:
- 需要大量标注数据
- 数据量越大,性能提升越明显

## 3. 计算资源

**传统机器学习**: 计算资源需求较低,可在普通CPU上运行。

**深度学习**: 通常需要GPU加速,训练时间较长。

## 4. 可解释性

**传统机器学习**: 模型相对简单,决策过程更透明。

**深度学习**: 作为"黑盒"模型,解释性较差,但性能更强。

两者各有优势,实际Apply中需根据具体场景选择。`,
    timestamp: new Date()
  }
])

// 事件处理
const handleRegenerate = async (message) => {
  ElMessage.info('正在Regenerate回复...')
  // 模拟Regenerate
  await new Promise(resolve => setTimeout(resolve, 1500))
  ElMessage.success('回复已Regenerate')
}

const handleShowHistory = (message) => {
  ElMessage.info(`查看消息 ${message.id} 的历史版本`)
}

// 样式计算
const pageStyle = computed(() => ({
  backgroundColor: isDark.value ? '#111827' : '#F9FAFB',
  color: isDark.value ? '#F9FAFB' : '#1F2937',
  minHeight: '100vh',
  transition: 'all 0.3s ease'
}))

const headerStyle = computed(() => ({
  backgroundColor: isDark.value ? '#1F2937' : '#FFFFFF',
  borderColor: isDark.value ? '#374151' : '#E5E7EB',
  boxShadow: isDark.value
    ? '0 1px 3px rgba(0, 0, 0, 0.3)'
    : '0 1px 3px rgba(0, 0, 0, 0.1)'
}))

const toggleStyle = computed(() => ({
  backgroundColor: isDark.value ? '#374151' : '#F3F4F6',
  color: isDark.value ? '#F9FAFB' : '#1F2937'
}))

const infoStyle = computed(() => ({
  backgroundColor: isDark.value ? '#1F2937' : '#FFFFFF',
  borderColor: isDark.value ? '#374151' : '#E5E7EB'
}))

const messagesStyle = computed(() => ({
  backgroundColor: isDark.value ? '#1F2937' : '#FFFFFF',
  borderColor: isDark.value ? '#374151' : '#E5E7EB'
}))

const tipsStyle = computed(() => ({
  backgroundColor: isDark.value ? '#1F2937' : '#FFFFFF',
  borderColor: isDark.value ? '#374151' : '#E5E7EB'
}))

const tipCardStyle = computed(() => ({
  backgroundColor: isDark.value ? '#374151' : '#F9FAFB',
  borderColor: isDark.value ? '#4B5563' : '#E5E7EB'
}))
</script>

<style scoped>
.demo-page {
  padding: 20px;
}

.demo-container {
  max-width: 1200px;
  margin: 0 auto;
}

/* Top control bar */
.demo-header {
  padding: 24px;
  border-radius: 12px;
  border: 1px solid;
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.demo-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0;
}

.controls {
  display: flex;
  gap: 12px;
}

.theme-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.theme-toggle:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Feature description */
.feature-info {
  padding: 24px;
  border-radius: 12px;
  border: 1px solid;
  margin-bottom: 24px;
}

.info-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 16px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-title i {
  color: #3B82F6;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 12px;
}

.feature-list li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 15px;
  line-height: 1.6;
}

.feature-list i {
  color: #22C55E;
  font-size: 18px;
  flex-shrink: 0;
  margin-top: 2px;
}

/* 消息区域 */
.messages-section {
  padding: 24px;
  border-radius: 12px;
  border: 1px solid;
  margin-bottom: 24px;
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 20px 0;
}

.messages-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 快速Tips */
.quick-tips {
  padding: 24px;
  border-radius: 12px;
  border: 1px solid;
}

.tips-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 16px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.tips-title i {
  color: #F59E0B;
}

.tips-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.tip-card {
  padding: 16px;
  border-radius: 8px;
  border: 1px solid;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 12px;
  transition: all 0.2s;
}

.tip-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.tip-icon {
  font-size: 32px;
  color: #3B82F6;
}

.tip-card p {
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .demo-page {
    padding: 12px;
  }

  .demo-header {
    padding: 16px;
  }

  .demo-title {
    font-size: 22px;
  }

  .feature-info,
  .messages-section,
  .quick-tips {
    padding: 16px;
  }

  .tips-grid {
    grid-template-columns: 1fr;
  }
}
</style>
