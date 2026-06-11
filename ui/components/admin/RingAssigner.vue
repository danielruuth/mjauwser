<template>
  <div class="space-y-4">
    <div v-if="loading" class="text-sm text-gray-500 py-2">Laddar data...</div>
    <template v-else-if="unassignedCount === 0">
      <p class="text-sm text-gray-500 mb-3">Alla katter är tilldelade</p>
      <Btn :href="`/admin/shows/${showId}/days/manual/${showDayId}`" variant="outline" size="small">
        → Manuell tilldelning
      </Btn>
    </template>
    <template v-else>
      <div class="grid grid-cols-2 gap-4">
        <div class="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
          <p class="text-2xl font-bold text-green-700">{{ assignedCount }}</p>
          <p class="text-sm text-green-600">Tilldelade katter</p>
        </div>
        <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center">
          <p class="text-2xl font-bold text-yellow-700">{{ unassignedCount }}</p>
          <p class="text-sm text-yellow-600">Otilldelade katter</p>
        </div>
      </div>

      <div class="flex justify-center pt-2">
        <Btn variant="primary" :disabled="unassignedCount === 0 || assigning" @click="autoAssign">
          {{ assigning ? 'Fördelar katter...' : 'Fördela katter' }}
        </Btn>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { api } from '~/utils/api'
import type { Breed, Category, Cat, Ring } from '~/types'

const props = defineProps<{
  showDayId: number
  showId: number
  rings: Ring[]
}>()

const emit = defineEmits<{ assigned: [] }>()

const loading = ref(true)
const assigning = ref(false)
const allCats = ref<Cat[]>([])
const breeds = ref<Breed[]>([])
const categories = ref<Category[]>([])
const assignedCatIds = ref<Set<number>>(new Set())

const totalCats = computed(() => allCats.value.length)
const unassignedCount = computed(() => totalCats.value - assignedCatIds.value.size)
const assignedCount = computed(() => assignedCatIds.value.size)

async function loadData() {
  loading.value = true
  const [catsData, breedsData, categoriesData] = await Promise.all([
    api.shows.cats(props.showId, props.showDayId),
    api.breeds.list(),
    api.categories.list(),
  ])
  allCats.value = catsData
  breeds.value = breedsData
  categories.value = categoriesData

  const queuePromises = props.rings.map((r) => api.rings.listQueue(r.id))
  const queues = await Promise.all(queuePromises)
  const assigned = new Set<number>()
  for (const q of queues) {
    for (const item of q) {
      assigned.add(item.cat_id)
    }
  }
  assignedCatIds.value = assigned
  loading.value = false
}

async function autoAssign() {
  assigning.value = true

  const breedCategoryMap = new Map<string, number>()
  for (const b of breeds.value) {
    if (b.category_id) breedCategoryMap.set(b.breed_code, b.category_id)
  }

  const categoryBreeds = new Map<number, string[]>()
  for (const b of breeds.value) {
    if (b.category_id) {
      const list = categoryBreeds.get(b.category_id) || []
      list.push(b.breed_code)
      categoryBreeds.set(b.category_id, list)
    }
  }

  const ringCompatibleBreeds = new Map<number, Set<string>>()
  for (const ring of props.rings) {
    const compatible = new Set<string>()
    if (ring.judge) {
      for (const cat of ring.judge.categories) {
        const breedsInCat = categoryBreeds.get(cat.id) || []
        for (const b of breedsInCat) compatible.add(b)
      }
    }
    ringCompatibleBreeds.set(ring.id, compatible)
  }

  const breedGroups = new Map<string, Cat[]>()
  for (const cat of allCats.value) {
    if (assignedCatIds.value.has(cat.id)) continue
    const group = breedGroups.get(cat.breed_ems) || []
    group.push(cat)
    breedGroups.set(cat.breed_ems, group)
  }

  const sortedGroups = [...breedGroups.entries()].sort((a, b) => b[1].length - a[1].length)

  const assignments: { ringId: number; catIds: number[] }[] = []

  for (const [breedCode, cats] of sortedGroups) {
    const compatibleRings = props.rings.filter((r) =>
      ringCompatibleBreeds.get(r.id)?.has(breedCode)
    )
    if (compatibleRings.length === 0) continue

    const ringWithCounts = compatibleRings
      .map((r) => ({
        ring: r,
        count: assignments
          .filter((a) => a.ringId === r.id)
          .reduce((sum, a) => sum + a.catIds.length, 0),
      }))
      .sort((a, b) => a.count - b.count)

    const groupSize = cats.length

    if (groupSize <= 4) {
      const target = ringWithCounts[0]
      assignments.push({ ringId: target.ring.id, catIds: cats.map((c) => c.id) })
    } else {
      const maxRings = Math.min(compatibleRings.length, Math.floor(groupSize / 3))
      const basePerRing = Math.floor(groupSize / maxRings)
      const remainder = groupSize % maxRings

      let catIdx = 0
      for (let i = 0; i < maxRings; i++) {
        const target = ringWithCounts[i]
        const count = basePerRing + (i < remainder ? 1 : 0)
        const catIds = cats.slice(catIdx, catIdx + count).map((c) => c.id)
        assignments.push({ ringId: target.ring.id, catIds })
        catIdx += count
      }
    }
  }

  for (const a of assignments) {
    await api.rings.queue.add(a.ringId, a.catIds)
  }

  await loadData()
  assigning.value = false
  emit('assigned')
}

onMounted(loadData)
</script>
