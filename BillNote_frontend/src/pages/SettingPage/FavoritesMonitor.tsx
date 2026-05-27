import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Heart,
  Plus,
  RefreshCw,
  Trash2,
  Play,
  Loader2,
  Clock,
  CheckCircle2,
  XCircle,
  FileText,
} from 'lucide-react'
import toast from 'react-hot-toast'
import {
  MonitorSource,
  CreateMonitorSource,
  SchedulerStatus,
  getMonitorSources,
  createMonitorSource,
  updateMonitorSource,
  deleteMonitorSource,
  manualCheck,
  getSchedulerStatus,
  startScheduler,
  stopScheduler,
} from '@/services/monitor'

const PLATFORMS = [
  { value: 'bilibili', label: '哔哩哔哩' },
  { value: 'douyin', label: '抖音' },
  { value: 'kuaishou', label: '快手' },
  { value: 'youtube', label: 'YouTube' },
]

const PROCESS_MODES = [
  { value: 'summary', label: '轻量摘要' },
  { value: 'full', label: '完整笔记' },
]

const DEFAULT_CRON_OPTIONS = [
  { value: '0 22 * * *', label: '每天 22:00' },
  { value: '0 20 * * *', label: '每天 20:00' },
  { value: '0 18 * * *', label: '每天 18:00' },
  { value: '0 */6 * * *', label: '每 6 小时' },
  { value: '0 */12 * * *', label: '每 12 小时' },
]

export default function FavoritesMonitor() {
  const [sources, setSources] = useState<MonitorSource[]>([])
  const [scheduler, setScheduler] = useState<SchedulerStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [checking, setChecking] = useState(false)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [newSource, setNewSource] = useState<CreateMonitorSource>({
    platform: 'bilibili',
    process_mode: 'summary',
    cron_expression: '0 22 * * *',
    enabled: 1,
  })

  const fetchSources = useCallback(async () => {
    try {
      const data = await getMonitorSources()
      setSources(data as any)
    } catch {
      toast.error('获取监控源列表失败')
    }
  }, [])

  const fetchScheduler = useCallback(async () => {
    try {
      const data = await getSchedulerStatus()
      setScheduler(data as any)
    } catch {}
  }, [])

  const initData = useCallback(async () => {
    setLoading(true)
    await Promise.all([fetchSources(), fetchScheduler()])
    setLoading(false)
  }, [fetchSources, fetchScheduler])

  useEffect(() => {
    initData()
  }, [initData])

  const handleCreate = async () => {
    try {
      await createMonitorSource(newSource)
      toast.success('监控源创建成功')
      setDialogOpen(false)
      setNewSource({
        platform: 'bilibili',
        process_mode: 'summary',
        cron_expression: '0 22 * * *',
        enabled: 1,
      })
      fetchSources()
    } catch {
      toast.error('创建失败')
    }
  }

  const handleToggle = async (source: MonitorSource) => {
    try {
      await updateMonitorSource(source.id, {
        enabled: source.enabled ? 0 : 1,
      })
      fetchSources()
    } catch {
      toast.error('更新失败')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteMonitorSource(id)
      toast.success('已删除')
      fetchSources()
    } catch {
      toast.error('删除失败')
    }
  }

  const handleCheck = async (sourceId?: number) => {
    setChecking(true)
    try {
      const result = await manualCheck(sourceId)
      const count = (result as any)?.new_count ?? 0
      toast.success(count > 0 ? `发现 ${count} 条新收藏` : '暂无新收藏')
      fetchSources()
    } catch {
      toast.error('检查失败')
    } finally {
      setChecking(false)
    }
  }

  const handleToggleScheduler = async () => {
    try {
      if (scheduler?.running) {
        await stopScheduler()
        toast.success('调度器已停止')
      } else {
        await startScheduler()
        toast.success('调度器已启动')
      }
      fetchScheduler()
    } catch {
      toast.error('操作失败')
    }
  }

  const getPlatformLabel = (p: string) =>
    PLATFORMS.find(x => x.value === p)?.label ?? p

  const getProcessModeLabel = (m: string) =>
    PROCESS_MODES.find(x => x.value === m)?.label ?? m

  return (
    <ScrollArea className="h-full overflow-y-auto bg-white">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">收藏监控</h1>
            <p className="text-muted-foreground text-sm">
              自动监控视频平台收藏夹，定时分析总结
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleCheck()}
              disabled={checking}
            >
              {checking ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="mr-2 h-4 w-4" />
              )}
              立即检查
            </Button>
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button size="sm">
                  <Plus className="mr-2 h-4 w-4" />
                  添加监控源
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>添加收藏监控源</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 pt-4">
                  <div>
                    <label className="mb-1 block text-sm font-medium">平台</label>
                    <Select
                      value={newSource.platform}
                      onValueChange={v =>
                        setNewSource({ ...newSource, platform: v })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {PLATFORMS.map(p => (
                          <SelectItem key={p.value} value={p.value}>
                            {p.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  {(newSource.platform === 'bilibili') && (
                    <div>
                      <label className="mb-1 block text-sm font-medium">
                        收藏夹 ID（留空则监控全部收藏夹）
                      </label>
                      <Input
                        placeholder="例如：1234567890"
                        value={newSource.source_id || ''}
                        onChange={e =>
                          setNewSource({ ...newSource, source_id: e.target.value })
                        }
                      />
                    </div>
                  )}
                  {newSource.platform === 'youtube' && (
                    <div>
                      <label className="mb-1 block text-sm font-medium">
                        播放列表 ID（默认 LL 为"稍后观看"）
                      </label>
                      <Input
                        placeholder="LL"
                        value={newSource.source_id || ''}
                        onChange={e =>
                          setNewSource({ ...newSource, source_id: e.target.value })
                        }
                      />
                    </div>
                  )}
                  <div>
                    <label className="mb-1 block text-sm font-medium">名称</label>
                    <Input
                      placeholder="例如：我的B站收藏"
                      value={newSource.source_name || ''}
                      onChange={e =>
                        setNewSource({ ...newSource, source_name: e.target.value })
                      }
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium">处理模式</label>
                    <Select
                      value={newSource.process_mode}
                      onValueChange={v =>
                        setNewSource({ ...newSource, process_mode: v })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {PROCESS_MODES.map(m => (
                          <SelectItem key={m.value} value={m.value}>
                            {m.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium">检查频率</label>
                    <Select
                      value={newSource.cron_expression}
                      onValueChange={v =>
                        setNewSource({ ...newSource, cron_expression: v })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {DEFAULT_CRON_OPTIONS.map(c => (
                          <SelectItem key={c.value} value={c.value}>
                            {c.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <Button className="w-full" onClick={handleCreate}>
                    创建
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        <Card className="mb-6">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
            <CardTitle className="text-base font-medium">
              <Clock className="mr-2 inline h-4 w-4 text-blue-500" />
              调度器状态
            </CardTitle>
            <div className="flex items-center gap-3">
              <Badge
                variant={scheduler?.running ? 'default' : 'secondary'}
                className={
                  scheduler?.running ? 'bg-green-500 hover:bg-green-600' : ''
                }
              >
                {scheduler?.running ? (
                  <>
                    <CheckCircle2 className="mr-1 h-3 w-3" />
                    运行中
                  </>
                ) : (
                  <>
                    <XCircle className="mr-1 h-3 w-3" />
                    已停止
                  </>
                )}
              </Badge>
              <Button
                variant="outline"
                size="sm"
                onClick={handleToggleScheduler}
              >
                {scheduler?.running ? '停止' : '启动'}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {scheduler?.jobs?.map(job => (
              <div key={job.id} className="text-sm text-muted-foreground">
                {job.name} — 下次执行：
                {job.next_run_time
                  ? new Date(job.next_run_time).toLocaleString('zh-CN')
                  : '未安排'}
              </div>
            ))}
          </CardContent>
        </Card>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        ) : sources.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Heart className="mb-4 h-12 w-12 text-gray-300" />
              <p className="text-lg font-medium text-gray-500">
                还没有配置监控源
              </p>
              <p className="text-sm text-gray-400">
                点击「添加监控源」开始监控你的视频收藏
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {sources.map(source => (
              <Card key={source.id}>
                <CardContent className="flex items-center justify-between py-4">
                  <div className="flex items-center gap-4">
                    <div
                      className={`flex h-10 w-10 items-center justify-center rounded-lg ${
                        source.enabled
                          ? 'bg-blue-100 text-blue-600'
                          : 'bg-gray-100 text-gray-400'
                      }`}
                    >
                      <Heart className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">
                          {source.source_name ||
                            `${getPlatformLabel(source.platform)} 收藏`}
                        </span>
                        <Badge variant="outline">
                          {getPlatformLabel(source.platform)}
                        </Badge>
                        <Badge variant="secondary">
                          {getProcessModeLabel(source.process_mode)}
                        </Badge>
                      </div>
                      <div className="mt-1 text-xs text-muted-foreground">
                        {source.last_check_at
                          ? `上次检查: ${new Date(source.last_check_at).toLocaleString('zh-CN')}`
                          : '尚未检查'}
                        {' · '}
                        频率: {DEFAULT_CRON_OPTIONS.find(c => c.value === source.cron_expression)?.label ?? source.cron_expression}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Switch
                      checked={source.enabled === 1}
                      onCheckedChange={() => handleToggle(source)}
                    />
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleCheck(source.id)}
                      disabled={checking}
                    >
                      <Play className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(source.id)}
                      className="text-red-500 hover:text-red-600"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        <div className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-medium">
                <FileText className="mr-2 inline h-4 w-4 text-green-500" />
                使用说明
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm text-muted-foreground">
              <p>1. 在「下载配置」中配置对应平台的 Cookie（必须）</p>
              <p>2. 添加监控源，选择平台和处理模式</p>
              <p>3. 启动调度器，系统将按设定频率自动检查收藏夹</p>
              <p>4. 轻量摘要模式：仅生成标题和简要总结，速度快</p>
              <p>5. 完整笔记模式：走完整的下载→转写→LLM总结流程</p>
              <p>6. 每日摘要可在「每日汇总」页面查看和导出</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </ScrollArea>
  )
}
