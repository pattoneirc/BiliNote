import request from '@/utils/request'

export interface MonitorSource {
  id: number
  platform: string
  source_type: string
  source_id: string | null
  source_name: string | null
  enabled: number
  process_mode: string
  cron_expression: string
  model_name: string | null
  provider_id: string | null
  note_style: string | null
  note_format: string | null
  last_check_at: string | null
  last_video_id: string | null
  created_at: string | null
}

export interface CreateMonitorSource {
  platform: string
  source_type?: string
  source_id?: string
  source_name?: string
  enabled?: number
  process_mode?: string
  cron_expression?: string
  model_name?: string
  provider_id?: string
  note_style?: string
  note_format?: string
}

export interface UpdateMonitorSource {
  source_name?: string
  enabled?: number
  process_mode?: string
  cron_expression?: string
  model_name?: string
  provider_id?: string
  note_style?: string
  note_format?: string
  source_id?: string
}

export interface FavoriteVideo {
  id: number
  video_id: string
  platform: string
  title: string
  url: string
  cover_url: string | null
  author: string | null
  duration: number | null
  favorited_at: string | null
  processed: number
  task_id: string | null
}

export interface DailyDigest {
  id: number
  digest_date: string
  title: string
  markdown_content?: string
  video_count: number
  platform: string | null
  file_path: string | null
  created_at: string | null
}

export interface SchedulerStatus {
  running: boolean
  jobs: Array<{
    id: string
    name: string
    next_run_time: string | null
  }>
}

export const getMonitorSources = () =>
  request.get<MonitorSource[]>('/monitor_sources')

export const getMonitorSource = (id: number) =>
  request.get<MonitorSource>(`/monitor_source/${id}`)

export const createMonitorSource = (data: CreateMonitorSource) =>
  request.post('/monitor_source', data)

export const updateMonitorSource = (id: number, data: UpdateMonitorSource) =>
  request.put(`/monitor_source/${id}`, data)

export const deleteMonitorSource = (id: number) =>
  request.delete(`/monitor_source/${id}`)

export const manualCheck = (sourceId?: number) =>
  request.post('/monitor/check', { source_id: sourceId || null })

export const processUnprocessed = (data: {
  process_mode?: string
  model_name?: string
  provider_id?: string
  style?: string
  note_format?: string[]
}) => request.post('/monitor/process', data)

export const generateDigest = (data?: {
  target_date?: string
  model_name?: string
  provider_id?: string
}) => request.post('/monitor/digest', data || {})

export const getDigests = (limit = 30) =>
  request.get<DailyDigest[]>('/digests', { params: { limit } })

export const getDigest = (id: number) =>
  request.get<DailyDigest>(`/digest/${id}`)

export const getFavoriteVideos = (params?: {
  platform?: string
  processed?: number
  limit?: number
}) => request.get<FavoriteVideo[]>('/favorite_videos', { params })

export const startScheduler = () =>
  request.post('/monitor/scheduler/start')

export const stopScheduler = () =>
  request.post('/monitor/scheduler/stop')

export const getSchedulerStatus = () =>
  request.get<SchedulerStatus>('/monitor/scheduler/status')

export const updateSchedulerCron = (cron_expression: string) =>
  request.put('/monitor/scheduler/cron', null, { params: { cron_expression } })

export interface NotifyChannel {
  id: number
  channel_type: string
  name: string | null
  webhook_url: string
  secret: string | null
  enabled: number
  notify_on_digest: number
  notify_on_new_favorite: number
  notify_on_error: number
  template: string | null
  created_at: string | null
}

export interface CreateNotifyChannel {
  channel_type: string
  name?: string
  webhook_url: string
  secret?: string
  enabled?: number
  notify_on_digest?: number
  notify_on_new_favorite?: number
  notify_on_error?: number
  template?: string
}

export const getNotifyChannels = () =>
  request.get<NotifyChannel[]>('/notify_channels')

export const createNotifyChannel = (data: CreateNotifyChannel) =>
  request.post('/notify_channel', data)

export const updateNotifyChannel = (id: number, data: Partial<CreateNotifyChannel>) =>
  request.put(`/notify_channel/${id}`, data)

export const deleteNotifyChannel = (id: number) =>
  request.delete(`/notify_channel/${id}`)

export const testNotifyChannel = (id: number) =>
  request.post(`/notify_channel/${id}/test`)
