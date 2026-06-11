export interface Category {
  id: number
  name: string
  description: string | null
}

export interface Breed {
  id: number
  breed_code: string
  name: string
  category_id: number | null
  category: Category | null
}

export interface Owner {
  id: number
  name: string
  phone: string | null
  email: string | null
}

export interface Cat {
  id: number
  name: string
  breed_ems: string
  breed_name: string
  gender: string
  show_class: string
  birth_date: string | null
  registration_nr: string | null
  owner: Owner | null
  status: 'present' | 'absent' | 'judged'
  days?: CatShowDay[]
}

export interface CatShowDay {
  cat_id: number
  show_day_id: number
  catalog_nr: number
  day_name: string
  status: 'unchecked' | 'present' | 'absent' | 'judged'
}

export interface Judge {
  id: number
  name: string
  photo: string | null
  bio: string | null
  flag: string | null
  categories: Category[]
}

export interface Show {
  id: number
  name: string
  start_date: string | null
  end_date: string | null
  status: 'draft' | 'active' | 'completed'
  days: ShowDay[]
}

export interface ShowDay {
  id: number
  show_id: number
  name: string
  sort_order: number
  rings?: Ring[]
}

export interface Ring {
  id: number
  show_day_id: number
  ring_number: number
  judge: Judge | null
  status: 'active' | 'paused' | 'finished'
  current_catalog_nr: number | null
  current_class: string | null
  pause_message?: string | null
  categories: Category[]
}

export interface RingQueueItem {
  id: number
  ring_id: number
  cat_id: number
  sequence_order: number
  status: 'pending' | 'ongoing' | 'completed' | 'skipped'
  catalog_nr?: number
  cat?: {
    id: number
    name: string
    breed_ems: string
    breed_name: string
    gender: string
    show_class: string
    status: string
  }
}

export interface QueueItem {
  id: number
  ring_id: number
  cat_id: number
  sequence_order: number
  status: 'pending' | 'ongoing' | 'completed' | 'skipped'
}

export interface WsEvent {
  event: string
  payload: Record<string, unknown>
}

export interface OfflineMutation {
  id: string
  method: string
  url: string
  body?: unknown
  timestamp: number
}

export interface ShowImportResponse {
  show_id: number
  categories_found: number
  breeds_found: number
  judges_created: number
  cats_created: number
  queue_entries: number
}

export interface ConnectionInfo {
  id: string
  role: 'admin' | 'judge' | 'display'
  device_type: 'panel' | 'ring_display' | 'day_display' | null
  device_id: string | null
  device_name: string | null
  ring_id: number | null
  ring_number: number | null
  show_id: number | null
  day_id: number | null
  connected_at: number
}

export interface DisplayDevice {
  id: number
  device_id: string
  name: string
  device_type: string
  show_id: number | null
  day_id: number | null
  last_connected_at: string | null
  created_at: string | null
}

export interface CatAssignmentProgress {
  total_cats: number
  assigned_cats: number
}

export interface JudgeRing {
  id: number
  ring_number: number
  day_id: number
  day_name: string
  show_id: number | null
  status: string
  current_catalog_nr: number | null
}
