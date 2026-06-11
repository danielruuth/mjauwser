<template>
  <Teleport to="body">
    <div class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="$emit('close')">
      <div class="bg-white rounded-xl shadow-xl p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
        <h3 class="text-lg font-semibold mb-4">Importera katter</h3>

        <div class="space-y-3">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Fil (CSV eller JSON)</label>
            <input ref="fileInputRef" type="file" accept=".csv,.json" @change="onFileChange" class="w-full px-3 py-2 border rounded-lg text-sm" />
          </div>

          <div v-if="previewRows.length > 0" class="border rounded-lg overflow-x-auto">
            <div class="p-3 bg-gray-50 border-b text-sm text-gray-500">
              {{ preview.total_estimated }} rader upptäckta
            </div>
            <div v-if="autoMapping && Object.keys(autoMapping).length > 0" class="p-3 border-b text-xs text-gray-500 space-y-1">
              <div class="font-medium">Automatisk fältmappning:</div>
              <div v-for="(field, col) in autoMapping" :key="col" class="flex gap-2">
                <span class="font-mono">{{ col }}</span>
                <span class="text-gray-300">→</span>
                <span class="font-mono text-blue-600">{{ field || 'omappad' }}</span>
              </div>
            </div>
            <table class="w-full text-sm">
              <thead class="bg-gray-50 text-gray-600 text-left">
                <tr>
                  <th v-for="h in preview.headers" :key="h" class="px-3 py-2 font-medium">{{ h }}</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                <tr v-for="(row, i) in previewRows" :key="i" class="hover:bg-gray-50">
                  <td v-for="h in preview.headers" :key="h" class="px-3 py-2">{{ row[h] || '' }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="flex gap-3 justify-end pt-2">
            <Btn variant="outline" size="small" @click="$emit('close')">Avbryt</Btn>
            <Btn variant="primary" size="small" :disabled="!selectedFile" @click="submitImport">
              Importera{{ preview.total_estimated ? ' ' + preview.total_estimated + ' katter' : '' }}
            </Btn>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { api } from '~/utils/api'

const props = defineProps<{ showId: number }>()
const emit = defineEmits<{ close: [] }>()

const fileInputRef = ref<HTMLInputElement>()
const selectedFile = ref<File | null>(null)
const preview = ref<{ headers: string[]; total_estimated: number; rows: Record<string, string>[]; auto_mapping: Record<string, string>; db_fields: string[] }>({
  headers: [],
  total_estimated: 0,
  rows: [],
  auto_mapping: {},
  db_fields: [],
})
const autoMapping = computed(() => preview.value.auto_mapping)
const previewRows = computed(() => preview.value.rows.slice(0, 20))

async function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  selectedFile.value = file

  try {
    preview.value = await api.import.preview(file)
  } catch (err: any) {
    alert('Förhandsvisning misslyckades: ' + (err.message || ''))
  }
}

async function submitImport() {
  if (!selectedFile.value) return
  const mapping = Object.keys(autoMapping.value).length > 0 ? autoMapping.value : {}
  try {
    const result = await api.import.upload(selectedFile.value, mapping, props.showId)
    let msg = `Importerade ${result.imported} katter`
    if (result.errors.length > 0) {
      msg += `\nFel: ${result.errors.slice(0, 5).map((e) => `Rad ${e.row}: ${e.error}`).join('\n')}`
      if (result.errors.length > 5) msg += `\n...and ${result.errors.length - 5} more`
    }
    alert(msg)
    emit('close')
  } catch (e: any) {
    alert('Import misslyckades: ' + (e.message || 'Okänt fel'))
  }
}
</script>
