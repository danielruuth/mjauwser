import { defineStore } from 'pinia'
import type { RingQueueItem } from '~/types'
import { api } from '~/utils/api'

export const useRingQueueStore = defineStore('ringQueue', () => {
  const queue = ref<RingQueueItem[]>([])

  async function fetchByRing(ringId: number) {
    queue.value = await api.rings.listQueue(ringId)
  }

  async function add(ringId: number, catId: number, sequenceOrder: number) {
    const item = await api.rings.addToQueue(ringId, catId, sequenceOrder)
    const exists = queue.value.find((q) => q.id === item.id)
    if (!exists) queue.value.push(item)
    return item
  }

  async function remove(queueId: number) {
    await api.rings.removeFromQueue(queueId)
    queue.value = queue.value.filter((q) => q.id !== queueId)
  }

  function applyAdd(payload: { queue_item: RingQueueItem }) {
    const exists = queue.value.find((q) => q.id === payload.queue_item.id)
    if (!exists) queue.value.push(payload.queue_item)
  }

  function applyRemove(payload: { queue_id: number }) {
    queue.value = queue.value.filter((q) => q.id !== payload.queue_id)
  }

  return { queue, fetchByRing, add, remove, applyAdd, applyRemove }
})
