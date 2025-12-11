/**
 * Title Generator Service
 *
 * Handles intelligent title generation for chat conversations.
 * Uses AI API when available, falls back to smart extraction algorithms.
 */

import storage from './storage.service'

class TitleGeneratorService {
  /**
   * Generate a smart title for a chat conversation
   * @param {string} userMessage - The user's message
   * @param {string} aiResponse - The AI's response
   * @returns {Promise<string>} Generated title (4-12 characters)
   */
  async generateTitle(userMessage, aiResponse) {
    try {
      const savedConfig = storage.get('api-configuration')

      if (!savedConfig) {
        console.warn('[TitleGenerator] No API configuration found, using smart extraction')
        return this.extractSmartTitle(aiResponse)
      }

      const apiKey = savedConfig.apiKey || savedConfig.openaiApiKey
      const baseUrl = savedConfig.baseUrl || 'https://api.openai.com/v1'

      if (!apiKey) {
        console.warn('[TitleGenerator] No API key found, using smart extraction')
        return this.extractSmartTitle(aiResponse)
      }

      // Try to generate title using AI
      const aiTitle = await this.generateWithAI(aiResponse, apiKey, baseUrl, savedConfig)

      if (this.isValidTitle(aiTitle)) {
        console.log('[TitleGenerator] Using AI-generated title:', aiTitle)
        return aiTitle
      }

      // Fallback to smart extraction
      console.warn('[TitleGenerator] AI title invalid, using smart extraction')
      return this.extractSmartTitle(aiResponse)

    } catch (error) {
      console.error('[TitleGenerator] Error generating title:', error)
      return this.extractSmartTitle(aiResponse)
    }
  }

  /**
   * Generate title using AI API
   * @private
   */
  async generateWithAI(aiResponse, apiKey, baseUrl, config) {
    const prompt = this.buildPrompt(aiResponse)

    const response = await fetch(`${baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: config.model || 'gpt-3.5-turbo',
        messages: [{
          role: 'user',
          content: prompt
        }],
        temperature: 0.3,
        max_tokens: 20
      })
    })

    if (!response.ok) {
      throw new Error(`API returned ${response.status}`)
    }

    const data = await response.json()
    let title = data.choices[0].message.content.trim()

    return this.cleanTitle(title)
  }

  /**
   * Build the prompt for AI title generation
   * @private
   */
  buildPrompt(aiResponse) {
    return `Analyze the following AI response and extract a SPECIFIC, MEANINGFUL title.

AI Response:
${aiResponse.substring(0, 600)}

Task: Generate a 4-8 character Chinese title that captures the SPECIFIC TOPIC or SUBJECT.

CRITICAL REQUIREMENTS:
1. MUST include concrete entities (product names, concepts, technologies, etc.)
2. AVOID generic words like: "Chat", "讨论", "分析", "问题", "咨询"
3. Focus on WHAT is being discussed, not HOW it's discussed
4. Identify the domain/category and key subject

Examples of GOOD titles:
- AI response about Python programming → "Python开发"
- AI response about Q3 sales data → "Q3销售分析"
- AI response about machine learning optimization → "模型优化"
- AI response about resume improvement → "简历修改"
- AI response about React hooks usage → "React Hooks"
- AI response about RAG system architecture → "RAG架构"
- AI response about database design → "数据库设计"

Examples of BAD titles (NEVER generate these):
- "Chat分析" ❌ (too generic)
- "文档讨论" ❌ (no specific topic)
- "用户咨询" ❌ (meaningless)
- "问题回答" ❌ (meta-reference)

EXTRACTION STRATEGY:
1. Identify main subject/entity (e.g., "Python", "机器学习", "销售数据")
2. Identify action/category (e.g., "开发", "优化", "分析")
3. Combine: [Subject] + [Action/Category] OR just [Specific Subject]

Output ONLY the title (4-8 characters, Chinese preferred):`
  }

  /**
   * Clean and normalize AI-generated title
   * @private
   */
  cleanTitle(title) {
    // Remove quotes
    title = title.replace(/^["'"""'']+|["'"""'']+$/g, '')

    // Remove colons and spaces
    title = title.replace(/^[：:：\s]+|[：:：\s]+$/g, '')

    // Remove common prefixes
    title = title.replace(/^(Title|Title|答案|回答|主题)[：:：\s]*/i, '')

    // Remove emoji
    title = title.replace(/[❌✅]/g, '')

    // Trim and limit length
    title = title.trim()
    if (title.length > 12) {
      title = title.substring(0, 12)
    }

    return title
  }

  /**
   * Validate if title is meaningful and not generic
   * @private
   */
  isValidTitle(title) {
    if (!title || title.length < 2 || title.length > 15) {
      return false
    }

    // Check for generic terms
    const genericTerms = [
      'Chat', '讨论', '分析', '问题', '咨询', '回答',
      '文档', 'Content', '用户', '新Chat'
    ]

    const isGeneric = genericTerms.some(term =>
      title === term ||
      title.includes(term + '分析') ||
      title.includes(term + '讨论')
    )

    return !isGeneric
  }

  /**
   * Extract title using pattern matching and heuristics
   * Fallback method when AI is unavailable
   * @private
   */
  extractSmartTitle(text) {
    // Remove markdown formatting and extra whitespace
    let cleaned = text
      .replace(/[#*`\[\]_>]/g, '')
      .replace(/\n+/g, ' ')
      .trim()

    // Pattern 1: "XXX是..." → extract "XXX"
    const pattern1 = cleaned.match(/^([^\s]{2,8})(是|为|指|表示|属于|包括|涉及)/)
    if (pattern1 && pattern1[1]) {
      const generic = ['Chat', '问题', '讨论', '分析', '文档', 'Content', '咨询', '回答']
      if (!generic.includes(pattern1[1])) {
        return pattern1[1]
      }
    }

    // Pattern 2: Technical terms (capitalized English)
    const techTerms = cleaned.match(/\b([A-Z][A-Za-z0-9]{1,7})\b/)
    if (techTerms && techTerms[1]) {
      const afterTech = cleaned.substring(cleaned.indexOf(techTerms[1]))
      const techContext = afterTech.match(/([A-Z][A-Za-z0-9]{1,7})(系统|架构|框架|接口|模型|平台|技术|开发|设计)/)

      if (techContext) {
        return (techContext[1] + techContext[2]).substring(0, 8)
      }
      return techTerms[1].substring(0, 8)
    }

    // Pattern 3: Domain-specific Chinese terms
    const domainTerms = cleaned.match(/([\u4e00-\u9fa5]{2,6})(技术|方法|系统|平台|框架|语言|工具|模型|算法|设计|开发|编程|优化|管理|策略|架构|接口|数据库|网络|安全)/)
    if (domainTerms && domainTerms[0]) {
      const term = domainTerms[0]
      const avoid = ['这个系统', '该技术', '这种方法', '该平台']
      if (!avoid.some(a => term.includes(a))) {
        return term.substring(0, 8)
      }
    }

    // Pattern 4: Entities with numbers
    const entityWithNumber = cleaned.match(/(Q[1-4]|第[一二三四]季度|[0-9]{4}年)[\s]*([\u4e00-\u9fa5]{2,4})/)
    if (entityWithNumber) {
      return (entityWithNumber[1] + entityWithNumber[2]).substring(0, 8)
    }

    // Pattern 5: First meaningful noun phrase
    const firstSentence = cleaned.split(/[。！？.!?]/)[0].trim()
    const fillers = [
      '是', '的', '了', '在', '有', '和', '与', '或', '但', '而',
      '因为', '所以', '可以', '能够', '通过', '让', '使',
      '这', '那', '该', '此'
    ]

    const words = firstSentence
      .split(/[\s,，、]/)
      .filter(w => w.length >= 2 && !fillers.includes(w))
      .filter(w => !/^(Chat|问题|讨论|分析|文档|咨询|回答)$/.test(w))

    if (words.length > 0) {
      // Prefer Chinese words or capitalized English
      const meaningfulWords = words.filter(w =>
        /[\u4e00-\u9fa5]/.test(w) || /^[A-Z]/.test(w)
      )

      if (meaningfulWords.length > 0) {
        // Try compound terms
        if (meaningfulWords.length >= 2) {
          const compound = meaningfulWords.slice(0, 2).join('')
          if (compound.length <= 8) {
            return compound
          }
        }
        return meaningfulWords[0].substring(0, 8)
      }
      return words[0].substring(0, 8)
    }

    // Last resort fallback
    const fallback = cleaned.substring(0, 6)
    if (/^(这是|这个|关于|Chat|问题)/.test(fallback)) {
      return '新Chat'
    }

    return fallback || '新Chat'
  }
}

// Create and export singleton instance
export const titleGenerator = new TitleGeneratorService()

// Export class for testing
export { TitleGeneratorService }

export default titleGenerator
