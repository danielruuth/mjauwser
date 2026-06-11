<template>
  <div>
    <h1 class="text-2xl font-bold mb-6">Översikt</h1>

    
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <NuxtLink to="/admin/cats" class="block bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:shadow-md transition-shadow">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
            <span class="text-blue-600 text-lg">🐱</span>
          </div>
          <div>
            <p class="text-2xl font-bold text-gray-900">{{ catsStore.cats.length }}</p>
            <p class="text-sm text-gray-500">Katter</p>
          </div>
        </div>
      </NuxtLink>

      <NuxtLink to="/admin/judges" class="block bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:shadow-md transition-shadow">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
            <span class="text-green-600 text-lg">&#9878;</span>
          </div>
          <div>
            <p class="text-2xl font-bold text-gray-900">{{ judgesStore.judges.length }}</p>
            <p class="text-sm text-gray-500">Domare</p>
          </div>
        </div>
      </NuxtLink>

      <NuxtLink to="/admin/shows" class="block bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:shadow-md transition-shadow">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center flex-shrink-0">
            <span class="text-indigo-600 text-lg">&#128197;</span>
          </div>
          <div>
            <p class="text-2xl font-bold text-gray-900">{{ showsStore.shows.length }}</p>
            <p class="text-sm text-gray-500">Utställningar</p>
          </div>
        </div>
      </NuxtLink>

      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0">
            <span class="text-purple-600 text-lg">&#9776;</span>
          </div>
          <div>
            <p class="text-2xl font-bold text-gray-900">{{ breeds.length }} / {{ categories.length }}</p>
            <p class="text-sm text-gray-500">Raser / Kategorier</p>
          </div>
        </div>
      </div>
    </div>

    <BreedCategoryManager v-if="showBreedManager" @close="refreshBreeds()" />
  </div>
</template>

<script setup lang="ts">
import { useCatsStore } from '~/stores/cats'
import { useJudgesStore } from '~/stores/judges'
import { useShowsStore } from '~/stores/shows'
import { useWebSocket } from '~/composables/useWebSocket'
import type { Breed, Category } from '~/types'
import BreedCategoryManager from '~/components/admin/BreedCategoryManager.vue'
import { api } from '~/utils/api'

const catsStore = useCatsStore()
const judgesStore = useJudgesStore()
const showsStore = useShowsStore()
const ws = useWebSocket()

const breeds = ref<Breed[]>([])
const categories = ref<Category[]>([])
const showBreedManager = ref(false)

async function refreshBreeds() {
  showBreedManager.value = false
  breeds.value = await api.breeds.list()
  categories.value = await api.categories.list()
}

onMounted(async () => {
  const [breedsData, catsData] = await Promise.all([
    api.breeds.list(),
    api.categories.list(),
  ])
  breeds.value = breedsData
  categories.value = catsData
  await Promise.all([
    catsStore.fetchAll(),
    judgesStore.fetchAll(),
    showsStore.fetchAll(),
  ])
  ws.connect('admin')
  ws.on('CAT_CREATED', (p: any) => catsStore.applyEvent(p))
  ws.on('CAT_UPDATED', (p: any) => catsStore.applyEvent(p))
  ws.on('CAT_STATUS_UPDATED', (p: any) => catsStore.applyEvent(p))
  ws.on('CAT_DELETED', (p: any) => catsStore.applyDelete(p))
  ws.on('JUDGE_CREATED', (p: any) => judgesStore.applyEvent(p))
  ws.on('JUDGE_UPDATED', (p: any) => judgesStore.applyEvent(p))
  ws.on('JUDGE_DELETED', (p: any) => judgesStore.applyDelete(p))
  ws.on('SHOW_CREATED', (p: any) => showsStore.shows.push(p.show))
  ws.on('SHOW_UPDATED', (p: any) => {
    const idx = showsStore.shows.findIndex((s) => s.id === p.show.id)
    if (idx !== -1) showsStore.shows[idx] = p.show
  })
  ws.on('SHOW_DELETED', (p: any) => {
    showsStore.shows = showsStore.shows.filter((s) => s.id !== p.show_id)
  })
  ws.onState((state: any) => {
    if (state.cats) catsStore.cats = state.cats
    if (state.judges) judgesStore.judges = state.judges
    if (state.shows) showsStore.shows = state.shows
    if (state.breeds) breeds.value = state.breeds
    if (state.categories) categories.value = state.categories
  })
})

onUnmounted(() => {
  ws.disconnect()
})
</script>
