<!--
  QuickActionButton Component

  Reusable button for quick actions in the chat input area.
-->
<template>
  <button
    type="button"
    class="flex items-center gap-1 px-3 py-1.5 rounded-md border transition-colors text-xs theme-transition relative"
    :class="{ 'animate-pulse': isActive }"
    :style="buttonStyle"
    @click="$emit('click')"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
  >
    <i
      class="fa"
      :class="icon"
      :style="iconStyle"
    ></i>
    <span>{{ label }}</span>

    <!-- Badge -->
    <span
      v-if="badge"
      class="badge"
      :style="badgeStyle"
    >
      {{ badge }}
    </span>
  </button>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  icon: {
    type: String,
    required: true
  },
  label: {
    type: String,
    required: true
  },
  isDark: {
    type: Boolean,
    default: false
  },
  isActive: {
    type: Boolean,
    default: false
  },
  activeColor: {
    type: String,
    default: null
  },
  badge: {
    type: [Number, String],
    default: null
  }
})

const emit = defineEmits(['click'])

const isHovered = ref(false)

// Button style based on state
const buttonStyle = computed(() => {
  if (props.isActive && props.activeColor) {
    return {
      borderColor: props.activeColor,
      color: props.activeColor,
      backgroundColor: props.isDark
        ? `rgba(${hexToRgb(props.activeColor)}, 0.1)`
        : `rgba(${hexToRgb(props.activeColor)}, 0.05)`
    }
  }

  if (isHovered.value) {
    return props.isDark
      ? {
          borderColor: '#4B5563',
          color: '#F9FAFB',
          backgroundColor: '#374151'
        }
      : {
          borderColor: '#D1D5DB',
          color: '#374151',
          backgroundColor: '#F3F4F6'
        }
  }

  return props.isDark
    ? {
        borderColor: '#4B5563',
        color: '#F9FAFB',
        backgroundColor: 'transparent'
      }
    : {
        borderColor: '#D1D5DB',
        color: '#374151',
        backgroundColor: 'transparent'
      }
})

// Icon style
const iconStyle = computed(() => {
  if (props.isActive && props.activeColor) {
    return { color: props.activeColor }
  }

  return {
    color: isHovered.value
      ? props.isDark ? '#F9FAFB' : '#374151'
      : props.isDark ? '#F9FAFB' : '#374151'
  }
})

function handleMouseEnter() {
  if (!props.isActive) {
    isHovered.value = true
  }
}

function handleMouseLeave() {
  isHovered.value = false
}

/**
 * Convert hex color to RGB
 * @param {string} hex - Hex color code
 * @returns {string} RGB values as comma-separated string
 */
function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result
    ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}`
    : '0, 0, 0'
}

// Badge style
const badgeStyle = computed(() => ({
  backgroundColor: '#EF4444',
  color: '#FFFFFF'
}))
</script>

<style scoped>
.badge {
  position: absolute;
  top: -6px;
  right: -6px;
  min-width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 9px;
  font-size: 10px;
  font-weight: 600;
  padding: 0 5px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}
</style>
