<template>
  <div>
    <div class="mb-6 flex gap-4 items-center">
      <Btn variant="primary" @click="showCreate = true">+ Skapa utställning</Btn>
      <Btn variant="secondary" @click="importFileInput?.click()">Importera</Btn>
      <input ref="importFileInput" type="file" accept=".json" class="hidden" @change="onImportFile" />
    </div>

    <section class="bg-white rounded-xl shadow-sm border border-gray-200">
      <div class="px-6 py-4 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900">Utställningar ({{ shows.length }})</h2>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-gray-600">
            <tr>
              <th class="text-left px-3 py-3 font-medium">Namn</th>
              <th class="text-left px-3 py-3 font-medium">Datum</th>
              <th class="text-left px-3 py-3 font-medium">Dagar</th>
              <th class="text-left px-3 py-3 font-medium">Status</th>
              <th class="text-right px-3 py-3 font-medium">Åtgärder</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="show in shows" :key="show.id" class="hover:bg-gray-50">
              <td class="px-3 py-3 font-medium">
                <NuxtLink :to="`/admin/shows/${show.id}`" class="text-black font-bold hover:text-purple-800">{{ show.name }}</NuxtLink>
              </td>
              <td class="px-3 py-3 text-gray-600">{{ show.start_date || '-' }} → {{ show.end_date || '-' }}</td>
              <td class="px-3 py-3">{{ show.days?.length || 0 }}</td>
              <td class="px-3 py-3">
                <span class="text-xs px-2 py-1 rounded-full font-medium" :class="statusClass(show.status)">{{ show.status }}</span>
              </td>
              <td class="px-3 py-3 text-right space-x-2">
                <Btn variant="outline" size="small" @click="deleteShow(show.id)">Radera</Btn>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <Teleport to="body">
      <div v-if="showCreate" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="showCreate = false">
        <div class="bg-white rounded-xl shadow-xl p-6 w-full max-w-lg">
          <h3 class="text-lg font-semibold mb-4">Skapa utställning</h3>
          <form @submit.prevent="submitCreate" class="space-y-3">
            <input v-model="form.name" type="text" placeholder="Utställningsnamn" class="w-full px-3 py-2 border rounded-lg text-sm" required />
            <div class="grid grid-cols-2 gap-3">
              <input v-model="form.start_date" type="text" placeholder="Startdatum (YYYY-MM-DD)" class="w-full px-3 py-2 border rounded-lg text-sm" />
              <input v-model="form.end_date" type="text" placeholder="Slutdatum (YYYY-MM-DD)" class="w-full px-3 py-2 border rounded-lg text-sm" />
            </div>
            <div class="flex gap-3 justify-end pt-2">
              <Btn variant="outline" size="small" @click="showCreate = false">Avbryt</Btn>
              <Btn type="submit" variant="primary" size="small">Skapa</Btn>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <ConfirmDialog :visible="confirm.visible" :title="confirm.title" :message="confirm.message" @confirm="confirm.onConfirm" @cancel="confirm.onCancel" />
  </div>
</template>

<script setup lang="ts">
import { useShowsStore } from '~/stores/shows'
import { useConfirm } from '~/composables/useConfirm'

const confirm = useConfirm()

const store = useShowsStore()
const shows = computed(() => store.shows)

const showCreate = ref(false)
const form = reactive({ name: '', start_date: '', end_date: '' })
const importFileInput = ref<HTMLInputElement>()
const router = useRouter()
const importing = ref(false)

async function onImportFile(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  importing.value = true
  try {
    const text = await file.text()
    const data = JSON.parse(text)
    const result = await api.shows.importShow(data)
    alert(`Importerade show "${data.show?.name || 'okänd'}" (ID ${result.show_id})\n` +
      `${result.categories_found} kategorier, ${result.breeds_found} raser,\n` +
      `${result.judges_created} domare, ${result.cats_created} katter,\n` +
      `${result.queue_entries} kö-poster`)
    await store.fetchAll()
    router.push(`/admin/shows/${result.show_id}`)
  } catch (e: any) {
    alert(`Import misslyckades: ${e.message}`)
  } finally {
    importing.value = false
    if (importFileInput.value) importFileInput.value.value = ''
  }
}

function statusClass(status: string) {
  if (status === 'active') return 'bg-green-100 text-green-700'
  if (status === 'completed') return 'bg-gray-100 text-gray-700'
  return 'bg-yellow-100 text-yellow-700'
}

async function submitCreate() {
  await store.create({ ...form } as any)
  showCreate.value = false
  form.name = ''
  form.start_date = ''
  form.end_date = ''
}

async function deleteShow(id: number) {
  const ok = await confirm.ask('Radera denna utställning och alla dess dagar/bord?')
  if (!ok) return
  await store.remove(id)
}

onMounted(() => store.fetchAll())
</script>
