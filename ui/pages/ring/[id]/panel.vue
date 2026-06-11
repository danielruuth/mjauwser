<template>
  <div class="min-h-screen bg-gray-950 text-white p-8">
    <div class="max-w-lg mx-auto space-y-8">
      <!-- Header -->
      <div class="text-center">
        <div class="text-4xl font-bold mb-2">Ring {{ ring?.ring_number || '-' }}</div>
        <div class="flex items-center justify-center gap-2 text-xl text-gray-400">
          <Flag v-if="ring?.judge?.flag" :code="ring.judge.flag" />
          <span>{{ ring?.judge?.name || 'Inte tilldelad' }}</span>
        </div>
      </div>

      <!-- Current Cat -->
      <div class="bg-gray-900 rounded-2xl p-8 text-center border border-gray-800">
        <div v-if="currentCat" class="space-y-4">
          <div class="text-8xl font-bold tracking-wider">#{{ currentCat.catalog_nr }}</div>
          <div class="text-2xl text-gray-400">{{ currentCat.name }}</div>
          <div class="text-lg text-gray-500">{{ currentCat.breed }} · {{ currentCat.class }}</div>
        </div>
        <div v-else class="text-2xl text-gray-600">Ingen aktuell katt</div>
      </div>

      <!-- Upcoming Cats -->
      <div class="space-y-2">
        <div class="text-sm text-gray-500 uppercase tracking-wider font-medium">Kommande</div>
        <div class="grid grid-cols-3 gap-3">
          <div v-for="item in upcomingCats" :key="item.id" class="bg-gray-900 rounded-xl p-4 text-center border border-gray-800">
            <div class="text-2xl font-bold">#{{ item.catalog_nr }}</div>
            <div class="text-sm text-gray-400 truncate">{{ item.name }}</div>
            <div class="text-xs text-gray-500">{{ item.breed }}</div>
          </div>
          <div v-if="upcomingCats.length === 0" class="col-span-3 text-center text-gray-600 py-4 text-sm">
            {{ ringQueue.length === 0 ? 'Kön är tom' : 'Inga kommande' }}
          </div>
        </div>
      </div>

      <!-- Queue Progress -->
      <div class="text-center text-sm text-gray-500">
        {{ completedCount }} / {{ ringQueue.length }} bedömda
      </div>

      <!-- Pause Message -->
      <div v-if="ring?.status === 'paused' && ring?.pause_message" class="bg-yellow-900/30 border border-yellow-700 rounded-xl p-4 text-center">
        <div class="text-sm text-yellow-400 uppercase tracking-wider font-medium mb-1">Pausmeddelande</div>
        <div class="text-lg text-yellow-200">{{ ring.pause_message }}</div>
      </div>

      <!-- Actions -->
      <div class="grid grid-cols-3 gap-3">
        <button
          class="w-full py-6 bg-red-700 hover:bg-red-600 disabled:opacity-20 text-white rounded-2xl text-xl font-bold transition-colors"
          :disabled="!hasPrevious || ring?.status === 'paused'"
          @click="previousCat"
        >
          ← Föregående
        </button>
        <button
          class="w-full py-6 bg-green-600 hover:bg-green-500 disabled:opacity-30 text-white rounded-2xl text-2xl font-bold transition-colors"
          :disabled="ringQueue.length === 0 || ring?.status === 'paused'"
          @click="nextCat"
        >
          Nästa katt →
        </button>
        <button
          class="w-full py-6 rounded-2xl text-xl font-bold transition-colors"
          :class="ring?.status === 'paused' ? 'bg-green-700 hover:bg-green-600' : 'bg-yellow-700 hover:bg-yellow-600'"
          @click="togglePause"
        >
          {{ ring?.status === 'paused' ? '▶ Återuppta' : '⏸ Pausa' }}
        </button>
      </div>

      <button class="w-full py-4 bg-red-900 hover:bg-red-800 text-white rounded-2xl text-lg font-bold transition-colors mt-3" @click="showAbsentModal = true">
        Absa katt
      </button>

      <!-- Offline banner -->
      <div v-if="!online" class="fixed bottom-0 left-0 right-0 bg-red-600 text-white text-center py-2 text-sm font-medium">
        Offline — ändringar i kö
      </div>
    </div>

    <!-- Pause Message Modal -->
    <Teleport to="body">
      <div v-if="showPauseModal" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50" @click.self="showPauseModal = false">
        <div class="bg-gray-900 rounded-2xl p-6 w-full max-w-lg mx-4 border border-gray-700">
          <h3 class="text-lg font-semibold text-white mb-2">Pausa</h3>
          <p class="text-sm text-gray-400 mb-4">Vill du ange ett pausmeddelande?</p>
          <input v-model="pauseMessage" placeholder="Meddelande (valfritt)" class="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-sm text-white placeholder-gray-500 mb-4" />
          <div class="flex gap-3 justify-end">
            <button class="px-4 py-2 text-sm text-gray-300 hover:text-white" @click="confirmPause(false)">Nej</button>
            <button class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium" @click="confirmPause(true)">Spara</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Absent Cat Modal -->
    <Teleport to="body">
      <div v-if="showAbsentModal" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50" @click.self="showAbsentModal = false">
        <div class="bg-gray-900 rounded-2xl p-6 w-full max-w-lg mx-4 border border-gray-700 max-h-[80vh] overflow-y-auto">
          <h3 class="text-lg font-semibold text-white mb-4">Stryk katt</h3>
          <div v-if="ringQueue.length === 0" class="text-sm text-gray-500 text-center py-8">Inga katter i kön.</div>
          <div v-else class="space-y-2">
            <div v-for="item in ringQueue" :key="item.id" class="flex items-center justify-between bg-gray-800 rounded-xl px-4 py-3">
              <div class="text-sm text-white">
                <span class="font-mono font-bold">#{{ item.catalog_nr || item.cat?.id }}</span>
                <span class="ml-2">{{ item.cat?.name || 'Okänd' }}</span>
                <span class="ml-2 text-gray-400">{{ item.cat?.breed_ems }}</span>
              </div>
              <button class="px-3 py-1.5 bg-red-700 hover:bg-red-600 text-white rounded-lg text-xs font-medium" @click="markAbsent(item)">
                Absa
              </button>
            </div>
          </div>
          <div class="flex justify-end pt-3">
            <button class="px-4 py-2 text-sm text-gray-300 hover:text-white" @click="showAbsentModal = false">Stäng</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import type { Ring, RingQueueItem } from '~/types'
import { api } from '~/utils/api'
import { useRingQueueStore } from '~/stores/ringQueue'

definePageMeta({ layout: 'judge-layout' })

const route = useRoute()
const ringId = computed(() => Number(route.params.id))

const store = useRingQueueStore()
const ring = ref<Ring | null>(null)
const ringQueue = ref<RingQueueItem[]>([])
const online = ref(true)
const showPauseModal = ref(false)
const pauseMessage = ref('')
const showAbsentModal = ref(false)

const currentCat = computed(() => {
  const current = ringQueue.value.find((q) => q.status === 'ongoing')
  if (!current) return null
  const cat = current.cat
  return { catalog_nr: current.catalog_nr || cat?.id, name: cat?.name || '#', breed: cat?.breed_ems || '', class: cat?.show_class || '' }
})

const upcomingCats = computed(() => {
  return ringQueue.value
    .filter((q) => q.status === 'pending')
    .slice(0, 3)
    .map((q) => ({
      id: q.id,
      catalog_nr: q.catalog_nr || q.cat?.id || '-',
      name: q.cat?.name || '',
      breed: q.cat?.breed_ems || '',
    }))
})

const completedCount = computed(() => ringQueue.value.filter((q) => q.status === 'completed' || q.status === 'skipped').length)

const hasPrevious = computed(() => {
  const current = ringQueue.value.find((q) => q.status === 'ongoing')
  if (!current) return false
  return ringQueue.value.some((q) => q.status === 'completed' && q.sequence_order < current.sequence_order)
})

async function load() {
  ring.value = await api.rings.get(ringId.value)
  ringQueue.value = await api.rings.queue.get(ringId.value)
}

async function nextCat() {
  try {
    await api.rings.nextCat(ringId.value)
  } catch (e: any) {
    alert(e.message || 'Kön kan vara tom')
  }
  // load() is called by the RING_PROGRESSED handler below
}

async function previousCat() {
  try {
    await api.rings.previousCat(ringId.value)
  } catch (e: any) {
    alert(e.message || 'Ingen föregående katt')
  }
}

async function togglePause() {
  if (ring.value?.status === 'paused') {
    await api.rings.resume(ringId.value)
    await load()
  } else {
    pauseMessage.value = ''
    showPauseModal.value = true
  }
}

async function confirmPause(withMessage: boolean) {
  const msg = withMessage ? pauseMessage.value || undefined : undefined
  await api.rings.pause(ringId.value, msg)
  showPauseModal.value = false
  await load()
}

async function markAbsent(item: RingQueueItem) {
  if (!ring.value) return
  const catName = item.cat?.name || `#${item.catalog_nr || item.cat_id}`
  const ok = confirm(`Stryk ${catName}?`)
  if (!ok) return
  try {
    await api.cats.updateDayStatus(item.cat_id, ring.value.show_day_id, 'absent')
    showAbsentModal.value = false
    await load()
  } catch (e: any) {
    alert(e.message)
  }
}

const { connect, disconnect, on, onState } = useWebSocket()

onMounted(() => {
  connect('judge', ringId.value, { deviceType: 'panel' })

  const unsubState = onState((state: any) => {
    ring.value = state?.rings?.[ringId.value] || ring.value
  })

  const unsubProgress = on('RING_PROGRESSED', (payload: any) => {
    if (payload?.ring?.id === ringId.value) {
      ring.value = payload.ring
      load()
    }
  })

  const unsubStatus = on('RING_STATUS_CHANGED', (payload: any) => {
    if (payload?.ring?.id === ringId.value) {
      ring.value = payload.ring
      load()
    }
  })

  const unsubDayCat = on('DAY_CAT_STATUS_CHANGED', (payload: any) => {
    if (ring.value && payload?.show_day_id === ring.value.show_day_id) {
      load()
    }
  })

  onUnmounted(() => {
    disconnect()
    unsubState()
    unsubProgress()
    unsubStatus()
    unsubDayCat()
  })
})

// Online/offline tracking
if (process.client) {
  window.addEventListener('online', () => { online.value = true })
  window.addEventListener('offline', () => { online.value = false })
  online.value = navigator.onLine
}

onMounted(() => load())
</script>
