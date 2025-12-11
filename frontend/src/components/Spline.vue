<template>
  <ParentSize
    :parent-size-styles="parentSizeStyles"
    :debounce-time="50"
    v-bind="$attrs"
  >
    <template #default>
      <canvas
        ref="canvasRef"
        :style="canvasStyle"
      />
      <slot v-if="isLoading" />
    </template>
  </ParentSize>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from "vue";
import { Application } from "@splinetool/runtime";
import { useDebounceFn, useIntersectionObserver } from "@vueuse/core";
import ParentSize from "./ParentSize.vue";

const props = defineProps({
  scene: {
    type: String,
    required: true,
  },
  onLoad: Function,
  renderOnDemand: {
    type: Boolean,
    default: true,
  },
  style: Object,
});

const emit = defineEmits([
  "error",
  "spline-mouse-down",
  "spline-mouse-up",
  "spline-mouse-hover",
  "spline-key-down",
  "spline-key-up",
  "spline-start",
  "spline-look-at",
  "spline-follow",
  "spline-scroll",
]);

const canvasRef = ref(null);
const isLoading = ref(false);
const splineApp = ref(null);
const isVisible = ref(true);

let cleanup = () => {};

const parentSizeStyles = computed(() => ({
  overflow: "hidden",
  ...props.style,
}));

const canvasStyle = computed(() => ({
  display: "block",
  width: "100%",
  height: "100%",
}));

const { stop: stopIntersectionObserver } = useIntersectionObserver(
  canvasRef,
  ([{ isIntersecting }]) => {
    isVisible.value = isIntersecting;
    if (isIntersecting && splineApp.value) {
      nextTick(() => {
        if (canvasRef.value && splineApp.value) {
          splineApp.value.requestRender();
          splineApp.value.setSize(canvasRef.value.clientWidth, canvasRef.value.clientHeight);
        }
      });
    }
  },
  { threshold: 0.1 },
);

function eventHandler(name, handler) {
  if (!handler || !splineApp.value) return;
  const debouncedHandler = useDebounceFn(handler, 50, { maxWait: 100 });
  splineApp.value.addEventListener(name, debouncedHandler);
  return () => splineApp.value?.removeEventListener(name, debouncedHandler);
}

async function initSpline() {
  if (!canvasRef.value) return;

  isLoading.value = true;

  try {
    if (splineApp.value) {
      splineApp.value.dispose();
      splineApp.value = null;
    }

    splineApp.value = new Application(canvasRef.value, {
      renderOnDemand: props.renderOnDemand,
    });

    await splineApp.value.load(props.scene);

    const cleanUpFns = [
      eventHandler("mouseDown", (e) => emit("spline-mouse-down", e)),
      eventHandler("mouseUp", (e) => emit("spline-mouse-up", e)),
      eventHandler("mouseHover", (e) => emit("spline-mouse-hover", e)),
      eventHandler("keyDown", (e) => emit("spline-key-down", e)),
      eventHandler("keyUp", (e) => emit("spline-key-up", e)),
      eventHandler("start", (e) => emit("spline-start", e)),
      eventHandler("lookAt", (e) => emit("spline-look-at", e)),
      eventHandler("follow", (e) => emit("spline-follow", e)),
      eventHandler("scroll", (e) => emit("spline-scroll", e)),
    ].filter(Boolean);

    isLoading.value = false;
    props.onLoad?.(splineApp.value);

    return () => {
      cleanUpFns.forEach((fn) => fn?.());
    };
  } catch (err) {
    console.error("Spline initialization error:", err);
    emit("error", err);
    isLoading.value = false;
    return () => {};
  }
}

async function initialize() {
  cleanup();
  cleanup = (await initSpline()) ?? (() => {});
}

onMounted(async () => {
  await initialize();

  watch(isVisible, (visible) => {
    if (visible) {
      initialize();
    }
  });
});

onUnmounted(() => {
  stopIntersectionObserver();
  if (splineApp.value) {
    splineApp.value.dispose();
    splineApp.value = null;
  }
});
</script>