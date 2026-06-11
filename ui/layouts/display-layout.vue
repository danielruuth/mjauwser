<script setup lang="ts">
import GradientMeshBackground from '~/components/GradientMeshBackground.vue';

</script>

<template>
  <div class="min-h-screen overflow-hidden">
    <gradient-mesh-background />
    <main class="h-screen">
      <slot />
    </main>
  </div>
</template>
