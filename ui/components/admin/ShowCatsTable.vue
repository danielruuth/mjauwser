<template>
  <section class="bg-white rounded-xl shadow-sm border border-gray-200">
    <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between gap-4">
      <h2 class="text-lg font-semibold text-gray-900">Registrerade katter ({{ totalCount }})</h2>
      <input v-model="search" type="text" placeholder="Sök på namn, ras eller katalognummer..." class="px-3 py-1.5 border border-gray-300 rounded-lg text-sm w-72" />
    </div>

    <div v-if="loading" class="px-6 py-8 text-sm text-gray-400 text-center">Laddar...</div>
    <div v-else-if="filtered.length === 0" class="px-6 py-8 text-sm text-gray-400 text-center">
      {{ search ? 'Inga katter matchade sökningen.' : 'Inga katter registrerade än.' }}
    </div>
    <div v-else class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 text-gray-600">
          <tr>
            <th class="text-left px-3 py-3 font-medium">Katalognr</th>
            <th class="text-left px-3 py-3 font-medium">Namn</th>
            <th class="text-left px-3 py-3 font-medium">Ras (EMS)</th>
            <th class="text-left px-3 py-3 font-medium">Kön</th>
            <th class="text-left px-3 py-3 font-medium">Klass</th>
            <th class="text-left px-3 py-3 font-medium">Status</th>
            <th v-if="!dayId" class="text-left px-3 py-3 font-medium">Dag(ar)</th>
            <th v-if="dayId" class="text-left px-3 py-3 font-medium"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-for="cat in pageItems" :key="cat.id" class="hover:bg-gray-50">
            <td class="px-3 py-3 font-mono">
              <span v-if="cat.days && cat.days.length > 0">#{{ cat.days[0].catalog_nr }}</span>
              <span v-else class="text-gray-400">—</span>
            </td>
            <td class="px-3 py-3">
              <div class="flex items-center gap-1.5">
                <span class="font-medium">{{ cat.name }}</span>
                <TriangleAlert v-if="isUnassigned(cat.id)"
                  class="w-4 h-4 text-amber-500 cursor-pointer shrink-0 hover:text-amber-700"
                  @click.stop="openAssignModal(cat)" />
              </div>
            </td>
            <td class="px-3 py-3">{{ cat.breed_name }} ({{ cat.breed_ems }})</td>
            <td class="px-3 py-3">{{ cat.gender }}</td>
            <td class="px-3 py-3">{{ cat.show_class }}</td>
            <td class="px-3 py-3">
              <span class="text-xs px-2 py-1 rounded-full font-medium" :class="catDayStatus(cat) === 'present' ? 'bg-green-100 text-green-700' : catDayStatus(cat) === 'absent' ? 'bg-red-100 text-red-700' : catDayStatus(cat) === 'unchecked' ? 'bg-amber-100 text-amber-700' : 'bg-gray-100 text-gray-700'">
                {{ catDayStatus(cat) === 'present' ? 'Närvarande' : catDayStatus(cat) === 'absent' ? 'Struken' : catDayStatus(cat) === 'unchecked' ? 'Ej incheckad' : 'Bedömd' }}
              </span>
            </td>
            <td v-if="dayId" class="px-3 py-3 text-right">
              <Btn v-if="catDayStatus(cat) === 'unchecked'" variant="outline" size="small" @click="checkIn(cat)">
                Checka in
              </Btn>
              <Btn v-else-if="catDayStatus(cat) !== 'absent'" variant="outline" size="small" @click="markAbsent(cat)">
                Absa
              </Btn>
              <Btn v-else variant="primary" size="small" @click="restorePresent(cat)">
                Återställ
              </Btn>
            </td>
            <td v-if="!dayId && cat.days" class="px-3 py-3 text-sm text-gray-600">
              <span v-for="(d, i) in cat.days" :key="d.show_day_id">
                {{ i > 0 ? ', ' : '' }}{{ d.day_name }} (#{{ d.catalog_nr }})
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="totalPages > 1" class="px-6 py-3 border-t border-gray-200 flex items-center justify-between gap-4 text-sm">
      <div class="flex items-center gap-2">
        <span class="text-gray-500">Visa per sida:</span>
        <select v-model.number="perPage" class="px-2 py-1 border rounded text-xs">
          <option :value="10">10</option>
          <option :value="25">25</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
        </select>
      </div>
      <div class="flex items-center gap-2">
        <span class="text-gray-500">Visar {{ pageStart }}–{{ pageEnd }} av {{ totalCount }} katter</span>
        <Btn variant="outline" size="small" :disabled="page === 1" @click="page--">
          Föregående
        </Btn>
        <span class="text-gray-700">Sida {{ page }} av {{ totalPages }}</span>
        <Btn variant="outline" size="small" :disabled="page === totalPages" @click="page++">
          Nästa
        </Btn>
      </div>
    </div>
  </section>

  <Teleport to="body">
    <div v-if="showAssignModal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="showAssignModal = false">
      <div class="bg-white rounded-xl shadow-xl p-6 w-full max-w-md mx-4">
        <h3 class="text-lg font-semibold mb-4">Tilldela {{ assignTarget?.name }} till domarbord</h3>
        <div class="space-y-4">
          <select v-model.number="selectedRingId" class="w-full px-3 py-2 border rounded-lg text-sm">
            <option :value="null" disabled>Välj domarbord...</option>
            <option v-for="ring in rings" :key="ring.id" :value="ring.id">
              Bord {{ ring.ring_number }}{{ ring.judge ? ' — ' + ring.judge.name : '' }}
            </option>
          </select>
          <div class="flex gap-3 justify-end pt-2">
            <Btn variant="outline" size="small" @click="showAssignModal = false">Avbryt</Btn>
            <Btn variant="primary" size="small" :disabled="!selectedRingId" @click="assignCat">
              Tilldela
            </Btn>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import type { Cat, Ring } from '~/types'
import { TriangleAlert } from '@lucide/vue'
import { api } from '~/utils/api'

const props = defineProps<{
  showId: number
  dayId?: number
  perPage?: number
  refreshTick?: number
}>()

const loading = ref(true)
const allCats = ref<Cat[]>([])
const search = ref('')
const page = ref(1)
const perPage = ref(25)

const rings = ref<Ring[]>([])
const assignedCatIds = ref<Set<number>>(new Set())
const showAssignModal = ref(false)
const assignTarget = ref<{ id: number; name: string } | null>(null)
const selectedRingId = ref<number | null>(null)

function catDayStatus(cat: Cat): string {
  const dayEntry = cat.days?.find((d) => d.show_day_id === props.dayId)
  return dayEntry?.status || cat.status || 'unchecked'
}

async function markAbsent(cat: Cat) {
  if (!props.dayId) return
  const ok = confirm(`Stryk ${cat.name} (#${cat.days?.[0]?.catalog_nr || cat.id}) för denna dag?`)
  if (!ok) return
  try {
    await api.cats.updateDayStatus(cat.id, props.dayId, 'absent')
    await load()
  } catch (e: any) {
    alert(e.message)
  }
}

async function checkIn(cat: Cat) {
  if (!props.dayId) return
  try {
    await api.cats.updateDayStatus(cat.id, props.dayId, 'present')
    await load()
  } catch (e: any) {
    alert(e.message)
  }
}

async function restorePresent(cat: Cat) {
  if (!props.dayId) return
  const ok = confirm(`Återställ ${cat.name} till närvarande?`)
  if (!ok) return
  try {
    await api.cats.updateDayStatus(cat.id, props.dayId, 'present')
    await load()
  } catch (e: any) {
    alert(e.message)
  }
}

async function loadAssignedCats() {
  if (!props.dayId) return
  rings.value = await api.rings.list(props.dayId)
  const queues = await Promise.all(rings.value.map(r => api.rings.listQueue(r.id)))
  const set = new Set<number>()
  for (const q of queues) for (const item of q) set.add(item.cat_id)
  assignedCatIds.value = set
}

function isUnassigned(catId: number): boolean {
  return !!props.dayId && !assignedCatIds.value.has(catId)
}

function openAssignModal(cat: { id: number; name: string }) {
  assignTarget.value = cat
  selectedRingId.value = null
  showAssignModal.value = true
}

async function assignCat() {
  if (!selectedRingId.value || !assignTarget.value) return
  await api.rings.queue.add(selectedRingId.value, [assignTarget.value.id])
  showAssignModal.value = false
  assignTarget.value = null
  await loadAssignedCats()
}

const filtered = computed(() => {
  const q = search.value.toLowerCase()
  if (!q) return allCats.value
  return allCats.value.filter((c) =>
    c.name.toLowerCase().includes(q) ||
    c.breed_name.toLowerCase().includes(q) ||
    c.breed_ems.toLowerCase().includes(q) ||
    (c.days && c.days.some((d) => String(d.catalog_nr).includes(q)))
  )
})

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / perPage.value)))
const totalCount = computed(() => filtered.value.length)

const pageItems = computed(() => {
  const start = (page.value - 1) * perPage.value
  return filtered.value.slice(start, start + perPage.value)
})

const pageStart = computed(() => (page.value - 1) * perPage.value + 1)
const pageEnd = computed(() => Math.min(page.value * perPage.value, filtered.value.length))

watch([search, perPage], () => {
  page.value = 1
})

watch(() => props.refreshTick, () => {
  load()
})

async function load() {
  allCats.value = await api.shows.cats(props.showId, props.dayId)
  if (props.dayId) await loadAssignedCats()
  loading.value = false
}

onMounted(load)
</script>
