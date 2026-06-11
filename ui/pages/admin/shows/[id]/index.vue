<template>
  <div>
    <div class="mb-6 flex gap-4 items-center">
      <Btn href="/admin/shows" variant="outline" size="small">← Utställningar</Btn>
      <Btn variant="primary" @click="showAddDay = true">+ Lägg till dag</Btn>
      <Btn :href="`/admin/shows/${showId}/judges`" variant="secondary" size="small">Domare</Btn>
      <Btn variant="secondary" @click="showImport = true">Importera Katter</Btn>
      <Btn variant="outline" @click="exportShow">Exportera</Btn>
    </div>

    <ShowOnboarding :show-id="showId" :refresh-tick="catRefreshTick" @add-day="showAddDay = true" @import-cats="showImport = true" />

    <section class="bg-white rounded-xl shadow-sm border border-gray-200 mb-6">
      <div class="px-6 py-4 border-b border-gray-200">
        <div class="flex items-start justify-between gap-4">
          <div class="flex-1 space-y-2">
            <input v-model="editForm.name" type="text" class="w-full px-3 py-2 border rounded-lg text-lg font-semibold" />
            <div class="flex items-center gap-2">
              <input v-model="editForm.start_date" type="date" class="px-3 py-1.5 border rounded-lg text-sm" />
              <span class="text-gray-400">→</span>
              <input v-model="editForm.end_date" type="date" class="px-3 py-1.5 border rounded-lg text-sm" />
            </div>
          </div>
          <div class="flex items-center gap-2">
            <Btn variant="primary" size="small" @click="saveShow">Spara</Btn>
            <select v-model="editForm.status" class="text-sm px-3 py-2 border rounded-lg">
              <option value="draft">Utkast</option>
              <option value="active">Aktiv</option>
              <option value="completed">Avslutad</option>
            </select>
          </div>
        </div>
      </div>
    </section>

    <section class="bg-white rounded-xl shadow-sm border border-gray-200">
      <div class="px-6 py-4 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900">Dagar ({{ show?.days?.length || 0 }})</h2>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-gray-600">
            <tr>
              <th class="text-left px-3 py-3 font-medium">#</th>
              <th class="text-left px-3 py-3 font-medium">Namn</th>
              <th class="text-left px-3 py-3 font-medium">Bord</th>
              <th class="text-right px-3 py-3 font-medium">&nbsp;</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="day in sortedDays" :key="day.id" class="hover:bg-gray-50">
              <td class="px-3 py-3 text-gray-500">{{ day.sort_order + 1 }}</td>
              <td class="px-3 py-3 font-medium">
                <NuxtLink :to="`/admin/shows/${showId}/days/${day.id}`" class="text-black font-bold hover:text-purple-800">{{ day.name }}</NuxtLink>
              </td>
              <td class="px-3 py-3">{{ day.rings?.length || 0 }}</td>
              <td class="px-3 py-3 text-right space-x-2">
                <Btn variant="secondary" size="small" @click="deleteDay(day.id)">Ta bort</Btn>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <Teleport to="body">
      <div v-if="showAddDay" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="showAddDay = false">
        <div class="bg-white rounded-xl shadow-xl p-6 w-full max-w-lg">
          <h3 class="text-lg font-semibold mb-4">Lägg till dag</h3>
          <form @submit.prevent="submitAddDay" class="space-y-3">
            <input v-model="dayForm.name" type="text" placeholder="Dagnamn (t.ex. Dag 1, Lör, 5:e Maj)" class="w-full px-3 py-2 border rounded-lg text-sm" required />
            <div class="flex gap-3 justify-end pt-2">
              <Btn variant="outline" size="small" @click="showAddDay = false">Avbryt</Btn>
              <Btn type="submit" variant="primary" size="small">Lägg till</Btn>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <CsvImportModal v-if="showImport" :show-id="showId" @close="showImport = false; refreshCats()" />
    <div class="mt-8">
      <ShowCatsTable :show-id="showId" :refresh-tick="catRefreshTick" />
    </div>

    <ConfirmDialog :visible="confirm.visible" :title="confirm.title" :message="confirm.message" @confirm="confirm.onConfirm" @cancel="confirm.onCancel" />
  </div>
</template>

<script setup lang="ts">
import { useShowsStore } from '~/stores/shows'
import { useCatsStore } from '~/stores/cats'
import { useJudgesStore } from '~/stores/judges'
import { useConfirm } from '~/composables/useConfirm'
import ShowCatsTable from '~/components/admin/ShowCatsTable.vue'
import CsvImportModal from '~/components/admin/CsvImportModal.vue'
import ShowOnboarding from '~/components/admin/ShowOnboarding.vue'

const confirm = useConfirm()

const route = useRoute()
const showId = computed(() => Number(route.params.id))

const store = useShowsStore()
const catsStore = useCatsStore()
const judgesStore = useJudgesStore()

const show = computed(() => store.shows.find((s) => s.id === showId.value))

const sortedDays = computed(() => [...(show.value?.days || [])].sort((a, b) => a.sort_order - b.sort_order))

const editForm = reactive({ name: '', start_date: '', end_date: '', status: 'draft' as string })
const catRefreshTick = ref(0)
const showAddDay = ref(false)
const showImport = ref(false)
const dayForm = reactive({ name: '' })

async function exportShow() {
  try {
    const blob = await api.shows.exportShow(showId.value)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `show_${showId.value}_${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e: any) {
    alert(e.message)
  }
}

watch(show, (s) => {
  if (s) {
    editForm.name = s.name
    editForm.start_date = s.start_date || ''
    editForm.end_date = s.end_date || ''
    editForm.status = s.status
  }
}, { immediate: true })

async function saveShow() {
  if (!show.value) return
  await store.update(showId.value, {
    name: editForm.name,
    start_date: editForm.start_date || undefined,
    end_date: editForm.end_date || undefined,
    status: editForm.status as any,
  })
}

async function submitAddDay() {
  const days = show.value?.days || []
  const sortOrder = days.length > 0 ? Math.max(...days.map((d) => d.sort_order)) + 1 : 0
  await store.addDay(showId.value, { name: dayForm.name, sort_order: sortOrder })
  showAddDay.value = false
  dayForm.name = ''
}

async function deleteDay(dayId: number) {
  const ok = await confirm.ask('Radera denna dag och alla dess bord/köer?')
  if (!ok) return
  await store.removeDay(dayId)
}

function refreshCats() {
  catsStore.fetchAll()
  catRefreshTick.value++
}

onMounted(async () => {
  await Promise.all([
    store.fetchAll(),
    store.fetchShow(showId.value),
    catsStore.fetchAll(),
    judgesStore.fetchAll(),
  ])
})
</script>
