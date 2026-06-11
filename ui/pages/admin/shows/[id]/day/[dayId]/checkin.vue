<template>
  <div class="max-w-4xl mx-auto">
    <div class="mb-6 flex gap-4 items-center">
      <Btn :href="`/admin/shows/${showId}/days/${dayId}`" variant="outline" size="small">← Tillbaka</Btn>
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Checka in katter</h1>
        <p v-if="day" class="text-sm text-gray-500">{{ day.name }}</p>
      </div>
    </div>

    <div v-if="loading" class="text-sm text-gray-400 text-center py-8">Laddar...</div>

    <template v-else>
      <!-- Unchecked -->
      <section class="bg-white rounded-xl shadow-sm border border-gray-200 mb-6">
        <div class="px-6 py-4 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-900">Inte incheckade ({{ unchecked.length }})</h2>
        </div>
        <div v-if="unchecked.length === 0" class="px-6 py-8 text-sm text-gray-400 text-center">
          Alla katter är incheckade eller absade.
        </div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-gray-50 text-gray-600">
              <tr>
                <th class="text-left px-3 py-3 font-medium">Katalognr</th>
                <th class="text-left px-3 py-3 font-medium">Namn</th>
                <th class="text-left px-3 py-3 font-medium">Ras (EMS)</th>
                <th class="text-left px-3 py-3 font-medium">Klass</th>
                <th class="text-right px-3 py-3 font-medium"></th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-for="cat in unchecked" :key="cat.id" class="hover:bg-gray-50">
                <td class="px-3 py-3 font-mono">
                  <span v-if="cat.days && cat.days.length > 0">#{{ cat.days[0].catalog_nr }}</span>
                  <span v-else class="text-gray-400">—</span>
                </td>
                <td class="px-3 py-3 font-medium">{{ cat.name }}</td>
                <td class="px-3 py-3">{{ cat.breed_name }} ({{ cat.breed_ems }})</td>
                <td class="px-3 py-3">{{ cat.show_class }}</td>
                <td class="px-3 py-3 text-right space-x-2">
                  <Btn variant="primary" size="small" @click="checkIn(cat)">Checka in</Btn>
                  <Btn variant="outline" size="small" @click="markAbsent(cat)">Absa</Btn>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- Checked in / Absent -->
      <section class="bg-white rounded-xl shadow-sm border border-gray-200">
        <div class="px-6 py-4 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-900">Incheckade / Absade ({{ processed.length }})</h2>
        </div>
        <div v-if="processed.length === 0" class="px-6 py-8 text-sm text-gray-400 text-center">
          Inga katter har checkats in eller absats än.
        </div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-gray-50 text-gray-600">
              <tr>
                <th class="text-left px-3 py-3 font-medium">Katalognr</th>
                <th class="text-left px-3 py-3 font-medium">Namn</th>
                <th class="text-left px-3 py-3 font-medium">Ras (EMS)</th>
                <th class="text-left px-3 py-3 font-medium">Klass</th>
                <th class="text-left px-3 py-3 font-medium">Status</th>
                <th class="text-right px-3 py-3 font-medium"></th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-for="cat in processed" :key="cat.id" class="hover:bg-gray-50">
                <td class="px-3 py-3 font-mono">
                  <span v-if="cat.days && cat.days.length > 0">#{{ cat.days[0].catalog_nr }}</span>
                  <span v-else class="text-gray-400">—</span>
                </td>
                <td class="px-3 py-3 font-medium">{{ cat.name }}</td>
                <td class="px-3 py-3">{{ cat.breed_name }} ({{ cat.breed_ems }})</td>
                <td class="px-3 py-3">{{ cat.show_class }}</td>
                <td class="px-3 py-3">
                  <span v-if="catDayStatus(cat) === 'present'" class="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full font-medium bg-green-100 text-green-700">
                    <Check class="w-3 h-3" /> In
                  </span>
                  <span v-else class="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full font-medium bg-red-100 text-red-700">
                    <X class="w-3 h-3" /> Abs
                  </span>
                </td>
                <td class="px-3 py-3 text-right">
                  <Btn variant="outline" size="small" @click="undoStatus(cat)">Ångra</Btn>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { Check, X } from '@lucide/vue'
import { api } from '~/utils/api'
import { useShowsStore } from '~/stores/shows'
import type { Cat } from '~/types'

const route = useRoute()
const showId = computed(() => Number(route.params.id))
const dayId = computed(() => Number(route.params.dayId))

const showsStore = useShowsStore()

const loading = ref(true)
const cats = ref<Cat[]>([])

const show = computed(() => showsStore.shows.find((s) => s.id === showId.value))
const day = computed(() => show.value?.days?.find((d) => d.id === dayId.value))

const unchecked = computed(() => cats.value.filter((c) => catDayStatus(c) === 'unchecked'))
const processed = computed(() => cats.value.filter((c) => !['unchecked', 'judged'].includes(catDayStatus(c))))

function catDayStatus(cat: Cat): string {
  const dayEntry = cat.days?.find((d) => d.show_day_id === dayId.value)
  return dayEntry?.status || 'unchecked'
}

async function loadCats() {
  loading.value = true
  try {
    cats.value = await api.shows.cats(showId.value, dayId.value)
  } catch {
    cats.value = []
  } finally {
    loading.value = false
  }
}

async function checkIn(cat: Cat) {
  try {
    await api.cats.updateDayStatus(cat.id, dayId.value, 'present')
    await loadCats()
  } catch (e: any) {
    alert(e.message)
  }
}

async function markAbsent(cat: Cat) {
  const ok = confirm(`Stryk ${cat.name} (#${cat.days?.[0]?.catalog_nr || cat.id}) för denna dag?`)
  if (!ok) return
  try {
    await api.cats.updateDayStatus(cat.id, dayId.value, 'absent')
    await loadCats()
  } catch (e: any) {
    alert(e.message)
  }
}

async function undoStatus(cat: Cat) {
  try {
    await api.cats.updateDayStatus(cat.id, dayId.value, 'unchecked')
    await loadCats()
  } catch (e: any) {
    alert(e.message)
  }
}

onMounted(() => {
  loadCats()
})
</script>
