<template>
  <div>
    <div class="mb-6 flex gap-4 items-center">
      
      <Btn variant="primary" @click="showAddJudge = true">+ Lägg till domare</Btn>
    </div>

    <section class="bg-white rounded-xl shadow-sm border border-gray-200">
      <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <h2 class="text-lg font-semibold text-gray-900">Domare ({{ judgesStore.judges.length }})</h2>
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
            <tr v-for="judge in judgesStore.judges" :key="judge.id" class="hover:bg-gray-50">
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
                <Btn size="small" @click="deleteJudge(judge.id)">Radera</Btn>
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
          <h3 class="text-lg font-semibold mb-4">Lägg till Domare</h3>
          <form @submit.prevent="submitJudge" class="space-y-3">
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
              <Btn type="submit" variant="primary" size="small">Lägg till</Btn>
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
import { useJudgesStore } from '~/stores/judges'
import { useWebSocket } from '~/composables/useWebSocket'
import { useConfirm } from '~/composables/useConfirm'
import type { Category, Judge } from '~/types'
import { api } from '~/utils/api'

const confirm = useConfirm()

const judgesStore = useJudgesStore()
const ws = useWebSocket()

const categories = ref<Category[]>([])
const showAddJudge = ref(false)
const editingJudge = ref<Judge | null>(null)
const judgeForm = reactive({ name: '', flag: '', photo: '', bio: '', category_ids: [] as number[] })

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
  judgeForm.category_ids = judge.categories.map((c) => c.id)
  editingJudge.value = judge
}

async function submitJudge() {
  await judgesStore.create({ ...judgeForm } as any)
  showAddJudge.value = false
  resetJudgeForm()
}

async function submitJudgeEdit() {
  if (!editingJudge.value) return
  await judgesStore.update(editingJudge.value.id, { ...judgeForm } as any)
  editingJudge.value = null
  resetJudgeForm()
}

async function deleteJudge(id: number) {
  const ok = await confirm.ask('Radera denna domare?')
  if (!ok) return
  await judgesStore.remove(id)
}

onMounted(async () => {
  categories.value = await api.categories.list()
  await judgesStore.fetchAll()
  ws.connect('admin')
  ws.on('JUDGE_CREATED', (p: any) => judgesStore.applyEvent(p))
  ws.on('JUDGE_UPDATED', (p: any) => judgesStore.applyEvent(p))
  ws.on('JUDGE_DELETED', (p: any) => judgesStore.applyDelete(p))
  ws.onState((state: any) => {
    judgesStore.judges = state.judges
  })
})

onUnmounted(() => {
  ws.disconnect()
})
</script>
