<template>
  <Teleport to="body">
    <div class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="$emit('close')">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h3 class="text-lg font-semibold text-gray-900">Hantera raser & kategorier</h3>
          <button class="text-gray-400 hover:text-gray-600 text-xl" @click="$emit('close')">&times;</button>
        </div>

        <div class="flex border-b border-gray-200">
          <button
            class="px-6 py-3 text-sm font-medium"
            :class="tab === 'breeds' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'"
            @click="tab = 'breeds'"
          >
            Raser ({{ breeds.length }})
          </button>
          <button
            class="px-6 py-3 text-sm font-medium"
            :class="tab === 'categories' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'"
            @click="tab = 'categories'"
          >
            Kategorier ({{ categories.length }})
          </button>
        </div>

        <div class="flex-1 overflow-y-auto p-6">
          <!-- Breeds Tab -->
          <div v-if="tab === 'breeds'">
            <div class="overflow-x-auto border border-gray-200 rounded-lg">
              <table class="w-full text-sm">
                <thead class="bg-gray-50 text-gray-600">
                  <tr>
                    <th class="text-left px-4 py-2 font-medium">Kod</th>
                    <th class="text-left px-4 py-2 font-medium">Namn</th>
                    <th class="text-left px-4 py-2 font-medium">Kategori</th>
                    <th class="text-right px-4 py-2 font-medium"></th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-100">
                  <tr v-for="b in breeds" :key="b.id" class="hover:bg-gray-50">
                    <td class="px-4 py-2 font-mono">{{ b.breed_code }}</td>
                    <td v-if="editingBreed !== b.id" class="px-4 py-2">{{ b.name }}</td>
                    <td v-else class="px-4 py-2">
                      <input v-model="editBreedForm.name" class="border rounded px-2 py-1 text-sm w-full" />
                    </td>
                    <td v-if="editingBreed !== b.id" class="px-4 py-2">{{ b.category?.name || '-' }}</td>
                    <td v-else class="px-4 py-2">
                      <select v-model="editBreedForm.category_id" class="border rounded px-2 py-1 text-sm w-full">
                        <option :value="null">Ingen</option>
                        <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
                      </select>
                    </td>
                    <td class="px-4 py-2 text-right">
                      <Btn v-if="editingBreed !== b.id" variant="outline" size="small" @click="startEditBreed(b)">
                        Redigera
                      </Btn>
                      <Btn v-else variant="primary" size="small" @click="saveEditBreed(b.id)">
                        Spara
                      </Btn>
                      <Btn variant="outline" size="small" @click="deleteBreed(b.id)">
                        Radera
                      </Btn>
                    </td>
                  </tr>
                  <!-- Add breed row -->
                  <tr class="bg-gray-50">
                    <td class="px-4 py-2">
                      <input v-model="newBreed.breed_code" placeholder="Kod" class="border rounded px-2 py-1 text-sm w-full uppercase" maxlength="10" />
                    </td>
                    <td class="px-4 py-2">
                      <input v-model="newBreed.name" placeholder="Namn" class="border rounded px-2 py-1 text-sm w-full" />
                    </td>
                    <td class="px-4 py-2">
                      <select v-model="newBreed.category_id" class="border rounded px-2 py-1 text-sm w-full">
                        <option :value="null">Ingen</option>
                        <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
                      </select>
                    </td>
                    <td class="px-4 py-2 text-right">
                      <Btn variant="primary" size="small" @click="addBreed">
                        Lägg till
                      </Btn>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Categories Tab -->
          <div v-if="tab === 'categories'">
            <div class="overflow-x-auto border border-gray-200 rounded-lg">
              <table class="w-full text-sm">
                <thead class="bg-gray-50 text-gray-600">
                  <tr>
                    <th class="text-left px-4 py-2 font-medium">Namn</th>
                    <th class="text-left px-4 py-2 font-medium">Beskrivning</th>
                    <th class="text-right px-4 py-2 font-medium"></th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-100">
                  <tr v-for="c in categories" :key="c.id" class="hover:bg-gray-50">
                    <td v-if="editingCategory !== c.id" class="px-4 py-2 font-medium">{{ c.name }}</td>
                    <td v-else class="px-4 py-2">
                      <input v-model="editCategoryForm.name" class="border rounded px-2 py-1 text-sm w-full" />
                    </td>
                    <td v-if="editingCategory !== c.id" class="px-4 py-2 text-gray-500">{{ c.description || '-' }}</td>
                    <td v-else class="px-4 py-2">
                      <input v-model="editCategoryForm.description" class="border rounded px-2 py-1 text-sm w-full" placeholder="Beskrivning" />
                    </td>
                    <td class="px-4 py-2 text-right whitespace-nowrap">
                      <Btn v-if="editingCategory !== c.id" variant="outline" size="small" @click="startEditCategory(c)">
                        Redigera
                      </Btn>
                      <Btn v-else variant="primary" size="small" @click="saveEditCategory(c.id)">
                        Spara
                      </Btn>
                      <Btn variant="outline" size="small" @click="deleteCategory(c.id)">
                        Radera
                      </Btn>
                    </td>
                  </tr>
                  <!-- Add category row -->
                  <tr class="bg-gray-50">
                    <td class="px-4 py-2">
                      <input v-model="newCategory.name" placeholder="Namn" class="border rounded px-2 py-1 text-sm w-full" />
                    </td>
                    <td class="px-4 py-2">
                      <input v-model="newCategory.description" placeholder="Beskrivning" class="border rounded px-2 py-1 text-sm w-full" />
                    </td>
                    <td class="px-4 py-2 text-right">
                      <Btn variant="primary" size="small" @click="addCategory">
                        Lägg till
                      </Btn>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { api } from '~/utils/api'
import type { Breed, Category } from '~/types'

defineEmits<{ close: [] }>()

const tab = ref<'breeds' | 'categories'>('breeds')
const breeds = ref<Breed[]>([])
const categories = ref<Category[]>([])

const editingBreed = ref<number | null>(null)
const editBreedForm = reactive({ name: '', category_id: null as number | null })
const newBreed = reactive({ breed_code: '', name: '', category_id: null as number | null })

const editingCategory = ref<number | null>(null)
const editCategoryForm = reactive({ name: '', description: '' })
const newCategory = reactive({ name: '', description: '' })

async function load() {
  breeds.value = await api.breeds.list()
  categories.value = await api.categories.list()
}

async function addBreed() {
  if (!newBreed.breed_code || !newBreed.name) return
  await api.breeds.create({ ...newBreed } as any)
  newBreed.breed_code = ''
  newBreed.name = ''
  newBreed.category_id = null
  await load()
}

function startEditBreed(b: Breed) {
  editingBreed.value = b.id
  editBreedForm.name = b.name
  editBreedForm.category_id = b.category_id
}

async function saveEditBreed(id: number) {
  await api.breeds.update(id, { ...editBreedForm } as any)
  editingBreed.value = null
  await load()
}

async function deleteBreed(id: number) {
  await api.breeds.remove(id)
  await load()
}

async function addCategory() {
  if (!newCategory.name) return
  await api.categories.create({ ...newCategory } as any)
  newCategory.name = ''
  newCategory.description = ''
  await load()
}

function startEditCategory(c: Category) {
  editingCategory.value = c.id
  editCategoryForm.name = c.name
  editCategoryForm.description = c.description || ''
}

async function saveEditCategory(id: number) {
  await api.categories.update(id, { ...editCategoryForm } as any)
  editingCategory.value = null
  await load()
}

async function deleteCategory(id: number) {
  await api.categories.remove(id)
  await load()
}

onMounted(load)
</script>
