<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
    <ManualRingAssigner :show-id="showId" :show-day-id="dayId" />
  </div>
</template>

<script setup lang="ts">
import ManualRingAssigner from '~/components/admin/ManualRingAssigner.vue'

const route = useRoute()
const showId = computed(() => Number(route.params.id))
const dayId = computed(() => Number(route.params.dayId))
</script>
