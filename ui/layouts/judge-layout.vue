<template>
  <div class="min-h-screen bg-gray-900 text-white flex flex-col">
    <header class="bg-gray-800 border-b border-gray-700 px-6 py-4 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <h1 class="text-2xl font-bold">Kattutställning</h1>
      </div>
      <div class="flex items-center gap-3">
        <span class="inline-block w-3 h-3 rounded-full" :class="online ? 'bg-green-500' : 'bg-red-500'" />
        <span class="text-sm text-gray-400">{{ online ? 'Online' : 'Offline' }}</span>
      </div>
    </header>
    <main class="flex-1 p-6">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
const online = ref(true)

onMounted(() => {
  if (process.client) {
    online.value = navigator.onLine
    window.addEventListener('online', () => { online.value = true })
    window.addEventListener('offline', () => { online.value = false })
  }
})
</script>
