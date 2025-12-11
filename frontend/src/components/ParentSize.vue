<template>
  <div
    ref="target"
    :style="mergedStyles"
    class="w-full h-full"
    v-bind="attrsWithoutClassAndStyle"
  >
    <slot />
  </div>
</template>

<script setup>
import { ref, computed, useAttrs } from "vue";
import { useDebounceFn, useResizeObserver } from "@vueuse/core";

const props = defineProps({
  class: String,
  debounceTime: {
    type: Number,
    default: 300,
  },
  ignoreDimensions: {
    type: [Array, String],
    default: () => [],
  },
  parentSizeStyles: Object,
  enableDebounceLeadingCall: {
    type: Boolean,
    default: true,
  },
});

const attrs = useAttrs();
const target = ref(null);
const state = ref({
  width: 0,
  height: 0,
  top: 0,
  left: 0,
});

const mergedStyles = computed(() => ({
  ...props.parentSizeStyles,
  ...(attrs.style || {})
}));

const attrsWithoutClassAndStyle = computed(() => {
  const { class: _, style: __, ...rest } = attrs;
  return rest;
});

const normalizedIgnore = computed(() =>
  Array.isArray(props.ignoreDimensions) ? props.ignoreDimensions : [props.ignoreDimensions]
);

function updateDimensions(rect) {
  const { width, height, top, left } = rect;
  const newState = { width, height, top, left };

  const hasChange = Object.keys(newState).some(
    (key) => state.value[key] !== newState[key]
  );

  if (!hasChange) return;

  const shouldUpdate = !Object.keys(newState).every((key) =>
    normalizedIgnore.value.includes(key)
  );

  if (shouldUpdate) {
    Object.assign(state.value, newState);
  }
}

const debouncedUpdate = useDebounceFn(updateDimensions, props.debounceTime);

useResizeObserver(target, (entries) => {
  const entry = entries[0];
  if (entry) debouncedUpdate(entry.contentRect);
});

defineExpose({
  ...state
})
</script>