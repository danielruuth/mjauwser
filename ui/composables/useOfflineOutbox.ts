import type { OfflineMutation } from '~/types'
import { useOnline } from '@vueuse/core'

const DB_NAME = 'catshow-offline'
const STORE_NAME = 'mutations'
const dbPromise: Promise<IDBDatabase> = new Promise((resolve, reject) => {
  const request = indexedDB.open(DB_NAME, 1)
  request.onupgradeneeded = () => {
    request.result.createObjectStore(STORE_NAME, { keyPath: 'id' })
  }
  request.onsuccess = () => resolve(request.result)
  request.onerror = () => reject(request.error)
})

async function getMutations(): Promise<OfflineMutation[]> {
  const db = await dbPromise
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly')
    const store = tx.objectStore(STORE_NAME)
    const request = store.getAll()
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
}

export function useOfflineOutbox() {
  const isOnline = useOnline()

  async function enqueue(method: string, url: string, body?: unknown) {
    const mutation: OfflineMutation = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      method,
      url,
      body,
      timestamp: Date.now(),
    }
    const db = await dbPromise
    return new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite')
      tx.objectStore(STORE_NAME).add(mutation)
      tx.oncomplete = () => resolve()
      tx.onerror = () => reject(tx.error)
    })
  }

  async function flush() {
    const mutations = await getMutations()
    if (mutations.length === 0) return

    const config = useRuntimeConfig()
    const base = config.public.apiBase as string

    for (const mutation of mutations) {
      try {
        const res = await fetch(`${base}${mutation.url}`, {
          method: mutation.method,
          headers: { 'Content-Type': 'application/json' },
          body: mutation.body ? JSON.stringify(mutation.body) : undefined,
        })
        if (res.ok) {
          const db = await dbPromise
          const tx = db.transaction(STORE_NAME, 'readwrite')
          tx.objectStore(STORE_NAME).delete(mutation.id)
        }
      } catch {
        // stop flushing on first error; will retry next online cycle
        break
      }
    }
  }

  watch(isOnline, (online) => {
    if (online) {
      flush()
    }
  })

  return { enqueue, flush }
}
