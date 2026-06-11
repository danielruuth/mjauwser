<template>
  <div>
    <div class="mb-6 flex gap-4 items-center">
      <Btn :href="`/admin/shows/${showId}`" variant="outline" size="small">← Utställningen</Btn>
      <Btn variant="primary" @click="showAddJudge = true">+ Lägg till domare</Btn>
    </div>

    <section class="bg-white rounded-xl shadow-sm border border-gray-200">
      <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <h2 class="text-lg font-semibold text-gray-900">Domare ({{ showJudges.length }})</h2>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-gray-600">
            <tr>
              <th class="text-left px-3 py-3 font-medium">Foto</th>
              <th class="text-left px-3 py-3 font-medium">Namn</th>
              <th class="text-left px-3 py-3 font-medium">Land</th>
              <th class="text-left px-3 py-3 font-medium">Licensierade Kategorier</th>
              <th class="text-right px-3 py-3 font-medium">&nbsp;</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="judge in showJudges" :key="judge.id" class="hover:bg-gray-50">
              <td class="px-3 py-3">
                <img v-if="judge.photo" :src="judge.photo" class="w-10 h-10 rounded-full object-cover" alt="" />
                <div v-else class="w-10 h-10 rounded-full bg-gray-200" />
              </td>
              <td class="px-3 py-3 font-medium">{{ judge.name }}</td>
              <td class="px-3 py-3 text-gray-600">
                <Flag v-if="judge.flag" :code="judge.flag" size="mini" />
                <span v-if="!judge.flag">-</span>
              </td>
              <td class="px-3 py-3">
                <div class="flex gap-1 flex-wrap">
                  <span v-for="cat in judge.categories" :key="cat.id" class="text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-700">{{ cat.name }}</span>
                  <span v-if="judge.categories.length === 0" class="text-xs text-gray-400">inga</span>
                </div>
              </td>
              <td class="px-3 py-3 text-right space-x-2 whitespace-nowrap">
                <Btn :href="`/judge/${judge.id}`" size="small">Domarbord</Btn>
                <Btn size="small" @click="openJudgeEdit(judge)">Redigera</Btn>
                <Btn size="small" @click="unassignJudge(judge.id)">Ta bort</Btn>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Add Judge Modal -->
    <Teleport to="body">
      <div v-if="showAddJudge" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="showAddJudge = false">
        <div class="bg-white rounded-xl shadow-xl p-6 w-full max-w-lg">
          <div class="flex gap-2 mb-4">
            <Btn :class="addMode === 'existing' ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-600'" size="small" @click="addMode = 'existing'">Välj befintlig</Btn>
            <Btn :class="addMode === 'new' ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-600'" size="small" @click="addMode = 'new'">Skapa ny</Btn>
          </div>

          <form v-if="addMode === 'existing'" @submit.prevent="submitAssignJudge" class="space-y-3">
            <fieldset v-if="availableJudges.length > 0" class="space-y-1 max-h-60 overflow-y-auto border rounded-lg p-2">
              <label v-for="j in availableJudges" :key="j.id" class="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-50 cursor-pointer text-sm">
                <input type="checkbox" :value="j.id" v-model="selectedJudgeIds" class="rounded" />
                {{ j.name }}
                <Flag v-if="j.flag" :code="j.flag" size="mini" />
              </label>
            </fieldset>
            <p v-else class="text-sm text-gray-400">Alla domare är redan tillagda i utställningen</p>
            <div class="flex gap-3 justify-end pt-2">
              <Btn variant="outline" size="small" @click="showAddJudge = false">Avbryt</Btn>
              <Btn type="submit" variant="primary" size="small" :disabled="selectedJudgeIds.length === 0">Lägg till</Btn>
            </div>
          </form>

          <form v-else @submit.prevent="submitCreateJudge" class="space-y-3">
            <input v-model="judgeForm.name" type="text" placeholder="Namn" class="w-full px-3 py-2 border rounded-lg text-sm" required />
            <div class="flex gap-2 items-center">
              <input v-model="judgeForm.flag" type="text" placeholder="Landskod (t.ex. SE)" maxlength="2" class="flex-1 px-3 py-2 border rounded-lg text-sm uppercase" />
              <Flag v-if="judgeForm.flag" :code="judgeForm.flag" size="small" />
            </div>
            <input v-model="judgeForm.photo" type="text" placeholder="Länk till foto (valfritt)" class="w-full px-3 py-2 border rounded-lg text-sm" />
            <textarea v-model="judgeForm.bio" placeholder="Kort biografi (valfritt)" class="w-full px-3 py-2 border rounded-lg text-sm" rows="3"></textarea>
            <fieldset>
              <legend class="text-sm font-medium text-gray-700 mb-1">Licensierade Kategorier</legend>
              <div class="grid grid-cols-2 gap-2">
                <label v-for="cat in categories" :key="cat.id" class="flex items-center gap-2 text-sm">
                  <input type="checkbox" :value="cat.id" v-model="judgeForm.category_ids" class="rounded" />
                  {{ cat.name }}
                </label>
              </div>
            </fieldset>
            <div class="flex gap-3 justify-end pt-2">
              <Btn variant="outline" size="small" @click="showAddJudge = false">Avbryt</Btn>
              <Btn type="submit" variant="primary" size="small">Skapa & lägg till</Btn>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Edit Judge Modal -->
    <Teleport to="body">
      <div v-if="editingJudge" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="editingJudge = null">
        <div class="bg-white rounded-xl shadow-xl p-6 w-full max-w-lg">
          <h3 class="text-lg font-semibold mb-4">Redigera Domare</h3>
          <form @submit.prevent="submitJudgeEdit" class="space-y-3">
            <input v-model="judgeForm.name" type="text" placeholder="Namn" class="w-full px-3 py-2 border rounded-lg text-sm" required />
            <div class="flex gap-2 items-center">
              <input v-model="judgeForm.flag" type="text" placeholder="Landskod (t.ex. SE)" maxlength="2" class="flex-1 px-3 py-2 border rounded-lg text-sm uppercase" />
              <Flag v-if="judgeForm.flag" :code="judgeForm.flag" size="small" />
            </div>
            <input v-model="judgeForm.photo" type="text" placeholder="Länk till foto (valfritt)" class="w-full px-3 py-2 border rounded-lg text-sm" />
            <textarea v-model="judgeForm.bio" placeholder="Kort biografi (valfritt)" class="w-full px-3 py-2 border rounded-lg text-sm" rows="3"></textarea>
            <fieldset>
              <legend class="text-sm font-medium text-gray-700 mb-1">Licensierade Kategorier</legend>
              <div class="grid grid-cols-2 gap-2">
                <label v-for="cat in categories" :key="cat.id" class="flex items-center gap-2 text-sm">
                  <input type="checkbox" :value="cat.id" v-model="judgeForm.category_ids" class="rounded" />
                  {{ cat.name }}
                </label>
              </div>
            </fieldset>
            <div class="flex gap-3 justify-end pt-2">
              <Btn variant="outline" size="small" @click="editingJudge = null">Avbryt</Btn>
              <Btn type="submit" variant="primary" size="small">Spara</Btn>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <ConfirmDialog :visible="confirm.visible" :title="confirm.title" :message="confirm.message" @confirm="confirm.onConfirm" @cancel="confirm.onCancel" />
  </div>
</template>

<script setup lang="ts">
import { useConfirm } from '~/composables/useConfirm'
import { useWebSocket } from '~/composables/useWebSocket'
import type { Category, Judge } from '~/types'
import { api } from '~/utils/api'

const confirm = useConfirm()
const ws = useWebSocket()

const route = useRoute()
const showId = computed(() => Number(route.params.id))

const showJudges = ref<Judge[]>([])
const allJudges = ref<Judge[]>([])
const categories = ref<Category[]>([])

const showAddJudge = ref(false)
const addMode = ref<'existing' | 'new'>('existing')
const selectedJudgeIds = ref<number[]>([])
const editingJudge = ref<Judge | null>(null)
const judgeForm = reactive({ name: '', flag: '', photo: '', bio: '', category_ids: [] as number[] })

const availableJudges = computed(() =>
  allJudges.value.filter((j) => !showJudges.value.some((sj) => sj.id === j.id))
)

function resetJudgeForm() {
  judgeForm.name = ''
  judgeForm.flag = ''
  judgeForm.photo = ''
  judgeForm.bio = ''
  judgeForm.category_ids = []
}

function openJudgeEdit(judge: Judge) {
  judgeForm.name = judge.name
  judgeForm.flag = judge.flag || ''
  judgeForm.photo = judge.photo || ''
  judgeForm.bio = judge.bio || ''
  judgeForm.category_ids = judge.categories.map((c: Category) => c.id)
  editingJudge.value = judge
}

async function submitAssignJudge() {
  if (selectedJudgeIds.value.length === 0) return
  await api.showJudges.add(showId.value, { judge_ids: selectedJudgeIds.value })
  showAddJudge.value = false
  selectedJudgeIds.value = []
  await fetchJudges()
  await fetchAllJudges()
}

async function submitCreateJudge() {
  await api.showJudges.add(showId.value, { ...judgeForm })
  showAddJudge.value = false
  resetJudgeForm()
  await fetchJudges()
  await fetchAllJudges()
}

async function submitJudgeEdit() {
  if (!editingJudge.value) return
  await api.judges.update(editingJudge.value.id, { ...judgeForm } as any)
  editingJudge.value = null
  resetJudgeForm()
  await fetchJudges()
}

async function unassignJudge(judgeId: number) {
  const ok = await confirm.ask('Ta bort denna domare från utställningen? (Domaren tas inte bort från databasen)')
  if (!ok) return
  await api.showJudges.unassign(showId.value, judgeId)
  await fetchJudges()
  await fetchAllJudges()
}

async function fetchJudges() {
  showJudges.value = await api.showJudges.list(showId.value)
}

async function fetchAllJudges() {
  allJudges.value = await api.judges.list()
}

onMounted(async () => {
  categories.value = await api.categories.list()
  await Promise.all([fetchJudges(), fetchAllJudges()])

  ws.connect('admin')
  ws.on('SHOW_JUDGE_ASSIGNED', (p: any) => {
    if (p.show_id === showId.value) fetchJudges()
  })
  ws.on('SHOW_JUDGE_UNASSIGNED', (p: any) => {
    if (p.show_id === showId.value) fetchJudges()
  })
  ws.on('JUDGE_CREATED', () => fetchJudges())
  ws.on('JUDGE_UPDATED', () => fetchJudges())
  ws.on('JUDGE_DELETED', () => fetchJudges())
  ws.onState(() => fetchJudges())
})

onUnmounted(() => {
  ws.disconnect()
})
</script>
