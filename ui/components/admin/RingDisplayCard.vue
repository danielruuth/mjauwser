<template>
  <div class="bg-gray-50 rounded-2xl p-6 border border-gray-200 min-h-[200px]">
    <div class="text-sm text-gray-400 font-medium mb-2">Ring {{ ring.ring_number }}</div>
    <div v-if="ring.judge" class="flex items-center gap-2 text-gray-600 mb-4">
      <Flag v-if="ring.judge.flag" :code="ring.judge.flag" />
      <span>{{ ring.judge.name }}</span>
    </div>
    <div class="text-6xl font-bold text-gray-900 mb-2">
      #{{ ring.current_catalog_nr || '-' }}
    </div>
    <div class="text-lg text-gray-500">{{ ring.current_class || '' }}</div>
    <div v-if="ring.status === 'paused'" class="mt-3 text-sm font-medium text-yellow-600 bg-yellow-50 inline-block px-3 py-1 rounded-full">
      {{ ring.pause_message || 'PAUS' }}
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Ring } from '~/types'
defineProps<{ ring: Ring }>()
</script>
