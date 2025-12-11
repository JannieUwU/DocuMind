/**
 * 文件上传Status管理
 * 支持批量上传、进度跟踪、文件管理
 */
import { ref, computed } from 'vue'
import axios from 'axios'

export interface UploadFile {
  id: string
  file: File
  name: string
  size: number
  status: 'pending' | 'uploading' | 'success' | 'error'
  progress: number
  error?: string
  conversationId?: number
}

const uploadQueue = ref<UploadFile[]>([])
const isUploading = ref(false)
const currentUploadingFile = ref<UploadFile | null>(null)

export function useFileUpload() {
  /**
   * 验证File Type - 只允许 PDF
   */
  const validateFileType = (file: File): boolean => {
    const validTypes = ['application/pdf']
    const validExtensions = ['.pdf']

    const isValidMimeType = validTypes.includes(file.type)
    const isValidExtension = validExtensions.some(ext =>
      file.name.toLowerCase().endsWith(ext)
    )

    return isValidMimeType || isValidExtension
  }

  /**
   * 格式化File Size
   */
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  /**
   * 添加文件到上传队列
   */
  const addFiles = (files: FileList | File[], conversationId?: number): {
    added: number
    rejected: { file: File, reason: string }[]
  } => {
    const filesArray = Array.from(files)
    const rejected: { file: File, reason: string }[] = []
    let added = 0

    filesArray.forEach(file => {
      // 验证File Type
      if (!validateFileType(file)) {
        rejected.push({
          file,
          reason: `只支持 PDF 文件 (当前: ${file.name})`
        })
        return
      }

      // 验证File Size (50MB)
      const maxSize = 50 * 1024 * 1024
      if (file.size > maxSize) {
        rejected.push({
          file,
          reason: `文件过大 (最大 50MB): ${file.name}`
        })
        return
      }

      // 检查是否已存在
      const exists = uploadQueue.value.some(item =>
        item.name === file.name && item.size === file.size
      )
      if (exists) {
        rejected.push({
          file,
          reason: `文件已存在: ${file.name}`
        })
        return
      }

      // 添加到队列
      const uploadFile: UploadFile = {
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        file,
        name: file.name,
        size: file.size,
        status: 'pending',
        progress: 0,
        conversationId
      }

      uploadQueue.value.push(uploadFile)
      added++
    })

    return { added, rejected }
  }

  /**
   * 移除文件
   */
  const removeFile = (fileId: string) => {
    const index = uploadQueue.value.findIndex(f => f.id === fileId)
    if (index !== -1) {
      const file = uploadQueue.value[index]

      // 如果Uploading，不允许Delete
      if (file.status === 'uploading') {
        return false
      }

      uploadQueue.value.splice(index, 1)
      return true
    }
    return false
  }

  /**
   * Clear队列
   */
  const clearQueue = (statusFilter?: UploadFile['status']) => {
    if (statusFilter) {
      uploadQueue.value = uploadQueue.value.filter(f => f.status !== statusFilter)
    } else {
      // 只清除非上传中的文件
      uploadQueue.value = uploadQueue.value.filter(f => f.status === 'uploading')
    }
  }

  /**
   * 上传单个文件
   */
  const uploadSingleFile = async (uploadFile: UploadFile): Promise<boolean> => {
    const token = localStorage.getItem('token')
    if (!token) {
      uploadFile.status = 'error'
      uploadFile.error = '未Login，Please login first'
      return false
    }

    try {
      uploadFile.status = 'uploading'
      uploadFile.progress = 0
      currentUploadingFile.value = uploadFile

      const formData = new FormData()
      formData.append('file', uploadFile.file)

      if (uploadFile.conversationId) {
        formData.append('conversation_id', uploadFile.conversationId.toString())
      }

      const response = await axios.post(
        '/api/documents/upload',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
            'Authorization': `Bearer ${token}`
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              uploadFile.progress = Math.round(
                (progressEvent.loaded * 100) / progressEvent.total
              )
            }
          },
          timeout: 300000 // 5分钟超时
        }
      )

      if (response.data.success) {
        uploadFile.status = 'success'
        uploadFile.progress = 100
        return true
      } else {
        throw new Error(response.data.message || 'Upload failed')
      }
    } catch (error: any) {
      uploadFile.status = 'error'
      uploadFile.error = error.response?.data?.detail || error.message || 'Upload failed'
      return false
    } finally {
      currentUploadingFile.value = null
    }
  }

  /**
   * 批量上传所有待Upload File
   */
  const uploadAll = async (): Promise<{
    success: number
    failed: number
    total: number
  }> => {
    const pendingFiles = uploadQueue.value.filter(f => f.status === 'pending')

    if (pendingFiles.length === 0) {
      return { success: 0, failed: 0, total: 0 }
    }

    isUploading.value = true
    let successCount = 0
    let failedCount = 0

    for (const file of pendingFiles) {
      const success = await uploadSingleFile(file)
      if (success) {
        successCount++
      } else {
        failedCount++
      }
    }

    isUploading.value = false

    return {
      success: successCount,
      failed: failedCount,
      total: pendingFiles.length
    }
  }

  /**
   * 重试Failed的文件
   */
  const retryFailed = async () => {
    const failedFiles = uploadQueue.value.filter(f => f.status === 'error')

    for (const file of failedFiles) {
      file.status = 'pending'
      file.error = undefined
      file.progress = 0
    }

    return uploadAll()
  }

  // Computed properties
  const pendingFiles = computed(() =>
    uploadQueue.value.filter(f => f.status === 'pending')
  )

  const uploadingFiles = computed(() =>
    uploadQueue.value.filter(f => f.status === 'uploading')
  )

  const successFiles = computed(() =>
    uploadQueue.value.filter(f => f.status === 'success')
  )

  const errorFiles = computed(() =>
    uploadQueue.value.filter(f => f.status === 'error')
  )

  const totalProgress = computed(() => {
    if (uploadQueue.value.length === 0) return 0

    const total = uploadQueue.value.reduce((sum, file) => sum + file.progress, 0)
    return Math.round(total / uploadQueue.value.length)
  })

  const hasFiles = computed(() => uploadQueue.value.length > 0)

  const canUpload = computed(() =>
    pendingFiles.value.length > 0 && !isUploading.value
  )

  return {
    // State
    uploadQueue,
    isUploading,
    currentUploadingFile,

    // Computed
    pendingFiles,
    uploadingFiles,
    successFiles,
    errorFiles,
    totalProgress,
    hasFiles,
    canUpload,

    // Methods
    validateFileType,
    formatFileSize,
    addFiles,
    removeFile,
    clearQueue,
    uploadSingleFile,
    uploadAll,
    retryFailed
  }
}
