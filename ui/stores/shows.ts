import { defineStore } from 'pinia'
import type { Show, ShowDay, Ring } from '~/types'
import { api } from '~/utils/api'

export const useShowsStore = defineStore('shows', () => {
  const shows = ref<Show[]>([])

  async function fetchAll() {
    shows.value = await api.shows.list()
  }

  async function fetchShow(id: number) {
    const show = await api.shows.get(id)
    const idx = shows.value.findIndex((s) => s.id === id)
    if (idx !== -1) shows.value[idx] = show
    else shows.value.push(show)
    return show
  }

  async function create(data: { name: string; start_date?: string; end_date?: string }) {
    const show = await api.shows.create(data)
    shows.value.push(show)
    return show
  }

  async function update(id: number, data: Partial<Show>) {
    const show = await api.shows.update(id, data)
    const idx = shows.value.findIndex((s) => s.id === id)
    if (idx !== -1) shows.value[idx] = show
    return show
  }

  async function remove(id: number) {
    await api.shows.delete(id)
    shows.value = shows.value.filter((s) => s.id !== id)
  }

  async function addDay(showId: number, data: { name: string; sort_order: number }) {
    const day = await api.showDays.create(showId, data)
    const show = shows.value.find((s) => s.id === showId)
    if (show) {
      if (!show.days) show.days = []
      show.days.push(day)
    }
    return day
  }

  async function updateDay(dayId: number, data: Partial<ShowDay>) {
    const day = await api.showDays.update(dayId, data)
    for (const show of shows.value) {
      const idx = show.days?.findIndex((d) => d.id === dayId)
      if (idx !== undefined && idx !== -1 && show.days) {
        show.days[idx] = day
        break
      }
    }
    return day
  }

  async function removeDay(dayId: number) {
    await api.showDays.delete(dayId)
    for (const show of shows.value) {
      show.days = show.days?.filter((d) => d.id !== dayId) || []
    }
  }

  return { shows, fetchAll, fetchShow, create, update, remove, addDay, updateDay, removeDay }
})
