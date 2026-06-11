import { defineStore } from 'pinia'
import type { Cat } from '~/types'
import { api } from '~/utils/api'

export const useCatsStore = defineStore('cats', () => {
  const cats = ref<Cat[]>([])

  async function fetchAll() {
    cats.value = await api.cats.list()
  }

  async function create(data: Partial<Cat>) {
    const cat = await api.cats.create(data)
    const idx = cats.value.findIndex((c) => c.id === cat.id)
    if (idx !== -1) cats.value[idx] = cat
    else cats.value.push(cat)
    return cat
  }

  async function update(id: number, data: Partial<Cat>) {
    const cat = await api.cats.update(id, data)
    const idx = cats.value.findIndex((c) => c.id === id)
    if (idx !== -1) cats.value[idx] = cat
    return cat
  }

  async function updateStatus(id: number, status: string) {
    const cat = await api.cats.updateStatus(id, status)
    const idx = cats.value.findIndex((c) => c.id === id)
    if (idx !== -1) cats.value[idx] = cat
    return cat
  }

  async function remove(id: number) {
    await api.cats.delete(id)
    cats.value = cats.value.filter((c) => c.id !== id)
  }

  function applyEvent(payload: { cat: Cat }) {
    const idx = cats.value.findIndex((c) => c.id === payload.cat.id)
    if (idx !== -1) {
      cats.value[idx] = payload.cat
    } else {
      cats.value.push(payload.cat)
    }
  }

  function applyDelete(payload: { cat_id: number }) {
    cats.value = cats.value.filter((c) => c.id !== payload.cat_id)
  }

  return { cats, fetchAll, create, update, updateStatus, remove, applyEvent, applyDelete }
})
