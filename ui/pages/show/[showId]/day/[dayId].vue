<template>
  <div class="min-h-screen p-8 flex flex-col">
    <div class="flex-1 grid gap-6 items-stretch" :class="gridCols">
      <RingGridItem v-for="data in ringData" :key="data.ring.id" :ringData="data" :ringCount="ringCount" />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ShowDay, Ring, RingQueueItem } from '~/types'
import { api } from '~/utils/api'

definePageMeta({ layout: 'display-layout' })

const route = useRoute()
const showId = computed(() => Number(route.params.showId))
const dayId = computed(() => Number(route.params.dayId))

const deviceId = import.meta.client
  ? localStorage.getItem('catshow_device_id') || (() => {
      const id = crypto.randomUUID()
      localStorage.setItem('catshow_device_id', id)
      return id
    })()
  : ''

const day = ref<ShowDay | null>(null)
const rings = ref<Ring[]>([])
const queueMap = ref<Map<number, RingQueueItem[]>>(new Map())

const ringCount = computed(() => rings.value.length)

const gridCols = computed(() => {
  if (ringCount.value >= 5) return 'grid-cols-3'
  if (ringCount.value >= 3) return 'grid-cols-2'
  return 'grid-cols-1'
})







const ringData = computed(() => {
  return rings.value.map((ring) => {
    const queue = queueMap.value.get(ring.id) || []
    const current = queue.find((q) => q.status === 'ongoing') || null
    const upcoming = queue.filter((q) => q.status === 'pending').slice(0, 3)
    return {
      ring,
      current: current
        ? {
            catalog_nr: current.catalog_nr || current.cat?.id || '',
            name: current.cat?.name || '',
            breed: current.cat?.breed_ems || '',
            class: current.cat?.show_class || '',
          }
        : null,
      upcoming: upcoming.map((q) => ({
        id: q.id,
        catalog_nr: q.catalog_nr || q.cat?.id || '',
        name: q.cat?.name || '',
      })),
    }
  })
})

async function loadDay() {
  const d = await api.showDays.get(dayId.value)
  day.value = d
  rings.value = d.rings || []
  await loadQueues()
}

async function loadQueues() {
  if (rings.value.length === 0) return
  const queues = await Promise.all(rings.value.map((r) => api.rings.queue.get(r.id)))
  const map = new Map<number, RingQueueItem[]>()
  rings.value.forEach((r, i) => map.set(r.id, queues[i]))
  queueMap.value = map
}

async function refreshRing(ringId: number) {
  const queue = await api.rings.queue.get(ringId)
  const copy = new Map(queueMap.value)
  copy.set(ringId, queue)
  queueMap.value = copy
}

const { connect, disconnect, on, onState } = useWebSocket()

onMounted(() => {
  connect('display', undefined, { deviceType: 'day_display', deviceId, showId: showId.value, dayId: dayId.value })

  const unsubState = onState((state: any) => {
    if (state?.rings) {
      for (const [id, r] of Object.entries(state.rings)) {
        const rid = Number(id)
        const idx = rings.value.findIndex((x) => x.id === rid)
        if (idx !== -1) {
          const copy = [...rings.value]
          copy[idx] = r as Ring
          rings.value = copy
        }
      }
    }
  })

  const unsubProgress = on('RING_PROGRESSED', (payload: any) => {
    const ringId = payload?.ring?.id
    if (ringId && rings.value.some((r) => r.id === ringId)) {
      const idx = rings.value.findIndex((r) => r.id === ringId)
      if (idx !== -1) {
        const copy = [...rings.value]
        copy[idx] = { ...copy[idx], ...payload.ring }
        rings.value = copy
      }
      refreshRing(ringId)
    }
  })

  const unsubStatus = on('RING_STATUS_CHANGED', (payload: any) => {
    const ringId = payload?.ring?.id
    if (ringId && rings.value.some((r) => r.id === ringId)) {
      const idx = rings.value.findIndex((r) => r.id === ringId)
      if (idx !== -1) {
        const copy = [...rings.value]
        copy[idx] = { ...copy[idx], ...payload.ring }
        rings.value = copy
      }
    }
  })

  onUnmounted(() => {
    disconnect()
    unsubState()
    unsubProgress()
    unsubStatus()
  })

  loadDay()
})
</script>
