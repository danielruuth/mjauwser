import type { Cat, Judge, Show, ShowDay, Ring, RingQueueItem, Breed, Category, JudgeRing, ShowImportResponse, ConnectionInfo, DisplayDevice, CatAssignmentProgress, Owner } from '~/types'

function getAuthHeaders(): Record<string, string> {
  if (!import.meta.client) return {}
  const token = localStorage.getItem('auth_token')
  return token ? { 'Authorization': `Bearer ${token}` } : {}
}

async function request<T>(method: string, url: string, body?: unknown): Promise<T> {
  let res: Response
  try {
    res = await fetch(url, {
      method,
      headers: {
        ...(body ? { 'Content-Type': 'application/json' } : {}),
        ...getAuthHeaders(),
      },
      body: body ? JSON.stringify(body) : undefined,
    })
  } catch (e) {
    throw new Error(`Nätverksfel: kunde inte nå ${method} ${url}. Kontrollera att API-servern är igång.`)
  }
  if (res.status === 401 && import.meta.client) {
    localStorage.removeItem('auth_token')
    window.location.href = '/login'
    throw new Error('Sessionen har löpt ut')
  }
  if (!res.ok) {
    const err = await res.text().catch(() => '')
    throw new Error(err || `HTTP ${res.status} ${res.statusText}`)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export const api = {
  cats: {
    list: () => request<Cat[]>('GET', '/api/cats'),
    get: (id: number) => request<Cat>('GET', `/api/cats/${id}`),
    create: (data: Partial<Cat>) => request<Cat>('POST', '/api/cats', data),
    update: (id: number, data: Partial<Cat>) => request<Cat>('PUT', `/api/cats/${id}`, data),
    updateStatus: (id: number, status: string) => request<Cat>('PATCH', `/api/cats/${id}/status?status=${status}`),
    delete: (id: number) => request<void>('DELETE', `/api/cats/${id}`),
    listDays: (catId: number) => request<import('~/types').CatShowDay[]>('GET', `/api/cats/${catId}/days`),
    updateDay: (catId: number, dayId: number, catalogNr: number) =>
      request<import('~/types').CatShowDay>('PUT', `/api/cats/${catId}/days/${dayId}`, { catalog_nr: catalogNr }),
    deleteDay: (catId: number, dayId: number) => request<void>('DELETE', `/api/cats/${catId}/days/${dayId}`),
    updateDayStatus: (catId: number, dayId: number, status: string) =>
      request<import('~/types').CatShowDay>('PATCH', `/api/cats/${catId}/days/${dayId}/status`, { status }),
  },
  judges: {
    list: () => request<Judge[]>('GET', '/api/judges'),
    get: (id: number) => request<Judge>('GET', `/api/judges/${id}`),
    create: (data: Partial<Judge>) => request<Judge>('POST', '/api/judges', data),
    update: (id: number, data: Partial<Judge>) => request<Judge>('PUT', `/api/judges/${id}`, data),
    delete: (id: number) => request<void>('DELETE', `/api/judges/${id}`),
    rings: (id: number) => request<JudgeRing[]>('GET', `/api/judges/${id}/rings`),
  },
  shows: {
    list: () => request<Show[]>('GET', '/api/shows'),
    get: (id: number) => request<Show>('GET', `/api/shows/${id}`),
    create: (data: { name: string; start_date?: string; end_date?: string }) =>
      request<Show>('POST', '/api/shows', data),
    update: (id: number, data: Partial<Show>) => request<Show>('PUT', `/api/shows/${id}`, data),
    delete: (id: number) => request<void>('DELETE', `/api/shows/${id}`),
    cats: (showId: number, dayId?: number) => {
      let url = `/api/shows/${showId}/cats`
      if (dayId) url += `?day_id=${dayId}`
      return request<Cat[]>('GET', url)
    },
    exportShow: async (id: number) => {
      const res = await fetch(`/api/shows/${id}/export`)
      if (!res.ok) throw new Error(await res.text() || `HTTP ${res.status}`)
      return res.blob()
    },
    importShow: (data: unknown) => request<ShowImportResponse>('POST', '/api/shows/import', data),
    catAssignmentProgress: (showId: number) => request<CatAssignmentProgress>('GET', `/api/shows/${showId}/cat-assignment-progress`),
  },
  showJudges: {
    list: (showId: number) => request<Judge[]>('GET', `/api/shows/${showId}/judges`),
    add: (showId: number, data: { judge_id?: number; judge_ids?: number[]; name?: string; flag?: string; photo?: string; bio?: string; category_ids?: number[] }) =>
      request<Judge>('POST', `/api/shows/${showId}/judges`, data),
    unassign: (showId: number, judgeId: number) => request<void>('DELETE', `/api/shows/${showId}/judges/${judgeId}`),
  },
  showDays: {
    list: (showId: number) => request<ShowDay[]>('GET', `/api/shows/${showId}/days`),
    get: (dayId: number) => request<ShowDay>('GET', `/api/days/${dayId}`),
    create: (showId: number, data: { name: string; sort_order: number }) =>
      request<ShowDay>('POST', `/api/shows/${showId}/days`, data),
    update: (dayId: number, data: Partial<ShowDay>) => request<ShowDay>('PUT', `/api/days/${dayId}`, data),
    delete: (dayId: number) => request<void>('DELETE', `/api/days/${dayId}`),
  },
  rings: {
    list: (dayId: number) => request<Ring[]>('GET', `/api/days/${dayId}/rings`),
    get: (id: number) => request<Ring>('GET', `/api/rings/${id}`),
    create: (dayId: number, data: { ring_number: number; judge_id?: number; category_ids?: number[] }) =>
      request<Ring>('POST', `/api/days/${dayId}/rings`, data),
    update: (id: number, data: Partial<Ring>) => request<Ring>('PUT', `/api/rings/${id}`, data),
    delete: (id: number) => request<void>('DELETE', `/api/rings/${id}`),
    assignJudge: (id: number, judgeId: number | null) =>
      request<Ring>('POST', `/api/rings/${id}/assign-judge`, { judge_id: judgeId }),
    updateCategories: (id: number, categoryIds: number[]) =>
      request<Ring>('PUT', `/api/rings/${id}/categories`, { category_ids: categoryIds }),
    nextCat: (id: number) => request<Ring>('POST', `/api/rings/${id}/next-cat`),
    previousCat: (id: number) => request<Ring>('POST', `/api/rings/${id}/previous-cat`),
    pause: (id: number, message?: string) => request<Ring>('POST', `/api/rings/${id}/pause`, message !== undefined ? { pause_message: message } : undefined),
    resume: (id: number) => request<Ring>('POST', `/api/rings/${id}/resume`),
    listQueue: (ringId: number) => request<RingQueueItem[]>('GET', `/api/rings/${ringId}/queue`),
    addToQueue: (ringId: number, catId: number, sequenceOrder: number) =>
      request<RingQueueItem>('POST', `/api/rings/${ringId}/queue`, { cat_id: catId, sequence_order: sequenceOrder }),
    removeFromQueue: (queueId: number) => request<void>('DELETE', `/api/queue/${queueId}`),
    queue: {
      get: (ringId: number) => api.rings.listQueue(ringId),
      add: async (ringId: number, catIds: number[]) => {
        const results: RingQueueItem[] = []
        // Get current queue length to determine starting sequence_order
        const current = await api.rings.listQueue(ringId)
        let order = current.length > 0 ? Math.max(...current.map((q) => q.sequence_order)) + 1 : 1
        for (const catId of catIds) {
          const item = await api.rings.addToQueue(ringId, catId, order)
          results.push(item)
          order++
        }
        return results
      },
      remove: (queueId: number) => api.rings.removeFromQueue(queueId),
    },
  },
  import: {
    upload: async (file: File, mapping: Record<string, string>, showId?: number) => {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('mapping', JSON.stringify(mapping))
      let url = '/api/cats/import'
      if (showId) url += `?show_id=${showId}`
      const res = await fetch(url, { method: 'POST', body: fd, headers: getAuthHeaders() })
      if (!res.ok) throw new Error(await res.text() || `HTTP ${res.status}`)
      return res.json() as Promise<{ imported: number; errors: { row: number; error: string }[]; total: number }>
    },
    preview: async (file: File) => {
      const fd = new FormData()
      fd.append('file', file)
      const res = await fetch('/api/cats/import/preview', { method: 'POST', body: fd, headers: getAuthHeaders() })
      if (!res.ok) throw new Error(await res.text() || `HTTP ${res.status}`)
      return res.json() as Promise<{
        headers: string[]
        total_estimated: number
        rows: Record<string, string>[]
        auto_mapping: Record<string, string>
        db_fields: string[]
      }>
    },
  },
  breeds: {
    list: () => request<Breed[]>('GET', '/api/breeds'),
    create: (data: Partial<Breed>) => request<Breed>('POST', '/api/breeds', data),
    update: (id: number, data: Partial<Breed>) => request<Breed>('PUT', `/api/breeds/${id}`, data),
    remove: (id: number) => request<void>('DELETE', `/api/breeds/${id}`),
  },
  categories: {
    list: () => request<Category[]>('GET', '/api/categories'),
    create: (data: Partial<Category>) => request<Category>('POST', '/api/categories', data),
    update: (id: number, data: Partial<Category>) => request<Category>('PUT', `/api/categories/${id}`, data),
    remove: (id: number) => request<void>('DELETE', `/api/categories/${id}`),
  },
  state: {
    get: () => request<{ judges: Judge[]; cats: Cat[]; shows: Show[]; breeds: Breed[]; categories: Category[] }>('GET', '/api/state'),
  },
  connections: {
    list: () => request<ConnectionInfo[]>('GET', '/api/connections'),
  },
  displayDevices: {
    list: (showId: number) => request<DisplayDevice[]>('GET', `/api/shows/${showId}/display-devices`),
    rename: (deviceId: string, name: string) => request<DisplayDevice>('PUT', `/api/display-devices/${deviceId}`, { name }),
  },
  owners: {
    list: (q?: string) => request<Owner[]>('GET', `/api/owners${q ? `?q=${encodeURIComponent(q)}` : ''}`),
    create: (data: { name: string; phone?: string; email?: string }) => request<Owner>('POST', '/api/owners', data),
    update: (id: number, data: Partial<Owner>) => request<Owner>('PUT', `/api/owners/${id}`, data),
    delete: (id: number) => request<void>('DELETE', `/api/owners/${id}`),
  },
}
