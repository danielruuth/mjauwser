<template>
  <div v-if="!allComplete" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
    <!-- Days -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-4 flex items-start gap-3">
      <Check v-if="hasDays" class="w-5 h-5 text-green-500 mt-0.5 shrink-0" />
      <div v-else class="w-5 h-5 rounded-full border-2 border-gray-300 mt-0.5 shrink-0" />
      <div class="min-w-0">
        <p class="text-sm font-semibold text-gray-900">Utställningsdagar</p>
        <p v-if="hasDays" class="text-xs text-gray-500">{{ dayCount }} dag(ar)</p>
        <Btn v-else variant="primary" size="small" @click="$emit('add-day')">Lägg till dag</Btn>
      </div>
    </div>

    <!-- Cats -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-4 flex items-start gap-3">
      <Check v-if="hasCats" class="w-5 h-5 text-green-500 mt-0.5 shrink-0" />
      <div v-else class="w-5 h-5 rounded-full border-2 border-gray-300 mt-0.5 shrink-0" />
      <div class="min-w-0">
        <p class="text-sm font-semibold text-gray-900">Katter</p>
        <p v-if="hasCats" class="text-xs text-gray-500">{{ catCount }} katter</p>
        <Btn v-else variant="primary" size="small" @click="$emit('import-cats')">Registrera katter</Btn>
      </div>
    </div>

    <!-- Judges -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-4 flex items-start gap-3">
      <Check v-if="hasJudges" class="w-5 h-5 text-green-500 mt-0.5 shrink-0" />
      <div v-else class="w-5 h-5 rounded-full border-2 border-gray-300 mt-0.5 shrink-0" />
      <div class="min-w-0">
        <p class="text-sm font-semibold text-gray-900">Domare</p>
        <p v-if="hasJudges" class="text-xs text-gray-500">{{ judgeCount }} domare</p>
        <Btn v-else variant="primary" size="small" :href="'/admin/shows/' + showId + '/judges'">Lägg till domare</Btn>
      </div>
    </div>

    <!-- Rings -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-4 flex items-start gap-3">
      <Check v-if="hasRings" class="w-5 h-5 text-green-500 mt-0.5 shrink-0" />
      <div v-else class="w-5 h-5 rounded-full border-2 border-gray-300 mt-0.5 shrink-0" />
      <div class="min-w-0">
        <p class="text-sm font-semibold text-gray-900">Domarbord</p>
        <p v-if="hasRings" class="text-xs text-gray-500">{{ ringCount }} bord</p>
        <template v-else-if="hasDays">
          <Btn variant="primary" size="small" :href="`/admin/shows/${showId}/days/${firstDayId}`">Lägg till första bordet</Btn>
        </template>
        <p v-else class="text-xs text-gray-400">Lägg till dagar först</p>
      </div>
    </div>

    <!-- Cat assignment -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-4 flex items-start gap-3">
      <Check v-if="assignmentDone" class="w-5 h-5 text-green-500 mt-0.5 shrink-0" />
      <ArrowRight v-else-if="assignmentStarted" class="w-5 h-5 text-amber-500 mt-0.5 shrink-0" />
      <div v-else class="w-5 h-5 rounded-full border-2 border-gray-300 mt-0.5 shrink-0" />
      <div class="min-w-0">
        <p class="text-sm font-semibold text-gray-900">Kattilldelning</p>
        <p v-if="assignmentDone" class="text-xs text-gray-500">Alla katter tilldelade</p>
        <p v-else-if="assignmentStarted" class="text-xs text-amber-600">{{ assignmentAssignedCount }}/{{ assignmentTotalCount }} katter tilldelade</p>
        <template v-else-if="hasCats">
          <Btn variant="primary" size="small" :href="`/admin/shows/${showId}/days/${firstDayId}`">Påbörja tilldelning</Btn>
        </template>
        <p v-else class="text-xs text-gray-400">Registrera katter först</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Check, ArrowRight } from '@lucide/vue'
import { api } from '~/utils/api'
import { useShowsStore } from '~/stores/shows'
import { useCatsStore } from '~/stores/cats'

const props = defineProps<{
  showId: number
  refreshTick?: number
}>()

defineEmits<{
  'add-day': []
  'import-cats': []
}>()

const showsStore = useShowsStore()
const catsStore = useCatsStore()

const showCatCount = ref(0)
const showJudgeCount = ref(0)
const assignmentTotal = ref(0)
const assignmentAssigned = ref(0)

const show = computed(() => showsStore.shows.find((s) => s.id === props.showId))

const days = computed(() => show.value?.days || [])

const hasDays = computed(() => days.value.length > 0)
const dayCount = computed(() => days.value.length)

const hasCats = computed(() => showCatCount.value > 0)
const catCount = computed(() => showCatCount.value)

const hasJudges = computed(() => showJudgeCount.value > 0)
const judgeCount = computed(() => showJudgeCount.value)

const rings = computed(() => days.value.flatMap((d) => d.rings || []))
const hasRings = computed(() => rings.value.length > 0)
const ringCount = computed(() => rings.value.length)

const assignmentDone = computed(() => assignmentTotal.value > 0 && assignmentAssigned.value === assignmentTotal.value)
const assignmentStarted = computed(() => assignmentAssigned.value > 0 && assignmentAssigned.value < assignmentTotal.value)
const assignmentTotalCount = computed(() => assignmentTotal.value)
const assignmentAssignedCount = computed(() => assignmentAssigned.value)

const sortedDays = computed(() => [...days.value].sort((a, b) => a.sort_order - b.sort_order))
const firstDayId = computed(() => sortedDays.value[0]?.id ?? 0)

const allComplete = computed(() => hasDays.value && hasCats.value && hasJudges.value && hasRings.value && assignmentDone.value)

async function fetchShowCats() {
  try {
    const cats = await api.shows.cats(props.showId)
    showCatCount.value = cats.length
  } catch {
    showCatCount.value = 0
  }
}

async function fetchShowJudges() {
  try {
    const judges = await api.showJudges.list(props.showId)
    showJudgeCount.value = judges.length
  } catch {
    showJudgeCount.value = 0
  }
}

async function fetchAssignmentProgress() {
  try {
    const progress = await api.shows.catAssignmentProgress(props.showId)
    assignmentTotal.value = progress.total_cats
    assignmentAssigned.value = progress.assigned_cats
  } catch {
    assignmentTotal.value = 0
    assignmentAssigned.value = 0
  }
}

watch(() => catsStore.cats.length, () => {
  fetchShowCats()
})

watch(() => showsStore.shows, () => {
  fetchAssignmentProgress()
  fetchShowJudges()
}, { deep: true })

watch(() => props.refreshTick, () => {
  fetchAssignmentProgress()
})

function onVisibilityChange() {
  if (document.visibilityState === 'visible') {
    fetchAssignmentProgress()
  }
}

onMounted(() => {
  fetchShowCats()
  fetchShowJudges()
  fetchAssignmentProgress()
  document.addEventListener('visibilitychange', onVisibilityChange)
})

onUnmounted(() => {
  document.removeEventListener('visibilitychange', onVisibilityChange)
})
</script>
