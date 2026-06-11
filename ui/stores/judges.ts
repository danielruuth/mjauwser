import { defineStore } from 'pinia'
import type { Judge } from '~/types'
import { api } from '~/utils/api'

export const useJudgesStore = defineStore('judges', () => {
  const judges = ref<Judge[]>([])

  async function fetchAll() {
    judges.value = await api.judges.list()
  }

  async function create(data: Partial<Judge>) {
    const judge = await api.judges.create(data)
    const idx = judges.value.findIndex((j) => j.id === judge.id)
    if (idx !== -1) judges.value[idx] = judge
    else judges.value.push(judge)
    return judge
  }

  async function update(id: number, data: Partial<Judge>) {
    const judge = await api.judges.update(id, data)
    const idx = judges.value.findIndex((j) => j.id === id)
    if (idx !== -1) judges.value[idx] = judge
    return judge
  }

  async function remove(id: number) {
    await api.judges.delete(id)
    judges.value = judges.value.filter((j) => j.id !== id)
  }

  function applyEvent(payload: { judge: Judge }) {
    const idx = judges.value.findIndex((j) => j.id === payload.judge.id)
    if (idx !== -1) {
      judges.value[idx] = payload.judge
    } else {
      judges.value.push(payload.judge)
    }
  }

  function applyDelete(payload: { judge_id: number }) {
    judges.value = judges.value.filter((j) => j.id !== payload.judge_id)
  }

  return { judges, fetchAll, create, update, remove, applyEvent, applyDelete }
})
