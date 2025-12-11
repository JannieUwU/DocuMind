<template>
  <div
    ref="container"
    :class="props.class"
  >
    <Motion
      v-for="(child, index) in children"
      :key="index"
      ref="childElements"
      as="div"
      :initial="getInitial()"
      :while-in-view="getAnimate()"
      :transition="{
        duration: props.duration,
        easing: 'easeInOut',
        delay: props.delay * index,
      }"
    >
      <component :is="child" />
    </Motion>
  </div>
</template>

<script setup>
import { Motion } from "motion-v";
import { ref, onMounted, watchEffect, useSlots } from "vue";

const props = defineProps({
  duration: {
    type: Number,
    default: 1
  },
  delay: {
    type: Number,
    default: 2
  },
  blur: {
    type: String,
    default: "20px"
  },
  yOffset: {
    type: Number,
    default: 20
  },
  class: {
    type: String,
    default: ""
  }
});

const container = ref(null);
const childElements = ref([]);
const slots = useSlots();

const children = ref([]);

onMounted(() => {
  // This will reactively capture all content provided in the default slot
  watchEffect(() => {
    children.value = slots.default ? slots.default() : [];
  });
});

function getInitial() {
  return {
    opacity: 0,
    filter: `blur(${props.blur})`,
    y: props.yOffset,
  };
}

function getAnimate() {
  return {
    opacity: 1,
    filter: `blur(0px)`,
    y: 0,
  };
}
</script>