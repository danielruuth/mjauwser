import type { WsEvent } from '~/types'
import { api } from '~/utils/api'

export interface WsMetadata {
  deviceType?: string
  deviceId?: string
  ringNumber?: number
  showId?: number
  dayId?: number
}

export function useWebSocket() {
  const config = useRuntimeConfig()
  const wsBase = config.public.wsBase

  let ws: WebSocket | null = null
  let reconnectTimeout: ReturnType<typeof setTimeout> | null = null
  let reconnectAttempts = 0
  const MAX_RECONNECT_DELAY = 30000

  const listeners = new Map<string, Set<(payload: any) => void>>()

  function handleMessage(event: MessageEvent) {
    try {
      const data: WsEvent = JSON.parse(event.data)
      const eventListeners = listeners.get(data.event)
      if (eventListeners) {
        eventListeners.forEach((cb) => cb(data.payload))
      }
      const allListeners = listeners.get('*')
      if (allListeners) {
        allListeners.forEach((cb) => cb(data))
      }
    } catch {
      // ignore parse errors
    }
  }

  async function reconcile() {
    try {
      const state = await api.state.get()
      const stateListeners = listeners.get('__state__')
      if (stateListeners) {
        stateListeners.forEach((cb) => cb(state))
      }
    } catch {
      // reconciliation failed, will retry on next reconnect
    }
  }

  function connect(role: 'admin' | 'display' | 'judge', ringId?: number, metadata?: WsMetadata) {
    disconnect()
    let url = `${wsBase}/ws-app?role=${role}`
    if (role === 'admin' && import.meta.client) {
      const token = localStorage.getItem('auth_token')
      if (token) {
        url += `&token=${encodeURIComponent(token)}`
      }
    }
    if (role === 'judge' && ringId !== undefined) {
      url += `&ring_id=${ringId}`
    }
    if (role === 'display' && ringId !== undefined) {
      url += `&ring_id=${ringId}`
    }
    if (metadata?.deviceType) {
      url += `&device_type=${metadata.deviceType}`
    }
    if (metadata?.deviceId) {
      url += `&device_id=${metadata.deviceId}`
    }
    if (metadata?.ringNumber !== undefined) {
      url += `&ring_number=${metadata.ringNumber}`
    }
    if (metadata?.showId !== undefined) {
      url += `&show_id=${metadata.showId}`
    }
    if (metadata?.dayId !== undefined) {
      url += `&day_id=${metadata.dayId}`
    }

    try {
      ws = new WebSocket(url)
    } catch {
      scheduleReconnect(role, ringId, metadata)
      return
    }

    ws.onopen = () => {
      reconnectAttempts = 0
      reconcile()
    }

    ws.onmessage = handleMessage

    ws.onclose = () => {
      ws = null
      scheduleReconnect(role, ringId, metadata)
    }

    ws.onerror = () => {
      ws?.close()
    }
  }

  function disconnect() {
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout)
      reconnectTimeout = null
    }
    reconnectAttempts = 0
    if (ws) {
      ws.onclose = null
      ws.close()
      ws = null
    }
  }

  function scheduleReconnect(role: 'admin' | 'display' | 'judge', ringId?: number, metadata?: WsMetadata) {
    if (reconnectTimeout) return
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), MAX_RECONNECT_DELAY)
    reconnectAttempts++
    reconnectTimeout = setTimeout(() => {
      reconnectTimeout = null
      connect(role, ringId, metadata)
    }, delay)
  }

  function on(event: string, callback: (payload: any) => void) {
    if (!listeners.has(event)) {
      listeners.set(event, new Set())
    }
    listeners.get(event)!.add(callback)
    return () => {
      listeners.get(event)?.delete(callback)
    }
  }

  function onState(callback: (state: any) => void) {
    return on('__state__', callback)
  }

  return { connect, disconnect, on, onState }
}
