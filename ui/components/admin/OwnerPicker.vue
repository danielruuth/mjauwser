<template>
  <div class="relative">
    <input
      ref="inputRef"
      v-model="inputValue"
      type="text"
      :placeholder="placeholder"
      class="w-full px-3 py-2 border rounded-lg text-sm"
      @input="onInput"
      @keydown.down.prevent="highlightNext"
      @keydown.up.prevent="highlightPrev"
      @keydown.enter.prevent="selectHighlighted"
      @keydown.escape="closeDropdown"
      @blur="onBlur"
      @focus="onFocus"
    />
    <ul
      v-if="showDropdown"
      class="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto"
    >
      <li
        v-for="(owner, i) in suggestions"
        :key="owner.id"
        class="px-3 py-2 text-sm cursor-pointer"
        :class="i === highlightIndex ? 'bg-gray-100' : 'hover:bg-gray-50'"
        @mousedown.prevent="selectOwner(owner)"
      >
        {{ owner.name }}
        <span v-if="owner.phone" class="text-gray-400 ml-2">{{ owner.phone }}</span>
      </li>
      <li
        v-if="showCreateOption"
        class="px-3 py-2 text-sm text-purple-700 cursor-pointer hover:bg-purple-50"
        @mousedown.prevent="createNew"
      >
        + Skapa "{{ inputValue }}"
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { api } from '~/utils/api'
import type { Owner } from '~/types'

const props = defineProps<{
  modelValue: { owner_id?: number; owner_name?: string } | null
  placeholder?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: { owner_id?: number; owner_name?: string } | null]
}>()

const inputRef = ref<HTMLInputElement>()
const inputValue = ref('')
const suggestions = ref<Owner[]>([])
const showDropdown = ref(false)
const highlightIndex = ref(-1)
const debounceTimer = ref<ReturnType<typeof setTimeout>>()

watch(() => props.modelValue, (val) => {
  if (!val) {
    inputValue.value = ''
  }
}, { immediate: true })

const showCreateOption = computed(() => {
  const q = inputValue.value.trim()
  if (!q || q.length < 1) return false
  const exact = suggestions.value.some((o) => o.name.toLowerCase() === q.toLowerCase())
  return !exact
})

async function searchOwners(q: string) {
  if (!q || q.length < 1) {
    suggestions.value = []
    showDropdown.value = false
    return
  }
  try {
    suggestions.value = await api.owners.list(q)
    showDropdown.value = suggestions.value.length > 0 || inputValue.value.trim().length > 0
    highlightIndex.value = -1
  } catch {
    suggestions.value = []
  }
}

function onInput() {
  clearTimeout(debounceTimer.value)
  debounceTimer.value = setTimeout(() => searchOwners(inputValue.value), 150)
  emit('update:modelValue', { owner_name: inputValue.value.trim() || undefined })
}

function onFocus() {
  if (inputValue.value.trim().length > 0) {
    searchOwners(inputValue.value)
  }
}

function onBlur() {
  setTimeout(() => {
    showDropdown.value = false
  }, 200)
}

function closeDropdown() {
  showDropdown.value = false
}

function highlightNext() {
  const max = suggestions.value.length + (showCreateOption.value ? 1 : 0) - 1
  highlightIndex.value = Math.min(highlightIndex.value + 1, max)
}

function highlightPrev() {
  highlightIndex.value = Math.max(highlightIndex.value - 1, -1)
}

function selectHighlighted() {
  if (highlightIndex.value >= 0 && highlightIndex.value < suggestions.value.length) {
    selectOwner(suggestions.value[highlightIndex.value])
  } else if (showCreateOption.value) {
    createNew()
  }
}

function selectOwner(owner: Owner) {
  inputValue.value = owner.name
  showDropdown.value = false
  emit('update:modelValue', { owner_id: owner.id })
}

async function createNew() {
  const name = inputValue.value.trim()
  if (!name) return
  try {
    const owner = await api.owners.create({ name })
    inputValue.value = owner.name
    showDropdown.value = false
    emit('update:modelValue', { owner_id: owner.id })
  } catch (e: any) {
    alert(e.message)
  }
}
</script>
