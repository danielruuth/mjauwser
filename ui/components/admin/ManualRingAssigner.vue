<template>
  <div>
    <div class="mb-6 flex items-center gap-3">
      <NuxtLink :to="`/admin/shows/${showId}/days/${showDayId}`" class="px-3 py-1.5 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-sm font-medium">
        ← Tillbaka
      </NuxtLink>
      <h1 class="text-xl font-bold text-gray-900">Manuell ringtilldelning</h1>
    </div>

    <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
      <div class="bg-white rounded-lg border border-gray-200 p-3 text-center">
        <div class="text-2xl font-bold text-gray-900">{{ totalCats }}</div>
        <div class="text-xs text-gray-500">Totalt katter</div>
      </div>
      <div class="bg-green-50 rounded-lg border border-green-200 p-3 text-center">
        <div class="text-2xl font-bold text-green-700">{{ assignedCount }}</div>
        <div class="text-xs text-green-600">Tilldelade</div>
      </div>
      <div class="bg-yellow-50 rounded-lg border border-yellow-200 p-3 text-center">
        <div class="text-2xl font-bold text-yellow-700">{{ unassignedCount }}</div>
        <div class="text-xs text-yellow-600">Otilldelade</div>
      </div>
      <div class="bg-blue-50 rounded-lg border border-blue-200 p-3 text-center">
        <div class="text-2xl font-bold text-blue-700">{{ rings.length }}</div>
        <div class="text-xs text-blue-600">Domarbord</div>
      </div>
    </div>

    <div
      class="bg-white rounded-xl shadow-sm border-2 transition-colors mb-6"
      :class="unassignedDropClasses"
    >
      <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
        <h2 class="text-sm font-semibold text-gray-700">Otilldelade katter</h2>
        <span class="text-xs px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700">{{ unassignedCount }}</span>
      </div>
      <div
        class="flex gap-3 overflow-x-auto p-4 min-h-[120px]"
        @dragover.prevent="onDragOverUnassigned"
        @dragleave="onDragLeaveUnassigned"
        @drop="onDropOnUnassigned"
      >
        <div
          v-for="cat in unassignedCats"
          :key="cat.id"
          :draggable="!moving"
          class="flex-shrink-0 w-52 p-3 rounded-lg border-2 cursor-grab active:cursor-grabbing select-none transition-all"
          :class="unassignedCatCardClasses(cat)"
          @dragstart="onDragStart(cat.id, null, $event)"
          @dragend="resetDrag"
        >
          <div class="flex items-start justify-between mb-1">
            <span class="font-mono text-xs text-gray-400">#{{ getCatalogNumber(cat.id) }}</span>
            <TriangleAlert v-if="!hasCompatibleRing(cat)" class="w-4 h-4 text-amber-500 shrink-0" title="Inget kompatibelt domarbord" />
          </div>
          <div class="text-sm font-medium truncate">{{ cat.name }}</div>
          <div class="text-xs text-gray-500 mt-0.5">{{ cat.breed_ems }} · {{ getCategoryName(cat.breed_ems) }}</div>
          <div class="text-xs text-gray-400 mt-0.5">{{ cat.show_class }}</div>
        </div>
        <div v-if="unassignedCats.length === 0" class="flex items-center justify-center w-full text-sm text-gray-400">
          <span v-if="dragSourceRingId !== null">Släpp här för att ta bort från ring</span>
          <span v-else>Alla katter är tilldelade</span>
        </div>
      </div>
    </div>

    <h2 class="text-sm font-semibold text-gray-700 mb-3">Domarbord</h2>
    <div v-if="rings.length === 0" class="text-sm text-gray-400 bg-white rounded-xl shadow-sm border border-gray-200 p-6 text-center mb-6">
      Inga domarbord skapade för denna dag.
    </div>
    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mb-8">
      <div
        v-for="ring in rings"
        :key="ring.id"
        class="bg-white rounded-xl shadow-sm border-2 transition-all"
        :class="ringBorderClasses(ring)"
        @dragover.prevent="onDragOverRing(ring)"
        @dragleave="onDragLeaveRing(ring)"
        @drop="onDropOnRing(ring)"
      >
        <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <h3 class="text-base font-bold">Bord {{ ring.ring_number }}</h3>
            <span class="text-xs px-2 py-0.5 rounded-full font-medium" :class="statusBadgeClass(ring.status)">
              {{ ring.status }}
            </span>
          </div>
        </div>

        <div class="px-4 py-2.5 space-y-1.5 border-b border-gray-50">
          <div class="flex items-center gap-1.5 text-sm">
            <span class="text-gray-400 text-xs">Domare:</span>
            <Flag v-if="ring.judge?.flag" :code="ring.judge.flag" size="mini" />
            <span class="text-sm font-medium" :class="ring.judge ? 'text-gray-900' : 'text-gray-400'">{{ ring.judge?.name || 'Ingen domare' }}</span>
          </div>
          <div class="flex gap-1 flex-wrap">
            <span v-for="c in ring.categories" :key="c.id" class="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
              {{ c.name }}
            </span>
            <span v-if="ring.categories.length === 0" class="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-400">
              Inga kategorier
            </span>
          </div>
        </div>

        <div class="px-4 py-2 border-b border-gray-50">
          <div class="flex items-center gap-3 text-sm">
            <span class="font-semibold text-gray-900">{{ ringCats(ring.id).length }}</span>
            <span class="text-gray-500">katter</span>
          </div>
          <div v-if="ringCategoryStats(ring.id).length > 0" class="flex items-center gap-3 mt-1">
            <div v-for="stat in ringCategoryStats(ring.id)" :key="stat.name" class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-gray-50 text-gray-600">
              {{ stat.name }}: {{ stat.count }}
            </div>
          </div>
        </div>

        <div class="divide-y divide-gray-50 max-h-80 overflow-y-auto">
          <div
            v-for="rc in ringCats(ring.id)"
            :key="rc.cat.id"
            :draggable="!moving"
            class="flex items-center gap-3 px-4 py-2 text-sm cursor-grab active:cursor-grabbing select-none transition-colors hover:bg-gray-50"
            :class="{ 'opacity-50': moving }"
            @dragstart="onDragStart(rc.cat.id, ring.id, $event)"
            @dragend="resetDrag"
          >
            <span class="font-mono text-xs text-gray-400 w-8 text-right shrink-0">#{{ getCatalogNumber(rc.cat.id) }}</span>
            <span class="text-gray-900 font-medium truncate">{{ rc.cat.name }}</span>
            <span class="text-xs text-gray-400 shrink-0">{{ rc.cat.breed_ems }}</span>
          </div>
          <div v-if="ringCats(ring.id).length === 0" class="px-4 py-8 text-center text-sm text-gray-400">
            <span v-if="dragSourceRingId !== null && dragSourceRingId !== ring.id && isCompatibleDrop(draggedCatId, ring.id)">Släpp katt här</span>
            <span v-else-if="dragSourceRingId !== null && dragSourceRingId !== ring.id && !isCompatibleDrop(draggedCatId, ring.id) && draggedCatId !== null">Inte kompatibel kategori</span>
            <span v-else>Inga katter i ringen</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="loading" class="fixed inset-0 bg-white/60 flex items-center justify-center z-50">
      <div class="flex items-center gap-2 px-4 py-2 bg-white rounded-lg shadow-md text-sm text-gray-600">
        <LoaderCircle class="w-4 h-4 animate-spin" />
        Laddar data...
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { api } from '~/utils/api'
import type { Cat, Ring, RingQueueItem, Breed, Category } from '~/types'
import { TriangleAlert, LoaderCircle } from '@lucide/vue'

const props = defineProps<{
  showId: number
  showDayId: number
}>()

const loading = ref(true)
const moving = ref(false)
const rings = ref<Ring[]>([])
const allCats = ref<Cat[]>([])
const breeds = ref<Breed[]>([])
const categories = ref<Category[]>([])
const ringQueues = ref<Map<number, RingQueueItem[]>>(new Map())

const draggedCatId = ref<number | null>(null)
const dragSourceRingId = ref<number | null>(null)
const hoverTargetRingId = ref<number | null>(null)
const isHoveringUnassigned = ref(false)

const breedCategoryMap = computed(() => {
  const map = new Map<string, number>()
  for (const b of breeds.value) {
    if (b.category_id) map.set(b.breed_code, b.category_id)
  }
  return map
})

const categoryNames = computed(() => {
  const map = new Map<number, string>()
  for (const c of categories.value) map.set(c.id, c.name)
  return map
})

const catAssignment = computed(() => {
  const map = new Map<number, { ringId: number; queueEntryId: number }>()
  for (const [ringId, queue] of ringQueues.value) {
    for (const item of queue) {
      map.set(item.cat_id, { ringId, queueEntryId: item.id })
    }
  }
  return map
})

const unassignedCats = computed(() =>
  allCats.value.filter((c) => !catAssignment.value.has(c.id))
)

const totalCats = computed(() => allCats.value.length)
const assignedCount = computed(() => catAssignment.value.size)
const unassignedCount = computed(() => unassignedCats.value.length)

function ringCats(ringId: number) {
  const queue = ringQueues.value.get(ringId) || []
  return queue
    .map((item) => ({
      cat: allCats.value.find((c) => c.id === item.cat_id)!,
      queueEntry: item,
    }))
    .filter((x) => x.cat)
}

function ringCategoryStats(ringId: number) {
  const ring = rings.value.find((r) => r.id === ringId)
  if (!ring) return []
  const cats = ringCats(ringId)
  const counts = new Map<string, number>()
  for (const { cat } of cats) {
    const catId = breedCategoryMap.value.get(cat.breed_ems)
    if (catId) {
      const name = categoryNames.value.get(catId) || `Kategori ${catId}`
      counts.set(name, (counts.get(name) || 0) + 1)
    }
  }
  return [...counts.entries()]
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
}

function getCatalogNumber(catId: number): number {
  const cat = allCats.value.find((c) => c.id === catId)
  const dayEntry = cat?.days?.find((d) => d.show_day_id === props.showDayId)
  return dayEntry?.catalog_nr ?? catId
}

function getCategoryName(breedEms: string): string {
  const catId = breedCategoryMap.value.get(breedEms)
  if (catId) return categoryNames.value.get(catId) || `Kategori ${catId}`
  return 'Okänd kategori'
}

function hasCompatibleRing(cat: Cat): boolean {
  const breedCategoryId = breedCategoryMap.value.get(cat.breed_ems)
  if (!breedCategoryId) return false
  return rings.value.some(
    (r) =>
      r.judge &&
      r.categories.length > 0 &&
      r.categories.some((c) => c.id === breedCategoryId)
  )
}

function isCompatibleDrop(catId: number | null, ringId: number | null): boolean {
  if (!catId || !ringId) return false
  const cat = allCats.value.find((c) => c.id === catId)
  if (!cat) return false
  const ring = rings.value.find((r) => r.id === ringId)
  if (!ring) return false
  if (!ring.judge || ring.categories.length === 0) return false
  const breedCategoryId = breedCategoryMap.value.get(cat.breed_ems)
  if (!breedCategoryId) return false
  return ring.categories.some((c) => c.id === breedCategoryId)
}

function onDragStart(catId: number, sourceRingId: number | null, event: DragEvent) {
  if (moving.value) return
  draggedCatId.value = catId
  dragSourceRingId.value = sourceRingId
  event.dataTransfer?.setData('text/plain', `${catId}`)
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'
}

function resetDrag() {
  draggedCatId.value = null
  dragSourceRingId.value = null
  if (hoverTargetRingId.value !== null) hoverTargetRingId.value = null
  isHoveringUnassigned.value = false
}

function onDragOverRing(ring: Ring) {
  if (!draggedCatId.value) return
  if (dragSourceRingId.value === ring.id) {
    hoverTargetRingId.value = null
    return
  }
  if (isCompatibleDrop(draggedCatId.value, ring.id)) {
    hoverTargetRingId.value = ring.id
  } else {
    hoverTargetRingId.value = null
  }
}

function onDragLeaveRing(ring: Ring) {
  if (hoverTargetRingId.value === ring.id) {
    hoverTargetRingId.value = null
  }
}

function onDropOnRing(ring: Ring) {
  if (!draggedCatId.value) return
  if (dragSourceRingId.value === ring.id) {
    resetDrag()
    return
  }
  if (!isCompatibleDrop(draggedCatId.value, ring.id)) {
    resetDrag()
    return
  }
  performMove(draggedCatId.value, dragSourceRingId.value, ring.id)
}

function onDragOverUnassigned() {
  if (dragSourceRingId.value !== null) {
    isHoveringUnassigned.value = true
  }
}

function onDragLeaveUnassigned() {
  isHoveringUnassigned.value = false
}

function onDropOnUnassigned() {
  if (!draggedCatId.value || dragSourceRingId.value === null) {
    resetDrag()
    return
  }
  performMove(draggedCatId.value, dragSourceRingId.value, null)
}

async function performMove(catId: number, fromRingId: number | null, toRingId: number | null) {
  moving.value = true

  try {
    if (fromRingId !== null) {
      const assignment = catAssignment.value.get(catId)
      if (!assignment) throw new Error('Cat not found in source ring')
      const q = ringQueues.value.get(fromRingId)
      if (q) {
        const idx = q.findIndex((e) => e.id === assignment.queueEntryId)
        if (idx !== -1) q.splice(idx, 1)
      }
      await api.rings.queue.remove(assignment.queueEntryId)
    }

    if (toRingId !== null) {
      const currentQueue = ringQueues.value.get(toRingId) || []
      const nextOrder =
        currentQueue.length > 0
          ? Math.max(...currentQueue.map((item) => item.sequence_order)) + 1
          : 1

      const realEntry = await api.rings.addToQueue(toRingId, catId, nextOrder)
      if (!ringQueues.value.has(toRingId)) {
        ringQueues.value.set(toRingId, [])
      }
      const cat = allCats.value.find((c) => c.id === catId)
      ringQueues.value.get(toRingId)!.push({
        ...realEntry,
        catalog_nr: getCatalogNumber(catId),
        cat: cat
          ? {
              id: cat.id,
              name: cat.name,
              breed_ems: cat.breed_ems,
              breed_name: cat.breed_name,
              gender: cat.gender,
              show_class: cat.show_class,
              status: cat.status,
            }
          : undefined,
      })
    }
  } catch (e) {
    console.error('Move failed:', e)
    await loadQueues()
  }

  moving.value = false
  resetDrag()
}

const unassignedDropClasses = computed(() => ({
  'border-blue-300 bg-blue-50/50': isHoveringUnassigned.value && dragSourceRingId.value !== null,
  'border-gray-200': !isHoveringUnassigned.value || dragSourceRingId.value === null,
}))

function unassignedCatCardClasses(cat: Cat) {
  return {
    'border-gray-200 bg-gray-50 hover:border-gray-300': !moving,
    'border-gray-100 bg-gray-50 opacity-50': moving,
    'ring-2 ring-blue-300': draggedCatId.value === cat.id,
    'border-amber-300': !hasCompatibleRing(cat) && !moving,
  }
}

function ringBorderClasses(ring: Ring) {
  if (draggedCatId.value === null) return 'border-gray-200'
  if (dragSourceRingId.value === ring.id) return 'border-gray-200'
  if (hoverTargetRingId.value === ring.id) {
    if (isCompatibleDrop(draggedCatId.value, ring.id)) {
      return 'border-green-400 bg-green-50/50 shadow-md'
    }
    return 'border-red-300 bg-red-50/50'
  }
  if (!ring.judge || ring.categories.length === 0) return 'border-gray-200 opacity-60'
  if (!isCompatibleDrop(draggedCatId.value, ring.id)) return 'border-gray-200 opacity-60'
  return 'border-gray-200'
}

function statusBadgeClass(status: string) {
  if (status === 'active') return 'bg-green-100 text-green-700'
  if (status === 'paused') return 'bg-yellow-100 text-yellow-700'
  return 'bg-gray-100 text-gray-600'
}

async function loadQueues() {
  const entries = await Promise.all(
    rings.value.map(async (r) => {
      const q = await api.rings.listQueue(r.id)
      return [r.id, q] as [number, RingQueueItem[]]
    })
  )
  ringQueues.value = new Map(entries)
}

async function loadData() {
  loading.value = true
  try {
    const [ringsData, catsData, breedsData, categoriesData] = await Promise.all([
      api.rings.list(props.showDayId),
      api.shows.cats(props.showId, props.showDayId),
      api.breeds.list(),
      api.categories.list(),
    ])
    rings.value = ringsData
    allCats.value = catsData
    breeds.value = breedsData
    categories.value = categoriesData

    await loadQueues()
  } catch (e) {
    console.error('Failed to load data:', e)
  }
  loading.value = false
}

onMounted(loadData)
</script>
