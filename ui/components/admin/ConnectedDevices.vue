<template>
  <section class="bg-white rounded-xl shadow-sm border border-gray-200">
    <div class="px-6 py-4 border-b border-gray-200">
      <h2 class="text-lg font-semibold text-gray-900">Anslutna enheter</h2>
    </div>

    <div class="p-6 space-y-8">
      <!-- Rings -->
      <div v-if="ringGroups.length > 0">
        <h3 class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Domarbord</h3>
        <div class="space-y-2">
          <div
            v-for="group in ringGroups"
            :key="group.ring.id"
            class="flex items-center gap-4 px-4 py-3 rounded-lg bg-gray-50 border border-gray-200"
          >
            <div class="w-20 text-sm font-bold text-gray-700">Bord {{ group.ring.ring_number }}</div>
            <div class="flex items-center gap-2 text-sm">
              <span :class="group.panel ? 'text-green-600' : 'text-red-400'" class="text-lg leading-none">●</span>
              <span class="text-gray-600">Domarpanel</span>
            </div>
            <div class="flex items-center gap-2 text-sm">
              <span :class="group.display ? 'text-green-600' : 'text-red-400'" class="text-lg leading-none">●</span>
              <span class="text-gray-600">Skärm</span>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="text-sm text-gray-400">Inga domarbord i utställningen</div>

      <!-- Day Displays -->
      <div>
        <h3 class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Dagsskärmar</h3>
          <div v-if="dayDisplayDevices.length > 0" class="space-y-2">
          <div
            v-for="device in dayDisplayDevices"
            :key="device.device_id"
            class="flex items-center gap-4 px-4 py-3 rounded-lg bg-gray-50 border border-gray-200"
          >
            <span :class="isDeviceConnected(device.device_id) ? 'text-green-600' : 'text-gray-300'" class="text-lg leading-none">●</span>
            <input
              :value="device.name"
              @change="renameDevice(device.device_id, ($event.target as HTMLInputElement).value)"
              class="flex-1 text-sm font-medium text-gray-700 bg-transparent border-b border-transparent hover:border-gray-300 focus:border-blue-500 focus:outline-none px-1 py-0.5"
            />
            <span class="text-xs text-gray-400 shrink-0">/show/{{ showId }}/day/{{ device.day_id }}</span>
          </div>
        </div>
        <div v-else class="text-sm text-gray-400">Inga registrerade dagsdisplayer</div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { ConnectionInfo, DisplayDevice } from '~/types'
import type { Ring } from '~/types'
import { api } from '~/utils/api'
import { useWebSocket } from '~/composables/useWebSocket'

const props = defineProps<{
  showId: number
  dayId: number
}>()

const connections = ref<ConnectionInfo[]>([])
const displayDevices = ref<DisplayDevice[]>([])
const rings = ref<Ring[]>([])

const ringConnections = computed(() =>
  connections.value.filter((c) => c.ring_id !== null && rings.value.some((r) => r.id === c.ring_id))
)

interface RingGroup {
  ring: { id: number; ring_number: number }
  panel: boolean
  display: boolean
}

const ringGroups = computed<RingGroup[]>(() =>
  rings.value.map((ring) => ({
    ring,
    panel: ringConnections.value.some((c) => c.ring_id === ring.id && c.device_type === 'panel'),
    display: ringConnections.value.some((c) => c.ring_id === ring.id && c.device_type === 'ring_display'),
  }))
)

const dayDisplayDevices = computed(() =>
  displayDevices.value.filter((d) => d.day_id === props.dayId)
)

function isDeviceConnected(deviceId: string): boolean {
  return connections.value.some((c) => c.device_id === deviceId)
}

function handleConnected(payload: any) {
  const conn = payload?.connection as ConnectionInfo | undefined
  if (conn && !connections.value.some((c) => c.id === conn.id)) {
    connections.value.push(conn)
    if (conn.device_type === 'day_display' && conn.device_id &&
        conn.day_id === props.dayId &&
        !displayDevices.value.some((d) => d.device_id === conn.device_id)) {
      api.displayDevices.list(props.showId).then((devices) => {
        displayDevices.value = devices
      })
    }
  }
}

function handleDisconnected(payload: any) {
  const conn = payload?.connection as ConnectionInfo | undefined
  if (conn) {
    connections.value = connections.value.filter((c) => c.id !== conn.id)
  }
}

function handleDeviceRenamed(payload: any) {
  const idx = displayDevices.value.findIndex((d) => d.device_id === payload?.device_id)
  if (idx !== -1 && payload?.name) {
    displayDevices.value[idx] = { ...displayDevices.value[idx], name: payload.name }
  }
}

async function renameDevice(deviceId: string, name: string) {
  const trimmed = name.trim()
  if (!trimmed) return
  const device = displayDevices.value.find((d) => d.device_id === deviceId)
  if (device && device.name === trimmed) return
  try {
    await api.displayDevices.rename(deviceId, trimmed)
  } catch {
    // revert on failure — WS event from server will correct
  }
}

const { connect, disconnect, on } = useWebSocket()

onMounted(async () => {
  const [conns, devices, ringList] = await Promise.all([
    api.connections.list(),
    api.displayDevices.list(props.showId),
    api.rings.list(props.dayId),
  ])
  connections.value = conns
  displayDevices.value = devices
  rings.value = ringList

  connect('admin')
  on('CONNECTED', handleConnected)
  on('DISCONNECTED', handleDisconnected)
  on('DEVICE_RENAMED', handleDeviceRenamed)
})

onUnmounted(() => {
  disconnect()
})
</script>
