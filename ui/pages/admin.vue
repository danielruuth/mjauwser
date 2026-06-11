<template>
  <div>
    <div class="mx-auto max-w-7xl">
      <main class="p-4">
        <NuxtPage />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default', middleware: 'auth' })
</script>
