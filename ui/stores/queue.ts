import { defineStore } from 'pinia'
import type { QueueItem } from '~/types'

export const useQueueStore = defineStore('queue', () => {
  const queue = ref<QueueItem[]>([])

  function applyAdd(payload: { queue_item: QueueItem }) {
    const exists = queue.value.find((q) => q.id === payload.queue_item.id)
    if (!exists) queue.value.push(payload.queue_item)
  }

  function applyRemove(payload: { queue_id: number }) {
    queue.value = queue.value.filter((q) => q.id !== payload.queue_id)
  }

  return { queue, applyAdd, applyRemove }
})
