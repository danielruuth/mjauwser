<template>
  <div v-if="ring" class="min-h-screen flex flex-col items-center justify-between p-8">
    <!-- Ring header -->
    <div class="space-y-8 w-full h-16 ">
       <div class="w-full flex gap-12">
        <div>
          <img src="/assets/forshaga_logo.png" alt="Mjauwser" width="238" height="208" class="h-16 w-auto" />
        </div>
        <div>
          <div class="text-gray-500 text-2xl font-medium tracking-widest uppercase">
            Bord {{ ring.ring_number }}
          </div>
          <div v-if="ring.judge" class="flex items-center justify-start gap-3 text-3xl text-gray-700">
            <span>{{ ring.judge.name }}</span> <Flag v-if="ring.judge.flag" :code="ring.judge.flag" size="small" />
          </div>
        </div>
      </div>
    </div>
    <!-- Ring display -->
     
    <div>
      <!-- Paused overlay -->
      <div v-if="ring.status === 'paused'" class="text-8xl text-gray-300 font-light py-24">
        {{ ring.pause_message || 'PAUS' }}
      </div>
      <!-- Current cat -->
      <div v-else-if="displayCat" class="space-y-6">
        <div ref="ml6Ref" class="ml6 text-[24rem] leading-none font-bold text-gray-900 tracking-tight">
          <span class="text-wrapper">
            <span class="letters">{{ displayCat.catalog_nr }}</span>
          </span>
        </div>
        <div class="flex items-center justify-center gap-4 text-2xl text-gray-500">
          <span>{{ displayCat.breed }}</span>
          <span class="text-gray-300">·</span>
          <span>{{ displayCat.class }}</span>
        </div>
      </div>
      <div v-else class="text-6xl text-gray-300 font-light py-24">
        Väntar...
      </div>
    </div>
    <!-- Next cats -->
    <div class="h-20 w-full border-t border-gray-200 pt-4">
      <div class="text-lg text-gray-400 mb-1">Nästa</div>
      <TransitionGroup name="upcoming" tag="div" class="flex gap-6 relative">
        <span v-for="(item, i) in upcoming" :key="item.id" class="upcoming-item text-3xl font-bold text-gray-800">#{{ item.catalog_nr }}</span>
      </TransitionGroup>
    </div>
  </div>
  <div v-else class="text-4xl text-gray-300 font-light">Laddar bord...</div>
</template>

<script setup lang="ts">
import type { Ring, RingQueueItem } from '~/types'
import { api } from '~/utils/api'
import { useRingQueueStore } from '~/stores/ringQueue'

definePageMeta({ layout: 'display-layout' })

interface CatInfo {
  catalog_nr: string
  name: string
  breed: string
  class: string
}

const route = useRoute()
const ringId = computed(() => Number(route.params.id))

const store = useRingQueueStore()
const ring = ref<Ring | null>(null)
const ringQueue = ref<RingQueueItem[]>([])

const displayCat = ref<CatInfo | null>(null)
const ml6Ref = ref<HTMLElement | null>(null)

const currentCat = computed(() => {
  const current = ringQueue.value.find((q) => q.status === 'ongoing')
  if (!current) return null
  return {
    catalog_nr: current.catalog_nr || current.cat?.id || '',
    name: current.cat?.name || '',
    breed: current.cat?.breed_ems || '',
    class: current.cat?.show_class || '',
  }
})

const upcoming = computed(() => {
  return ringQueue.value.filter((q) => q.status === 'pending').slice(0, 3).map((q) => ({
    id: q.id,
    catalog_nr: q.catalog_nr || q.cat?.id || '',
    name: q.cat?.name || '',
  }))
})

const { $anime } = useNuxtApp()

function getLetterOffset(el: HTMLElement): number {
  const fontSize = parseFloat(getComputedStyle(el).fontSize)
  return Math.round(fontSize * 1.1)
}

async function animateExit(): Promise<void> {
  const wrapper = ml6Ref.value?.querySelector('.letters') as HTMLElement
  const letters = wrapper?.querySelectorAll('.letter')
  if (!letters?.length) return
  const offset = getLetterOffset(letters[0])
  await $anime({
    targets: letters,
    translateY: [0, -offset],
    opacity: [1, 0],
    duration: 400,
    delay: (_el: HTMLElement, i: number) => 30 * i,
    easing: 'easeInExpo',
  }).finished
}

async function animateEnter(): Promise<void> {
  await nextTick()
  const wrapper = ml6Ref.value?.querySelector('.letters') as HTMLElement
  if (!wrapper) return
  wrapper.innerHTML = wrapper.textContent!.replace(/\S/g, "<span class='letter'>$&</span>")
  const letters = wrapper.querySelectorAll('.letter')
  if (!letters.length) return
  const offset = getLetterOffset(letters[0])
  $anime({
    targets: letters,
    rotate: [45, 0],
    translateY: [offset, 0],
    opacity: [0, 1],
    duration: 750,
    delay: (_el: HTMLElement, i: number) => 50 * i,
  })
}

watch(currentCat, async (newCat, oldCat) => {
  if (oldCat && newCat && oldCat.catalog_nr !== newCat.catalog_nr) {
    await animateExit()
  }
  displayCat.value = newCat ? { ...newCat } : null
  if (newCat) {
    await animateEnter()
  }
}, { immediate: true })

async function load() {
  ring.value = await api.rings.get(ringId.value)
  ringQueue.value = await api.rings.queue.get(ringId.value)
}

const { connect, disconnect, onState, on } = useWebSocket()

onMounted(() => {
  connect('display', ringId.value, { deviceType: 'ring_display' })

  const unsubState = onState((state: any) => {
    ring.value = state?.rings?.[ringId.value] || ring.value
  })

  const unsubProgress = on('RING_PROGRESSED', (payload: any) => {
    if (payload?.ring?.id === ringId.value) {
      ring.value = payload.ring
      load()
    }
  })

  const unsubStatus = on('RING_STATUS_CHANGED', (payload: any) => {
    if (payload?.ring?.id === ringId.value) {
      ring.value = payload.ring
      load()
    }
  })

  onUnmounted(() => {
    disconnect()
    unsubState()
    unsubProgress()
    unsubStatus()
  })

  load()
})
</script>

<style scoped>
.ml6 {
  position: relative;
  font-weight: 900;
}
.ml6 :deep(.text-wrapper) {
  position: relative;
  display: inline-block;
  padding-top: 0.2em;
  padding-right: 0.05em;
  padding-bottom: 0.1em;
  overflow: hidden;
}
.ml6 :deep(.letter) {
  display: inline-block;
  line-height: 1em;
}

.upcoming-move {
  transition: transform 0.4s ease;
}

.upcoming-enter-active {
  transition: all 0.35s ease-out;
}

.upcoming-leave-active {
  transition: all 0.35s ease-in;
  position: absolute;
}

.upcoming-enter-from {
  opacity: 0;
  transform: translateX(40px);
}

.upcoming-leave-to {
  opacity: 0;
  transform: translateX(-40px);
}
</style>
