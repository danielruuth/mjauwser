<template>
  <div>
    <div class="mb-4 flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold mt-1">Katter ({{ catsStore.cats.length }})</h2>
      </div>
      <div class="flex gap-3">
        <input v-model="search" type="text" placeholder="Sök på namn eller ras..." class="px-3 py-1.5 border border-gray-300 rounded-lg text-sm w-64" />
        <Btn variant="primary" @click="openAddCat()">+ Lägg till katt</Btn>
        <Btn variant="secondary" @click="showBreedManager = true">Hantera raser & kategorier</Btn>
      </div>
    </div>

    <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 text-gray-600">
          <tr>
            <th class="text-left px-3 py-3 font-medium">Namn</th>
            <th class="text-left px-3 py-3 font-medium">Ras</th>
            <th class="text-left px-3 py-3 font-medium">Kön</th>
            <th class="text-left px-3 py-3 font-medium">Klass</th>
            <th class="text-left px-3 py-3 font-medium">Födelsedatum</th>
            <th class="text-left px-3 py-3 font-medium">Reg Nr</th>
            <th class="text-left px-3 py-3 font-medium">Ägare</th>
            <th class="text-left px-3 py-3 font-medium">Status</th>
            <th class="text-right px-3 py-3 font-medium">&nbsp;</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-for="cat in filteredCats" :key="cat.id" class="hover:bg-gray-50">
            <td class="px-3 py-1">
              <NuxtLink :to="`/admin/cats/${cat.id}`" class="font-bold text-black hover:text-purple-800">{{ cat.name }}</NuxtLink>
            </td>
            <td class="px-3 py-1">{{ cat.breed_ems }}</td>
            <td class="px-3 py-1">{{ cat.gender }}</td>
            <td class="px-3 py-1">{{ cat.show_class }}</td>
            <td class="px-3 py-1">{{ cat.birth_date || '-' }}</td>
            <td class="px-3 py-1">{{ cat.registration_nr || '-' }}</td>
            <td class="px-3 py-1">{{ cat.owner?.name || '-' }}</td>
            <td class="px-3 py-1">
              <select :value="cat.status" class="text-xs px-2 py-1 border rounded" :class="statusClass(cat.status)" @change="catsStore.updateStatus(cat.id, ($event.target as HTMLSelectElement).value)">
                <option value="present">Närvarande</option>
                <option value="absent">Struken</option>
                <option value="judged">Bedömd</option>
              </select>
            </td>
            <td class="w-[140px] px-3 py-3 text-right flex flex-nowrap justify-end flex-row gap-2">
              <Btn size="small" variant="secondary" @click="openEditCat(cat)">Redigera</Btn>
              <Btn size="small" variant="secondary" @click="catsStore.remove(cat.id)">Radera</Btn>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add Cat Modal -->
    <Teleport to="body">
      <div v-if="showAddCat" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="showAddCat = false">
        <div class="bg-white rounded-xl shadow-xl p-6 w-full max-w-lg">
          <h3 class="text-lg font-semibold mb-4">Lägg till katt</h3>
          <form @submit.prevent="submitCat" class="space-y-3">
            <div class="grid grid-cols-2 gap-3">
              <input v-model="form.name" type="text" placeholder="Namn" class="w-full px-3 py-2 border rounded-lg text-sm" required />
              <select v-model="form.breed_ems" class="w-full px-3 py-2 border rounded-lg text-sm" required>
                <option value="" disabled>Välj ras...</option>
                <option v-for="b in breeds" :key="b.breed_code" :value="b.breed_code">{{ b.breed_code }} - {{ b.name }}</option>
              </select>
              <select v-model="form.gender" class="w-full px-3 py-2 border rounded-lg text-sm" required>
                <option value="" disabled>Kön...</option>
                <option value="M">M</option>
                <option value="F">F</option>
              </select>
              <input v-model="form.show_class" type="text" placeholder="Klass" class="w-full px-3 py-2 border rounded-lg text-sm" required />
              <input v-model="form.birth_date" type="text" placeholder="Födelsedatum (YYYY-MM-DD)" class="w-full px-3 py-2 border rounded-lg text-sm" />
              <input v-model="form.registration_nr" type="text" placeholder="Registreringsnummer" class="w-full px-3 py-2 border rounded-lg text-sm" />
              <OwnerPicker v-model="form.ownerValue" placeholder="Ägare" />
            </div>
            <div class="flex gap-3 justify-end pt-2">
              <Btn variant="outline" size="small" @click="showAddCat = false">Avbryt</Btn>
              <Btn type="submit" variant="primary" size="small">Lägg till</Btn>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Edit Cat Modal -->
    <Teleport to="body">
      <div v-if="editingCat" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="editingCat = null">
        <div class="bg-white rounded-xl shadow-xl p-6 w-full max-w-lg">
          <h3 class="text-lg font-semibold mb-4">Redigera katt</h3>
          <form @submit.prevent="submitCatEdit" class="space-y-3">
            <div class="grid grid-cols-2 gap-3">
              <input v-model="form.name" type="text" placeholder="Namn" class="w-full px-3 py-2 border rounded-lg text-sm" required />
              <select v-model="form.breed_ems" class="w-full px-3 py-2 border rounded-lg text-sm" required>
                <option value="" disabled>Välj ras...</option>
                <option v-for="b in breeds" :key="b.breed_code" :value="b.breed_code">{{ b.breed_code }} - {{ b.name }}</option>
              </select>
              <select v-model="form.gender" class="w-full px-3 py-2 border rounded-lg text-sm" required>
                <option value="" disabled>Kön...</option>
                <option value="M">M</option>
                <option value="F">F</option>
              </select>
              <input v-model="form.show_class" type="text" placeholder="Klass" class="w-full px-3 py-2 border rounded-lg text-sm" required />
              <input v-model="form.birth_date" type="text" placeholder="Födelsedatum (ÅÅÅÅ-MM-DD)" class="w-full px-3 py-2 border rounded-lg text-sm" />
              <input v-model="form.registration_nr" type="text" placeholder="Registreringsnummer" class="w-full px-3 py-2 border rounded-lg text-sm" />
              <OwnerPicker v-model="form.ownerValue" placeholder="Ägare" />
            </div>
            <div class="flex gap-3 justify-end pt-2">
              <Btn variant="outline" size="small" @click="editingCat = null">Avbryt</Btn>
              <Btn type="submit" variant="primary" size="small">Spara</Btn>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Breed Manager Modal -->
    <BreedCategoryManager v-if="showBreedManager" @close="refreshBreeds()" />
  </div>
</template>

<script setup lang="ts">
import { useCatsStore } from '~/stores/cats'
import { useWebSocket } from '~/composables/useWebSocket'
import type { Cat, Breed } from '~/types'
import BreedCategoryManager from '~/components/admin/BreedCategoryManager.vue'
import OwnerPicker from '~/components/admin/OwnerPicker.vue'
import { api } from '~/utils/api'

const catsStore = useCatsStore()
const ws = useWebSocket()

const breeds = ref<Breed[]>([])
const search = ref('')
const showAddCat = ref(false)
const showBreedManager = ref(false)
const editingCat = ref<Cat | null>(null)

const form = reactive({
  name: '',
  breed_ems: '',
  gender: '',
  show_class: '',
  birth_date: '',
  registration_nr: '',
  ownerValue: null as { owner_id?: number; owner_name?: string } | null,
})

async function refreshBreeds() {
  showBreedManager.value = false
  breeds.value = await api.breeds.list()
}

const filteredCats = computed(() => {
  const q = search.value.toLowerCase()
  if (!q) return catsStore.cats
  return catsStore.cats.filter((c) =>
    c.name.toLowerCase().includes(q) || c.breed_name.toLowerCase().includes(q)
  )
})

function statusClass(status: string) {
  if (status === 'present') return 'border-green-300 text-green-700'
  if (status === 'absent') return 'border-red-300 text-red-700'
  return 'border-gray-300 text-gray-700'
}

function resetForm() {
  form.name = ''
  form.breed_ems = ''
  form.gender = ''
  form.show_class = ''
  form.birth_date = ''
  form.registration_nr = ''
  form.ownerValue = null
}

function openAddCat() {
  resetForm()
  showAddCat.value = true
}

async function submitCat() {
  const payload: Record<string, any> = {
    name: form.name,
    breed_ems: form.breed_ems,
    gender: form.gender,
    show_class: form.show_class,
    birth_date: form.birth_date || undefined,
    registration_nr: form.registration_nr || undefined,
    status: 'present',
  }
  if (form.ownerValue?.owner_id) payload.owner_id = form.ownerValue.owner_id
  else if (form.ownerValue?.owner_name) payload.owner_name = form.ownerValue.owner_name
  await catsStore.create(payload as any)
  showAddCat.value = false
  resetForm()
}

function openEditCat(cat: Cat) {
  form.name = cat.name
  form.breed_ems = cat.breed_ems
  form.gender = cat.gender
  form.show_class = cat.show_class
  form.birth_date = cat.birth_date || ''
  form.registration_nr = cat.registration_nr || ''
  form.ownerValue = cat.owner ? { owner_id: cat.owner.id } : null
  editingCat.value = cat
}

async function submitCatEdit() {
  if (!editingCat.value) return
  const payload: Record<string, any> = {
    name: form.name,
    breed_ems: form.breed_ems,
    gender: form.gender,
    show_class: form.show_class,
    birth_date: form.birth_date || undefined,
    registration_nr: form.registration_nr || undefined,
  }
  if (form.ownerValue?.owner_id) payload.owner_id = form.ownerValue.owner_id
  else if (form.ownerValue?.owner_name) payload.owner_name = form.ownerValue.owner_name
  else payload.owner_id = null
  await catsStore.update(editingCat.value.id, payload as any)
  editingCat.value = null
  resetForm()
}

onMounted(async () => {
  breeds.value = await api.breeds.list()
  await catsStore.fetchAll()
  ws.connect('admin')
  ws.on('CAT_CREATED', (p: any) => catsStore.applyEvent(p))
  ws.on('CAT_UPDATED', (p: any) => catsStore.applyEvent(p))
  ws.on('CAT_STATUS_UPDATED', (p: any) => catsStore.applyEvent(p))
  ws.on('CAT_DELETED', (p: any) => catsStore.applyDelete(p))
  ws.onState((state: any) => {
    catsStore.cats = state.cats
    if (state.breeds) breeds.value = state.breeds
  })
})

onUnmounted(() => {
  ws.disconnect()
})
</script>
