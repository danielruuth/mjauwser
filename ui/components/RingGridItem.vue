<template>
  <div v-if="ringData"
    :key="ringData.ring.id"
    class="relative bg-white rounded-lg  px-4 py-3 pb-2 flex flex-col min-h-0 h-full overflow-hidden"
  >
    <div
      v-if="ringData.ring.status === 'paused'"
      class="absolute inset-0 bg-white/90 rounded-lg flex items-center justify-center z-10"
    >
      <div class="text-5xl font-bold text-gray-900 mx-4 text-center">{{ ringData.ring.pause_message || 'PAUS' }}</div>
    </div>

    <div class="w-full h-16 flex flex-col justify-between">
      <div v-if="ringData.ring.judge" class="flex items-center gap-2 text-lg text-black font-bold">
        <span>{{ ringData.ring.ring_number }}. {{ ringData.ring.judge.name }}</span>
        <Flag v-if="ringData.ring.judge.flag" :code="ringData.ring.judge.flag" size="small" />
      </div>
    </div>

    <div v-if="localCurrent" class="flex-1 flex flex-col items-center justify-center space-y-1 my-2">
      <div ref="ml6Ref" :class="['ml6', catalogFontSize]" class="leading-none font-bold text-gray-900 tracking-tight">
        <span class="text-wrapper">
          <span class="letters">{{ localCurrent.catalog_nr }}</span>
        </span>
      </div>
      <div class="text-gray-500 text-center" :class="detailFontSize">
        {{ localCurrent.breed }} · {{ localCurrent.class }}
      </div>
    </div>
    <div v-else class="flex-1 flex items-center justify-center text-3xl text-gray-300 font-light my-2">
      Väntar...
    </div>

    <div class="w-full border-t border-gray-100 pt-2 mt-auto h-8 flex items-center">
      <div class="flex justify-start gap-2" v-if="ringData.upcoming.length > 0">
        <span class="font-bold text-gray-400">Kommande:</span>
        <span v-for="item in ringData.upcoming" :key="item.id" class="font-bold text-gray-700" :class="upcomingNrFontSize">
          #{{ item.catalog_nr }}
        </span>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import type { Ring, RingQueueItem, } from '~/types'
const props = defineProps<{
  ringData: {
    ring: Ring
    current?: { catalog_nr: string; name: string; breed: string; class: string }
    upcoming: { id?: number | string; catalog_nr: string; name: string }[]
  },
    ringCount: number
}>()

const { $anime } = useNuxtApp()
const ml6Ref = ref<HTMLElement | null>(null)
const localCurrent = ref<typeof props.ringData.current>(null)

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
    translateY: [offset, 0],
    opacity: [0, 1],
    duration: 750,
    delay: (_el: HTMLElement, i: number) => 50 * i,
  })
}

localCurrent.value = props.ringData.current ? { ...props.ringData.current } : null

watch(() => props.ringData.current?.catalog_nr, async (newVal, oldVal) => {
  if (!newVal) {
    localCurrent.value = null
    return
  }
  if (oldVal && oldVal !== newVal) {
    await animateExit()
  }
  localCurrent.value = props.ringData.current ? { ...props.ringData.current } : null
  if (oldVal !== newVal) {
    await animateEnter()
  }
})

onMounted(() => {
  if (localCurrent.value) {
    animateEnter()
  }
})

const upcomingNrFontSize = computed(() => {
  if (props.ringCount >= 5) return 'text-base'
  if (props.ringCount >= 3) return 'text-lg'
  if (props.ringCount >= 2) return 'text-xl'
  return 'text-3xl'
})

const upcomingNameFontSize = computed(() => {
  if (props.ringCount >= 5) return 'text-xs'
  if (props.ringCount >= 3) return 'text-sm'
  if (props.ringCount >= 2) return 'text-base'
  return 'text-lg'
})

const detailFontSize = computed(() => {
  if (props.ringCount >= 5) return 'text-sm'
  if (props.ringCount >= 3) return 'text-base'
  if (props.ringCount >= 2) return 'text-xl'
  return 'text-2xl'
})

const catalogFontSize = computed(() => {
  if (props.ringCount >= 5) return 'text-9xl'
  if (props.ringCount >= 3) return 'text-7xl'
  if (props.ringCount >= 2) return 'text-5xl'
  return 'text-[12rem]'
})

const nameFontSize = computed(() => {
  if (props.ringCount >= 5) return 'text-lg'
  if (props.ringCount >= 3) return 'text-xl'
  if (props.ringCount >= 2) return 'text-3xl'
  return 'text-4xl'
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
</style>