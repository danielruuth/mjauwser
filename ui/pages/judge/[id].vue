<template>
  <div class="min-h-screen bg-gray-950 text-white p-8">
    <div class="max-w-2xl mx-auto space-y-6">
      <div class="flex items-center justify-between mb-6">
        <div>
          <div class="flex items-center gap-3">
            <Flag v-if="judge?.flag" :code="judge.flag" size="small" />
            <h1 class="text-3xl font-bold">{{ judge?.name || 'Domare' }}</h1>
          </div>
          <div v-if="judge" class="flex gap-2 mt-2">
            <span v-for="cat in judge.categories" :key="cat.id" class="text-xs px-2 py-0.5 rounded-full bg-blue-900/60 text-blue-200">{{ cat.name }}</span>
          </div>
        </div>
      </div>

      <div v-if="rings.length === 0" class="text-center py-16 text-gray-600">
        <p class="text-xl">Inga bord tilldelade</p>
        <p class="text-sm mt-2">Tilldela denna domare till ett bord i en utställningsdag för att börja.</p>
      </div>

      <div v-else class="space-y-4">
        <h2 class="text-sm uppercase tracking-wider text-gray-500 font-medium">Tilldelade bord</h2>
        <div v-for="ring in rings" :key="ring.id" class="bg-gray-900 rounded-2xl border border-gray-800 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-xl font-bold">Ring {{ ring.ring_number }}</p>
              <p v-if="ring.show_day_name" class="text-sm text-gray-400">{{ ring.show_day_name }}</p>
            </div>
            <div class="flex gap-3">
              <NuxtLink :to="`/ring/${ring.id}/panel`" class="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 rounded-xl text-sm font-medium transition-colors">
                Domarpanel
              </NuxtLink>
              <NuxtLink :to="`/ring/${ring.id}`" class="px-5 py-2.5 bg-gray-700 hover:bg-gray-600 rounded-xl text-sm font-medium transition-colors">
                Skärm
              </NuxtLink>
            </div>
          </div>
          <div class="mt-3 flex items-center gap-3 text-sm text-gray-500">
            <span :class="ring.status === 'active' ? 'text-green-400' : ring.status === 'paused' ? 'text-yellow-400' : 'text-gray-500'">{{ ring.status }}</span>
            <span>·</span>
            <span>Current: #{{ ring.current_catalog_nr || '-' }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useJudgesStore } from '~/stores/judges'
import { api } from '~/utils/api'
import type { Judge, Ring } from '~/types'

definePageMeta({ layout: 'judge-layout' })

const route = useRoute()
const judgeId = computed(() => Number(route.params.id))

const judgesStore = useJudgesStore()
const judge = computed(() => judgesStore.judges.find((j) => j.id === judgeId.value) || null)

const rings = ref<(Ring & { show_day_name?: string })[]>([])

async function loadRings() {
  rings.value = await api.judges.rings(judgeId.value)
}

onMounted(async () => {
  await judgesStore.fetchAll()
  await loadRings()
})
</script>
