<template>
  <Teleport to="body">
    <div v-if="visible" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="$emit('cancel')">
      <div class="bg-white rounded-xl shadow-xl p-6 w-full max-w-sm mx-4">
        <h3 class="text-lg font-semibold mb-2">{{ title }}</h3>
        <p class="text-sm text-gray-600 mb-6">{{ message }}</p>
        <div class="flex gap-3 justify-end">
          <Btn variant="outline" size="small" @click="$emit('cancel')">Avbryt</Btn>
          <Btn variant="primary" size="small" @click="$emit('confirm')">Bekräfta</Btn>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
defineProps<{
  visible: boolean
  title?: string
  message: string
}>()

defineEmits<{
  confirm: []
  cancel: []
}>()
</script>
