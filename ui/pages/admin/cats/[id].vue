<template>
  <div>
    <NuxtLink to="/admin/cats" class="text-sm text-gray-500 hover:text-gray-700">&larr; Alla katter</NuxtLink>
    <div v-if="cat" class="mt-4">
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div class="flex items-center justify-between mb-6">
          <div>
            <h2 class="text-2xl font-bold">{{ cat.name }}</h2>
            <p class="text-sm text-gray-500">#{{ cat.id }} &middot; {{ cat.breed_name }} ({{ cat.breed_ems }})</p>
          </div>
          <span class="text-xs px-3 py-1 rounded-full font-medium"
            :class="cat.status === 'present' ? 'bg-green-100 text-green-700' : cat.status === 'absent' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'">
            {{ cat.status }}
          </span>
        </div>

        <div class="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span class="text-gray-500">Kön</span>
            <p class="font-medium">{{ cat.gender }}</p>
          </div>
          <div>
            <span class="text-gray-500">Klass</span>
            <p class="font-medium">{{ cat.show_class }}</p>
          </div>
          <div>
            <span class="text-gray-500">Födelsedatum</span>
            <p class="font-medium">{{ cat.birth_date || '-' }}</p>
          </div>
          <div>
            <span class="text-gray-500">Registreringsnummer</span>
            <p class="font-medium">{{ cat.registration_nr || '-' }}</p>
          </div>
          <div>
            <span class="text-gray-500">Ägare</span>
            <p class="font-medium">{{ cat.owner?.name || '-' }}</p>
          </div>
        </div>
      </div>

      <div v-if="cat.days && cat.days.length" class="mt-6 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 class="text-lg font-semibold mb-3">Utställningsdagar</h3>
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-gray-600">
            <tr>
              <th class="text-left px-3 py-2 font-medium">Dag</th>
              <th class="text-left px-3 py-2 font-medium">Katalognr</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="d in cat.days" :key="d.show_day_id">
              <td class="px-3 py-2">{{ d.day_name }}</td>
              <td class="px-3 py-2 font-mono">{{ d.catalog_nr }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-else class="mt-8 text-center text-gray-400">
      Laddar...
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Cat } from '~/types'
import { api } from '~/utils/api'

const route = useRoute()
const catId = computed(() => Number(route.params.id))
const cat = ref<Cat | null>(null)

onMounted(async () => {
  cat.value = await api.cats.get(catId.value)
})
</script>
