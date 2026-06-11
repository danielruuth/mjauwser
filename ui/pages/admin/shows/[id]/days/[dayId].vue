<template>
  <div>
    <div class="mb-6 flex gap-4 items-center justify-between">
      <div class="flex gap-4">
        <Btn :href="`/admin/shows/${showId}`" variant="outline" size="small">← Utställningen</Btn>
        <Btn variant="primary" @click="showAddRing = true">+ Lägg till domarbord</Btn>
    </div>
    <div>
        <Btn :href="`/admin/shows/${showId}/day/${dayId}/checkin`" variant="secondary" size="small">Checka in</Btn>
        <Btn :href="`/show/${showId}/day/${dayId}`" variant="outline" size="small">
          <Monitor class="w-4 h-4" />
          Skärm
        </Btn>
      </div>
    </div>

    <section class="mb-8">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">Domarbord på {{ day?.name }}</h2>
      <div v-if="rings.length === 0" class="text-sm text-gray-400 bg-white rounded-xl shadow-sm border border-gray-200 p-6 text-center">
        Inga domarbord än.
      </div>
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <RingCard
          v-for="ring in rings"
          :key="ring.id"
          :ring="ring"
          :cats="dayCats"
          @assign-judge="assignJudge"
          @next-cat="ringNextCat"
          @pause="ringPause"
          @resume="ringResume"
          @delete-ring="deleteRing"
        />
      </div>
    </section>

    <!-- Ring Assigner -->
    <section class="bg-white rounded-xl shadow-sm border border-gray-200 mb-8">
      <div class="px-6 py-4 border-b border-gray-200 flex gap-2 justify-between items-center">
        <h2 class="text-lg font-semibold text-gray-900">Domarfördelare</h2><NuxtLink :to="`/admin/shows/${showId}/days/manual/${dayId}`" class="text-gray-400 hover:text-gray-600">
            <SquareArrowOutUpRight class="inline-block w-4 h-4 text-gray-400" />
          </NuxtLink>
      </div>
      <div class="p-4">
        <p v-if="loadingCats" class="text-sm text-gray-500">Laddar katter...</p>
        <RingAssigner v-else :show-day-id="dayId" :show-id="showId" :rings="rings" @assigned="refreshRings" />
      </div>
    </section>

    <!-- Add Ring Modal -->
    <Teleport to="body">
      <div v-if="showAddRing" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="showAddRing = false">
        <div class="bg-white rounded-xl shadow-xl p-6 w-full max-w-lg">
          <h3 class="text-lg font-semibold mb-4">Lägg till domarbord</h3>
          <form @submit.prevent="submitAddRing" class="space-y-3">
            <p class="text-xs text-gray-500">Bord #{{ nextRingNumber }}</p>
            <select v-model.number="ringForm.judge_id" class="w-full px-3 py-2 border rounded-lg text-sm">
              <option :value="undefined">Ingen domare</option>
              <option v-for="j in judges" :key="j.id" :value="j.id">{{ j.name }} {{ j.flag ? '(' + j.flag + ')' : '' }}</option>
            </select>
            <fieldset v-if="judgeCategories.length > 0">
              <legend class="text-sm font-medium text-gray-700 mb-1">
                Kategorier {{ ringForm.judge_id ? ' (Från domarens licenser)' : '' }}
              </legend>
              <div class="grid grid-cols-2 gap-2">
                <label v-for="cat in judgeCategories" :key="cat.id" class="flex items-center gap-2 text-sm">
                  <input type="checkbox" :value="cat.id" v-model="ringForm.category_ids" class="rounded" />
                  {{ cat.name }}
                </label>
              </div>
            </fieldset>
            <div class="flex gap-3 justify-end pt-2">
              <Btn variant="outline" size="small" @click="showAddRing = false">Avbryt</Btn>
              <Btn type="submit" variant="primary" size="small">Lägg till</Btn>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Pause Modal -->
    <Teleport to="body">
      <div v-if="showPauseModal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="showPauseModal = false">
        <div class="bg-white rounded-xl shadow-xl p-6 w-full max-w-lg">
          <h3 class="text-lg font-semibold mb-4">Pausa domarbord #{{ pausedRingNumber }}</h3>
          <p class="text-sm text-gray-600 mb-4">Vill du ange ett pausmeddelande?</p>
          <input v-model="pauseMessage" placeholder="Meddelande (valfritt)" class="w-full px-3 py-2 border rounded-lg text-sm mb-4" />
          <div class="flex gap-3 justify-end">
            <Btn variant="outline" size="small" @click="confirmPause(false)">Nej</Btn>
            <Btn variant="primary" size="small" @click="confirmPause(true)">Spara</Btn>
          </div>
        </div>
      </div>
    </Teleport>

    <div class="mt-8">
      <ShowCatsTable :show-id="showId" :day-id="dayId" :refresh-tick="catRefreshTick" />
    </div>

    <div class="mt-8">
      <ConnectedDevices :show-id="showId" :day-id="dayId" />
    </div>

    <ConfirmDialog :visible="confirm.visible" :title="confirm.title" :message="confirm.message" @confirm="confirm.onConfirm" @cancel="confirm.onCancel" />
  </div>
</template>

<script setup lang="ts">
import { useJudgesStore } from '~/stores/judges'
import { useCatsStore } from '~/stores/cats'
import { useShowsStore } from '~/stores/shows'
import { useConfirm } from '~/composables/useConfirm'
import RingCard from '~/components/admin/RingCard.vue'
import ShowCatsTable from '~/components/admin/ShowCatsTable.vue'
import RingAssigner from '~/components/admin/RingAssigner.vue'
import ConnectedDevices from '~/components/admin/ConnectedDevices.vue'
import { useWebSocket } from '~/composables/useWebSocket'
import { api } from '~/utils/api'
import type { Ring, Category } from '~/types'
import { SquareArrowOutUpRight, Monitor } from '@lucide/vue'

const confirm = useConfirm()

const route = useRoute()
const showId = computed(() => Number(route.params.id))
const dayId = computed(() => Number(route.params.dayId))

const judgesStore = useJudgesStore()
const catsStore = useCatsStore()
const showsStore = useShowsStore()

const judges = computed(() => judgesStore.judges)
const categories = ref<Category[]>([])
const rings = ref<Ring[]>([])
const dayCats = ref<{ id: number; name: string; catalog_nr: number }[]>([])
const loadingCats = ref(true)
const { connect, disconnect, on, onState } = useWebSocket()

const day = computed(() => {
  const s = showsStore.shows.find((s) => s.id === showId.value)
  return s?.days?.find((d) => d.id === dayId.value)
})

const showAddRing = ref(false)
const ringForm = reactive({ ring_number: 0, judge_id: undefined as number | undefined, category_ids: [] as number[] })
const catRefreshTick = ref(0)

const showPauseModal = ref(false)
const pauseRingId = ref<number | null>(null)
const pauseMessage = ref('')
const pausedRingNumber = computed(() => {
  const r = rings.value.find((r2) => r2.id === pauseRingId.value)
  return r?.ring_number ?? ''
})

const nextRingNumber = computed(() => {
  if (rings.value.length === 0) return 1
  return Math.max(...rings.value.map((r) => r.ring_number)) + 1
})

const selectedJudge = computed(() => {
  if (ringForm.judge_id === undefined) return null
  return judgesStore.judges.find((j) => j.id === ringForm.judge_id) || null
})

const judgeCategories = computed(() => {
  if (selectedJudge.value) return selectedJudge.value.categories
  return categories.value
})

watch(() => ringForm.judge_id, () => {
  if (selectedJudge.value) {
    ringForm.category_ids = selectedJudge.value.categories.map((c) => c.id)
  } else {
    ringForm.category_ids = []
  }
})

async function loadRings() {
  rings.value = await api.rings.list(dayId.value)
}

async function loadDayCats() {
  loadingCats.value = true
  const results = await api.cats.list()
  const dayCatsList: { id: number; name: string; catalog_nr: number }[] = []
  for (const cat of results) {
    const catDetail = await api.cats.get(cat.id)
    if (catDetail.days) {
      const dayEntry = catDetail.days.find((d: any) => d.show_day_id === dayId.value)
      if (dayEntry) {
        dayCatsList.push({ id: cat.id, name: cat.name, catalog_nr: dayEntry.catalog_nr })
      }
    }
  }
  dayCats.value = dayCatsList
  loadingCats.value = false
}

async function submitAddRing() {
  await api.rings.create(dayId.value, {
    ring_number: nextRingNumber.value,
    judge_id: ringForm.judge_id || undefined,
    category_ids: ringForm.category_ids,
  })
  showAddRing.value = false
  ringForm.judge_id = undefined
  ringForm.category_ids = []
  await loadRings()
}

async function assignJudge(ring: Ring) {
  const judges = judgesStore.judges
  const msg = judges.map((j) => `${j.id}: ${j.name}`).join('\n')
  const input = prompt(`Ange domar-ID att tilldela till Bord ${ring.ring_number}:\n${msg}`)
  if (input) {
    await api.rings.assignJudge(ring.id, Number(input))
    await loadRings()
  }
}

async function ringNextCat(id: number) {
  try {
    await api.rings.nextCat(id)
    await loadRings()
  } catch (e: any) {
    alert(e.message || 'Inga fler katter')
  }
}

async function ringPause(id: number) {
  pauseRingId.value = id
  pauseMessage.value = ''
  showPauseModal.value = true
}

async function confirmPause(withMessage: boolean) {
  if (pauseRingId.value === null) return
  const msg = withMessage ? pauseMessage.value || undefined : undefined
  await api.rings.pause(pauseRingId.value, msg)
  showPauseModal.value = false
  pauseRingId.value = null
  await loadRings()
}

async function ringResume(id: number) {
  await api.rings.resume(id)
  await loadRings()
}

async function deleteRing(id: number) {
  const ok = await confirm.ask('Radera detta bord och dess kö?')
  if (!ok) return
  await api.rings.delete(id)
  await loadRings()
}

function refreshRings() {
  loadRings()
}

onMounted(async () => {
  categories.value = await api.categories.list()
  await Promise.all([judgesStore.fetchAll(), loadRings(), loadDayCats()])

  connect('admin')

  on('RING_PROGRESSED', (payload: any) => {
    const ringId = payload?.ring?.id
    if (ringId) {
      const idx = rings.value.findIndex((r) => r.id === ringId)
      if (idx !== -1) {
        const copy = [...rings.value]
        copy[idx] = { ...copy[idx], ...payload.ring }
        rings.value = copy
      }
    }
  })

  on('RING_STATUS_CHANGED', (payload: any) => {
    const ringId = payload?.ring?.id
    if (ringId) {
      const idx = rings.value.findIndex((r) => r.id === ringId)
      if (idx !== -1) {
        const copy = [...rings.value]
        copy[idx] = { ...copy[idx], ...payload.ring }
        rings.value = copy
      }
    }
  })

  on('DAY_CAT_STATUS_CHANGED', () => {
    catRefreshTick.value++
  })

  onState((state: any) => {
    const show = state.shows?.find((s: any) => s.id === showId.value)
    const day = show?.days?.find((d: any) => d.id === dayId.value)
    if (day?.rings) {
      rings.value = day.rings
    }
  })
})

onUnmounted(() => {
  disconnect()
})
</script>
