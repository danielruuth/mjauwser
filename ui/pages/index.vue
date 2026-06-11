<template>
  <div class="min-h-screen bg-white flex flex-col">
    <header class="px-8 py-4 border-b border-gray-200">
      <h1 class="text-3xl font-bold text-gray-900">Kattutställning · Live Ringar</h1>
    </header>
    <div class="flex-1 p-8 overflow-auto">
      <div v-for="show in shows" :key="show.id" class="mb-12">
        <h2 class="text-2xl font-bold text-gray-800 mb-1">{{ show.name }}</h2>
        <p class="text-gray-400 mb-6">{{ show.start_date }} → {{ show.end_date }}</p>

        <div v-for="day in show.days" :key="day.id" class="mb-8">
          <h3 class="text-lg font-medium text-gray-500 mb-3">{{ day.name }}</h3>
          <div v-if="day.rings && day.rings.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            <RingDisplayCard v-for="ring in day.rings" :key="ring.id" :ring="ring" />
          </div>
          <div v-else class="text-gray-300 text-lg py-4">Inga aktiva bord</div>
        </div>
      </div>
    </div>
    <div class="absolute left-4 bottom-0 w-24 h-auto"><img src="/assets/mjauwser.webp" alt="Mjauwser" /></div>
  </div>
</template>

<script setup lang="ts">
import type { Show } from '~/types'
import { api } from '~/utils/api'

definePageMeta({ layout: 'display-layout' })

const shows = ref<Show[]>([])

async function load() {
  const state = await api.state.get()
  shows.value = state.shows || []
}

const { connect, disconnect, onState, on } = useWebSocket()

onMounted(() => {
  connect('display')

  const unsubState = onState((state: any) => {
    if (state?.shows) shows.value = state.shows
  })

  const unsubProgress = on('RING_PROGRESSED', (payload: any) => {
    const updated = payload?.ring
    if (!updated) return
    for (const show of shows.value) {
      for (const day of show.days || []) {
        const idx = (day.rings || []).findIndex((r: any) => r.id === updated.id)
        if (idx >= 0) {
          day.rings[idx] = updated
          return
        }
      }
    }
  })

  onUnmounted(() => {
    disconnect()
    unsubState()
    unsubProgress()
  })

  load()
})
</script>
