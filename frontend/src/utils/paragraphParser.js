/**
 * Paragraph Parser Utility
 *
 * 智能段落解析工具 - 将AI回复的HTMLContent分割成独立的段落
 */

/**
 * 解析HTMLContent为段落数组
 * @param {string} htmlContent - AI回复的HTMLContent
 * @param {Object} sourceMapping - 来源映射（可选）
 * @returns {Array} 段落对象数组
 */
export function parseHtmlToParagraphs(htmlContent, sourceMapping = null) {
  if (!htmlContent) return []

  // 创建临时DOM元素来解析HTML
  const tempDiv = document.createElement('div')
  tempDiv.innerHTML = htmlContent

  const paragraphs = []
  let paragraphIndex = 0

  // 遍历所有子节点
  const processNode = (node) => {
    // 处理段落标签
    if (node.nodeName === 'P') {
      const text = node.textContent.trim()
      if (text) {
        paragraphs.push({
          id: `para-${paragraphIndex++}`,
          html: node.outerHTML,
          text: text,
          source: getSourceInfo(text, sourceMapping)
        })
      }
    }
    // 处理div作为段落
    else if (node.nodeName === 'DIV') {
      const text = node.textContent.trim()
      if (text && !hasBlockChildren(node)) {
        paragraphs.push({
          id: `para-${paragraphIndex++}`,
          html: node.outerHTML,
          text: text,
          source: getSourceInfo(text, sourceMapping)
        })
      } else {
        // 递归处理子节点
        Array.from(node.childNodes).forEach(processNode)
      }
    }
    // 处理列表
    else if (node.nodeName === 'UL' || node.nodeName === 'OL') {
      const text = node.textContent.trim()
      if (text) {
        paragraphs.push({
          id: `para-${paragraphIndex++}`,
          html: node.outerHTML,
          text: text,
          source: getSourceInfo(text, sourceMapping)
        })
      }
    }
    // 处理代码块
    else if (node.nodeName === 'PRE') {
      const text = node.textContent.trim()
      if (text) {
        paragraphs.push({
          id: `para-${paragraphIndex++}`,
          html: node.outerHTML,
          text: text,
          source: getSourceInfo(text, sourceMapping),
          isCode: true
        })
      }
    }
    // 处理Title
    else if (/^H[1-6]$/.test(node.nodeName)) {
      const text = node.textContent.trim()
      if (text) {
        paragraphs.push({
          id: `para-${paragraphIndex++}`,
          html: node.outerHTML,
          text: text,
          source: getSourceInfo(text, sourceMapping),
          isHeading: true
        })
      }
    }
    // 处理blockquote
    else if (node.nodeName === 'BLOCKQUOTE') {
      const text = node.textContent.trim()
      if (text) {
        paragraphs.push({
          id: `para-${paragraphIndex++}`,
          html: node.outerHTML,
          text: text,
          source: getSourceInfo(text, sourceMapping)
        })
      }
    }
  }

  // 处理所有顶级节点
  Array.from(tempDiv.childNodes).forEach(processNode)

  // 如果没有找到段落，将整个Content作为一个段落
  if (paragraphs.length === 0 && htmlContent.trim()) {
    paragraphs.push({
      id: 'para-0',
      html: htmlContent,
      text: tempDiv.textContent.trim(),
      source: getSourceInfo(tempDiv.textContent.trim(), sourceMapping)
    })
  }

  return paragraphs
}

/**
 * 检查节点是否包含块级子元素
 * @param {HTMLElement} node - DOM节点
 * @returns {boolean}
 */
function hasBlockChildren(node) {
  const blockTags = ['P', 'DIV', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'UL', 'OL', 'PRE', 'BLOCKQUOTE']
  return Array.from(node.children).some(child => blockTags.includes(child.nodeName))
}

/**
 * 获取段落的来源Information
 * @param {string} text - 段落文本
 * @param {Object} sourceMapping - 来源映射
 * @returns {Object|null} 来源Information
 */
function getSourceInfo(text, sourceMapping) {
  if (!sourceMapping) return null

  // 如果sourceMapping是函数，调用它获取来源
  if (typeof sourceMapping === 'function') {
    return sourceMapping(text)
  }

  // 如果sourceMapping是对象，查找匹配的来源
  if (typeof sourceMapping === 'object') {
    // 简单匹配：查找文本片段
    for (const [key, value] of Object.entries(sourceMapping)) {
      if (text.includes(key)) {
        return value
      }
    }
  }

  return null
}

/**
 * 从AI回复中提取来源引用
 * @param {string} content - AI回复Content
 * @returns {Object} 来源映射
 */
export function extractSourceReferences(content) {
  const sourceMapping = {}

  // 匹配常见的引用格式
  // 格式1: [1] 或 [ref1]
  const bracketRefs = content.match(/\[(\d+|ref\w+)\]/g)
  if (bracketRefs) {
    bracketRefs.forEach(ref => {
      // 这里可以实现更复杂的引用解析逻辑
      sourceMapping[ref] = {
        documentName: '未知文档',
        page: '?',
        position: '引用 ' + ref
      }
    })
  }

  // 格式2: (来源: xxx)
  const sourceMatches = content.match(/\(来源[:：]\s*([^)]+)\)/g)
  if (sourceMatches) {
    sourceMatches.forEach(match => {
      const source = match.match(/\(来源[:：]\s*([^)]+)\)/)[1]
      sourceMapping[match] = {
        documentName: source,
        page: '?',
        position: '文中引用'
      }
    })
  }

  return sourceMapping
}

/**
 * 清理HTMLContent中的特殊标记
 * @param {string} html - HTMLContent
 * @returns {string} 清理后的HTML
 */
export function cleanHtmlContent(html) {
  if (!html) return ''

  return html
    // 移除引用标记（保留Content）
    .replace(/\[(\d+|ref\w+)\]/g, '')
    // 移除来源标注
    .replace(/\(来源[:：]\s*[^)]+\)/g, '')
    // 清理多余的空白
    .replace(/\s+/g, ' ')
    .trim()
}

/**
 * 高亮段落文本
 * @param {string} text - 原始文本
 * @param {string} searchTerm - Search词
 * @returns {string} 高亮后的HTML
 */
export function highlightText(text, searchTerm) {
  if (!searchTerm || !text) return text

  const regex = new RegExp(`(${escapeRegex(searchTerm)})`, 'gi')
  return text.replace(regex, '<mark class="highlight">$1</mark>')
}

/**
 * 转义正则表达式特殊字符
 * @param {string} str - 字符串
 * @returns {string} 转义后的字符串
 */
function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/**
 * 获取段落摘要
 * @param {string} text - 段落文本
 * @param {number} maxLength - 最大长度
 * @returns {string} 摘要文本
 */
export function getParagraphSummary(text, maxLength = 100) {
  if (!text) return ''

  if (text.length <= maxLength) return text

  return text.substring(0, maxLength).trim() + '...'
}

/**
 * 检测段落Type
 * @param {string} html - HTMLContent
 * @returns {string} 段落Type
 */
export function detectParagraphType(html) {
  if (!html) return 'text'

  if (/<pre|<code/.test(html)) return 'code'
  if (/<h[1-6]/.test(html)) return 'heading'
  if (/<ul|<ol|<li/.test(html)) return 'list'
  if (/<blockquote/.test(html)) return 'quote'
  if (/<table/.test(html)) return 'table'

  return 'text'
}
