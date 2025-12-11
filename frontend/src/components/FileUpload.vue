<template>
  <ClientOnly>
    <div
      :class="cn('w-full', $props.class)"
      @dragover.prevent="handleEnter"
      @dragleave="handleLeave"
      @drop.prevent="handleDrop"
      @mouseover="handleEnter"
      @mouseleave="handleLeave"
    >
      <div
        class="group/file relative block w-full cursor-pointer overflow-hidden rounded-lg p-10"
        @click="handleClick"
      >
        <input
          ref="fileInputRef"
          type="file"
          accept=".pdf"
          multiple
          class="hidden"
          @change="onFileChange"
        />

        <!-- Grid pattern -->
        <div
          class="pointer-events-none absolute inset-0 [mask-image:radial-gradient(ellipse_at_center,white,transparent)]"
        >
          <slot />
        </div>

        <!-- Content -->
        <div class="flex flex-col items-center justify-center">
          <p
            class="relative z-20 font-sans text-base font-bold text-neutral-700 dark:text-gray-100"
          >
            Upload PDF files
          </p>
          <p
            class="relative z-20 mt-2 font-sans text-base font-normal text-neutral-400 dark:text-gray-300"
          >
            Drag or drop your PDF files here or click to upload
          </p>
          <p
            class="relative z-20 mt-1 font-sans text-sm font-normal text-neutral-400 dark:text-gray-400"
          >
            Supports multiple files, max 50MB each
          </p>

          <div class="relative mx-auto mt-10 w-full max-w-xl space-y-4">
            <Motion
              v-for="(file, idx) in files"
              :key="`file-${idx}`"
              :initial="{ opacity: 0, scaleX: 0 }"
              :animate="{ opacity: 1, scaleX: 1 }"
              class="relative z-40 mx-auto flex w-full flex-col items-start justify-start overflow-hidden rounded-md bg-white p-4 shadow-sm md:h-24 dark:bg-neutral-900"
            >
              <div class="flex w-full items-center justify-between gap-4">
                <div class="flex items-center gap-2 flex-1 min-w-0">
                  <i class="fa fa-file-pdf-o text-red-500 text-xl flex-shrink-0"></i>
                  <Motion
                    as="p"
                    :initial="{ opacity: 0 }"
                    :animate="{ opacity: 1 }"
                    class="flex-1 truncate text-base text-neutral-700 dark:text-gray-100"
                  >
                    {{ file.name }}
                  </Motion>
                </div>
                <div class="flex items-center gap-2 flex-shrink-0">
                  <Motion
                    as="p"
                    :initial="{ opacity: 0 }"
                    :animate="{ opacity: 1 }"
                    class="w-fit rounded-lg px-2 py-1 text-sm text-neutral-600 shadow-input dark:bg-gray-800 dark:text-gray-100"
                  >
                    {{ (file.size / (1024 * 1024)).toFixed(2) }} MB
                  </Motion>
                  <button
                    @click.stop="removeFile(idx)"
                    class="w-6 h-6 flex items-center justify-center rounded-full hover:bg-red-100 dark:hover:bg-red-900 text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
                    title="Remove file"
                  >
                    <i class="fa fa-times text-sm"></i>
                  </button>
                </div>
              </div>

              <div
                class="mt-2 flex w-full flex-col items-start justify-between text-sm text-neutral-600 md:flex-row md:items-center dark:text-gray-300"
              >
                <Motion
                  as="p"
                  :initial="{ opacity: 0 }"
                  :animate="{ opacity: 1 }"
                  class="rounded-md bg-gray-100 px-1.5 py-1 text-sm dark:bg-gray-800 dark:text-gray-100"
                >
                  {{ file.type || "application/pdf" }}
                </Motion>
                <Motion
                  as="p"
                  :initial="{ opacity: 0 }"
                  :animate="{ opacity: 1 }"
                  class="dark:text-gray-300"
                >
                  modified {{ new Date(file.lastModified).toLocaleDateString() }}
                </Motion>
              </div>
            </Motion>

            <template v-if="!files.length">
              <Motion
                as="div"
                class="relative z-40 mx-auto mt-4 flex h-32 w-full max-w-32 items-center justify-center rounded-md shadow-[0px_10px_50px_rgba(0,0,0,0.1)] group-hover/file:shadow-2xl theme-transition"
                :style="isDark ? { backgroundColor: '#1F2937' } : { backgroundColor: '#FFFFFF' }"
                :initial="{
                  x: 0,
                  y: 0,
                  opacity: 1,
                }"
                :transition="{
                  type: 'spring',
                  stiffness: 300,
                  damping: 20,
                }"
                :animate="
                  isActive
                    ? {
                        x: 20,
                        y: -20,
                        opacity: 0.9,
                      }
                    : {}
                "
              >
                <i
                  class="fa fa-upload text-xl theme-transition"
                  :style="isDark ? { color: '#D1D5DB' } : { color: '#4B5563' }"
                ></i>
              </Motion>

              <div
                class="absolute inset-0 z-30 mx-auto mt-4 flex h-32 w-full max-w-32 items-center justify-center rounded-md border border-dashed bg-transparent transition-opacity theme-transition"
                :class="{ 'opacity-100': isActive, 'opacity-0': !isActive }"
                :style="isDark ? { borderColor: '#60A5FA' } : { borderColor: '#38BDF8' }"
              ></div>
            </template>
          </div>
        </div>
      </div>
    </div>
  </ClientOnly>
</template>

<script setup>
import { cn } from '@/utils/cn.js'
import { Motion } from 'motion-v'
import { ref, computed, onMounted } from 'vue'
import { themeManager } from '@/utils/theme'
import { ElMessage } from 'element-plus'

const props = defineProps({
  class: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['onChange'])

const fileInputRef = ref(null)
const files = ref([])
const isActive = ref(false)

// 检测当前主题
const currentTheme = ref(themeManager.getCurrentTheme())
const isDark = computed(() => currentTheme.value === 'dark')

// 监听主题变化
onMounted(() => {
  currentTheme.value = themeManager.getCurrentTheme()
  window.addEventListener('themechange', (event) => {
    currentTheme.value = event.detail
  })
})

// 验证File Type和Size
function validateFile(file) {
  // 检查File Type
  const isValidType = file.name.toLowerCase().endsWith('.pdf') || file.type === 'application/pdf'
  if (!isValidType) {
    ElMessage.error(`Only PDF files are supported! (${file.name})`)
    return false
  }

  // 检查File Size (50MB)
  const maxSize = 50 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error(`File too large! Max size is 50MB (${file.name})`)
    return false
  }

  // 检查是否已存在
  const exists = files.value.some(f => f.name === file.name && f.size === file.size)
  if (exists) {
    ElMessage.warning(`File already added: ${file.name}`)
    return false
  }

  return true
}

function handleFileChange(newFiles) {
  const validFiles = newFiles.filter(file => validateFile(file))

  if (validFiles.length > 0) {
    files.value = [...files.value, ...validFiles]
    emit('onChange', files.value)

    if (validFiles.length > 1) {
      ElMessage.success(`${validFiles.length} PDF files added successfully`)
    }
  }
}

function onFileChange(e) {
  const input = e.target
  if (!input.files) return
  handleFileChange(Array.from(input.files))
  // Clear input，允许重复选择相同文件
  input.value = ''
}

function handleClick() {
  fileInputRef.value?.click()
}

function handleEnter() {
  isActive.value = true
}

function handleLeave() {
  isActive.value = false
}

function handleDrop(e) {
  isActive.value = false
  const droppedFiles = e.dataTransfer?.files ? Array.from(e.dataTransfer.files) : []
  if (droppedFiles.length) handleFileChange(droppedFiles)
}

function removeFile(index) {
  const removedFile = files.value[index]
  files.value.splice(index, 1)
  emit('onChange', files.value)
  ElMessage.info(`Removed: ${removedFile.name}`)
}
</script>

<style scoped>
.group-hover\/file\:shadow-2xl:hover {
  box-shadow: 0px 10px 20px rgba(0, 0, 0, 0.25);
}

.transition-opacity {
  transition: opacity 0.3s ease;
}

/* 确保暗色模式下文字可见 */
.dark .relative.z-20 {
  color: var(--text-primary);
}

.dark .relative.z-20.font-normal {
  color: var(--text-secondary);
}
</style>