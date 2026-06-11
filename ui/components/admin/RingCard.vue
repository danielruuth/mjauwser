<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200">
    <div class="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <h3 class="text-lg font-bold">Bord {{ ring.ring_number }}</h3>
        <span class="text-xs px-2 py-1 rounded-full font-medium" :class="ring.status === 'active' ? 'bg-green-100 text-green-700' : ring.status === 'paused' ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-700'">
          {{ ring.status }}
        </span>
      </div>
    </div>

    <div class="px-4 py-3 space-y-2">
      <div class="flex items-center gap-2 text-sm">
        <span class="text-gray-500">Domare:</span>
        <Flag v-if="ring.judge?.flag" :code="ring.judge.flag" size="mini" />
        <span>{{ ring.judge?.name || 'Inte tilldelad' }}</span>
        <span v-if="ring.judge?.flag" class="text-xs text-gray-400">({{ ring.judge.flag }})</span>
      </div>

      <div class="text-sm">
        <span class="text-gray-500">Kategorier:</span>
        <div class="flex gap-1 flex-wrap mt-1">
          <span v-for="cat in ring.categories" :key="cat.id" class="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">{{ cat.name }}</span>
          <span v-if="ring.categories.length === 0" class="text-xs text-gray-400">inga</span>
        </div>
      </div>

      <div class="text-sm">
        <span class="text-gray-500">Nuvarande katt:</span>
        <span class="font-mono font-medium ml-1">#{{ ring.current_catalog_nr || '-' }}</span>
      </div>
    </div>

    <div class="px-4 py-3 border-t border-gray-200 flex gap-2 flex-wrap">
      <Btn variant="secondary" size="small" @click="$emit('assign-judge', ring)">
        <Gavel class="w-4 h-4" />
        Domare
      </Btn>
      <Btn variant="primary" size="small" @click="$emit('next-cat', ring.id)">
        <ChevronRight class="w-4 h-4" />
        Nästa katt
      </Btn>
      <Btn v-if="ring.status === 'active'" variant="outline" size="small" @click="$emit('pause', ring.id)">
        <Pause class="w-4 h-4" />
        Pausa
      </Btn>
      <Btn v-else variant="primary" size="small" @click="$emit('resume', ring.id)">
        <Play class="w-4 h-4" />
        Återuppta
      </Btn>
      <Btn :href="`/ring/${ring.id}/panel`" variant="secondary" size="small">
        <LayoutPanelTop class="w-4 h-4" />
        Panel
      </Btn>
      <Btn :href="`/ring/${ring.id}`" variant="secondary" size="small">
        <Monitor class="w-4 h-4" />
        Skärm
      </Btn>
      <Btn variant="outline" size="small" @click="$emit('delete-ring', ring.id)">
        <Trash2 class="w-4 h-4" />
        Radera
      </Btn>
    </div>

    <details class="border-t border-gray-200">
      <summary class="px-4 py-2 text-sm text-gray-500 cursor-pointer hover:bg-gray-50 select-none">
        Katter i kön ({{ queue.length }})
      </summary>
      <div class="border-t border-gray-100">
        <div v-if="queue.length === 0" class="px-4 py-3 text-sm text-gray-400">Inga katter i kön</div>
        <div v-else class="max-h-60 overflow-y-auto divide-y divide-gray-50">
          <div v-for="item in enrichedQueue" :key="item.id" class="flex items-center gap-3 px-4 py-2 text-sm hover:bg-gray-50">
            <span class="text-gray-400 w-6 text-right font-mono text-xs">{{ item.sequence_order }}.</span>
            <span class="font-mono text-gray-700">#{{ item.catalog_nr }}</span>
            <span class="text-gray-900">{{ item.cat_name }}</span>
          </div>
        </div>
      </div>
    </details>
  </div>
</template>

<script setup lang="ts">
import { Gavel, ChevronRight, Play, Pause, Monitor, Trash2, LayoutPanelTop, Layout } from '@lucide/vue';
import type { Ring, RingQueueItem } from '~/types'
import { api } from '~/utils/api'

const props = defineProps<{
  ring: Ring
  cats: { id: number; name: string; catalog_nr: number }[]
}>()

defineEmits<{
  'assign-judge': [ring: Ring]
  'next-cat': [ringId: number]
  pause: [ringId: number]
  resume: [ringId: number]
  'delete-ring': [ringId: number]
}>()

const queue = ref<RingQueueItem[]>([])

const catMap = computed(() => {
  const map = new Map<number, { name: string; catalog_nr: number }>()
  for (const cat of props.cats) {
    map.set(cat.id, { name: cat.name, catalog_nr: cat.catalog_nr })
  }
  return map
})

const enrichedQueue = computed(() => {
  return queue.value.map((item) => {
    const cat = catMap.value.get(item.cat_id)
    return {
      ...item,
      cat_name: cat?.name || `Katt #${item.cat_id}`,
      catalog_nr: cat?.catalog_nr ?? item.cat_id,
    }
  })
})

onMounted(async () => {
  queue.value = await api.rings.listQueue(props.ring.id)
})
</script>
