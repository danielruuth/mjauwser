<template>
  <component
    :is="href ? 'a' : 'button'"
    v-bind="attrs"
    :class="classes"
    :disabled="disabled"
    :href="href"
    @click="$emit('click', $event)"
  >
    <component v-if="icon" :is="icon" class="shrink-0" :class="iconClass" />
    <slot />
  </component>
</template>

<script setup lang="ts">
import { computed, useAttrs } from 'vue'

const props = withDefaults(defineProps<{
  variant?: 'primary' | 'secondary' | 'outline'
  size?: 'normal' | 'small'
  icon?: object
  disabled?: boolean
  href?: string
}>(), {
  variant: 'primary',
  size: 'normal',
})

defineEmits<{ click: [e: MouseEvent] }>()

const attrs = useAttrs()

const base = 'inline-flex items-center justify-center gap-2 transition-colors focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed select-none'

const variantClasses: Record<string, string> = {
  primary: 'bg-black text-white hover:bg-gray-800 font-bold',
  secondary: 'bg-gray-300 text-black hover:bg-gray-200',
  outline: 'border-2 border-black text-black bg-transparent hover:bg-gray-100',
}

const sizeClasses: Record<string, string> = {
  normal: 'px-3 py-2 rounded-full text-sm',
  small: 'px-2 py-1 rounded-2xl text-xs',
}

const iconSize: Record<string, string> = {
  normal: 'w-4 h-4',
  small: 'w-3 h-3',
}

const classes = computed(() => [
  base,
  variantClasses[props.variant],
  sizeClasses[props.size],
])

const iconClass = computed(() => iconSize[props.size])
</script>
