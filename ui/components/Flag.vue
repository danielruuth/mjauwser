<template>
  <img
    v-if="src"
    :src="src"
    class="inline-block align-middle"
    :style="{ width: px, height: px }"
    @error="onError"
  />
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  code: string
  size?: 'nano' | 'micro' | 'mini' | 'small' | 'default' | 'medium' | 'large' | 'huge'
}>(), { size: 'default' })

const sizes: Record<string, number> = {
  nano: 12,
  micro: 14,
  mini: 18,
  small: 24,
  default: 32,
  medium: 48,
  large: 64,
  huge: 128,
}

const px = computed(() => `${sizes[props.size] || 32}px`)

const errored = ref(false)

const src = computed(() => {
  if (errored.value || !props.code) return null
  return `/flags/${props.code.toLowerCase()}.svg`
})

function onError() {
  errored.value = true
}
</script>
