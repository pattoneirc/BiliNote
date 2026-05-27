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
  Bell,
  Plus,
  Trash2,
  Send,
  Loader2,
  CheckCircle2,
  XCircle,
  MessageSquare,
} from 'lucide-react'
import toast from 'react-hot-toast'
import {
  NotifyChannel,
  CreateNotifyChannel,
  getNotifyChannels,
  createNotifyChannel,
  updateNotifyChannel,
  deleteNotifyChannel,
  testNotifyChannel,
} from '@/services/monitor'

const CHANNEL_TYPES = [
  { value: 'feishu', label: '飞书', desc: '飞书群机器人 Webhook' },
  { value: 'wechat_work', label: '企业微信', desc: '企业微信群机器人 Webhook' },
  { value: 'dingtalk', label: '钉钉', desc: '钉钉群机器人 Webhook' },
  { value: 'custom', label: '自定义', desc: '自定义 Webhook 地址' },
]

export default function NotifySettings() {
  const [channels, setChannels] = useState<NotifyChannel[]>([])
  const [loading, setLoading] = useState(true)
  const [testing, setTesting] = useState<number | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [newChannel, setNewChannel] = useState<CreateNotifyChannel>({
    channel_type: 'feishu',
    webhook_url: '',
    name: '',
    notify_on_digest: 1,
    notify_on_new_favorite: 0,
    notify_on_error: 0,
  })

  const fetchChannels = useCallback(async () => {
    try {
      const data = await getNotifyChannels()
      setChannels(data as any)
    } catch {
      toast.error('获取通知渠道列表失败')
    }
  }, [])

  useEffect(() => {
    setLoading(true)
    fetchChannels().finally(() => setLoading(false))
  }, [fetchChannels])

  const handleCreate = async () => {
    if (!newChannel.webhook_url) {
      toast.error('请填写 Webhook 地址')
      return
    }
    try {
      await createNotifyChannel(newChannel)
      toast.success('通知渠道创建成功')
      setDialogOpen(false)
      setNewChannel({
        channel_type: 'feishu',
        webhook_url: '',
        name: '',
        notify_on_digest: 1,
        notify_on_new_favorite: 0,
        notify_on_error: 0,
      })
      fetchChannels()
    } catch {
      toast.error('创建失败')
    }
  }

  const handleToggle = async (channel: NotifyChannel) => {
    try {
      await updateNotifyChannel(channel.id, {
        enabled: channel.enabled ? 0 : 1,
      })
      fetchChannels()
    } catch {
      toast.error('更新失败')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteNotifyChannel(id)
      toast.success('已删除')
      fetchChannels()
    } catch {
      toast.error('删除失败')
    }
  }

  const handleTest = async (id: number) => {
    setTesting(id)
    try {
      await testNotifyChannel(id)
      toast.success('测试通知发送成功，请检查对应平台')
    } catch {
      toast.error('测试通知发送失败')
    } finally {
      setTesting(null)
    }
  }

  const getChannelLabel = (type: string) =>
    CHANNEL_TYPES.find(c => c.value === type)?.label ?? type

  return (
    <ScrollArea className="h-full overflow-y-auto bg-white">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">通知设置</h1>
            <p className="text-muted-foreground text-sm">
              配置每日摘要推送到飞书、企业微信、钉钉等平台
            </p>
          </div>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button size="sm">
                <Plus className="mr-2 h-4 w-4" />
                添加通知渠道
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>添加通知渠道</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 pt-4">
                <div>
                  <label className="mb-1 block text-sm font-medium">平台类型</label>
                  <Select
                    value={newChannel.channel_type}
                    onValueChange={v =>
                      setNewChannel({ ...newChannel, channel_type: v })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {CHANNEL_TYPES.map(c => (
                        <SelectItem key={c.value} value={c.value}>
                          {c.label} — {c.desc}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium">名称</label>
                  <Input
                    placeholder="例如：我的飞书群"
                    value={newChannel.name || ''}
                    onChange={e =>
                      setNewChannel({ ...newChannel, name: e.target.value })
                    }
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium">
                    Webhook 地址
                  </label>
                  <Input
                    placeholder={
                      newChannel.channel_type === 'feishu'
                        ? 'https://open.feishu.cn/open-apis/bot/v2/hook/xxx'
                        : newChannel.channel_type === 'wechat_work'
                          ? 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx'
                          : newChannel.channel_type === 'dingtalk'
                            ? 'https://oapi.dingtalk.com/robot/send?access_token=xxx'
                            : 'https://your-webhook-url'
                    }
                    value={newChannel.webhook_url}
                    onChange={e =>
                      setNewChannel({ ...newChannel, webhook_url: e.target.value })
                    }
                  />
                </div>
                {(newChannel.channel_type === 'feishu' ||
                  newChannel.channel_type === 'dingtalk') && (
                  <div>
                    <label className="mb-1 block text-sm font-medium">
                      签名密钥（可选）
                    </label>
                    <Input
                      placeholder="飞书/钉钉机器人的签名密钥"
                      value={newChannel.secret || ''}
                      onChange={e =>
                        setNewChannel({ ...newChannel, secret: e.target.value })
                      }
                    />
                  </div>
                )}
                <div className="space-y-3 rounded-lg border p-4">
                  <div className="text-sm font-medium">通知事件</div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">每日摘要生成时通知</span>
                    <Switch
                      checked={newChannel.notify_on_digest === 1}
                      onCheckedChange={v =>
                        setNewChannel({
                          ...newChannel,
                          notify_on_digest: v ? 1 : 0,
                        })
                      }
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">新增收藏视频时通知</span>
                    <Switch
                      checked={newChannel.notify_on_new_favorite === 1}
                      onCheckedChange={v =>
                        setNewChannel({
                          ...newChannel,
                          notify_on_new_favorite: v ? 1 : 0,
                        })
                      }
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">监控异常时通知</span>
                    <Switch
                      checked={newChannel.notify_on_error === 1}
                      onCheckedChange={v =>
                        setNewChannel({
                          ...newChannel,
                          notify_on_error: v ? 1 : 0,
                        })
                      }
                    />
                  </div>
                </div>
                <Button className="w-full" onClick={handleCreate}>
                  创建
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        ) : channels.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Bell className="mb-4 h-12 w-12 text-gray-300" />
              <p className="text-lg font-medium text-gray-500">
                还没有配置通知渠道
              </p>
              <p className="text-sm text-gray-400">
                添加飞书/企业微信/钉钉 Webhook，自动推送每日摘要
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {channels.map(channel => (
              <Card key={channel.id}>
                <CardContent className="flex items-center justify-between py-4">
                  <div className="flex items-center gap-4">
                    <div
                      className={`flex h-10 w-10 items-center justify-center rounded-lg ${
                        channel.enabled
                          ? 'bg-green-100 text-green-600'
                          : 'bg-gray-100 text-gray-400'
                      }`}
                    >
                      <MessageSquare className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">
                          {channel.name || getChannelLabel(channel.channel_type)}
                        </span>
                        <Badge variant="outline">
                          {getChannelLabel(channel.channel_type)}
                        </Badge>
                        {channel.notify_on_digest === 1 && (
                          <Badge variant="secondary" className="text-xs">
                            每日摘要
                          </Badge>
                        )}
                        {channel.notify_on_new_favorite === 1 && (
                          <Badge variant="secondary" className="text-xs">
                            新收藏
                          </Badge>
                        )}
                      </div>
                      <div className="mt-1 text-xs text-muted-foreground">
                        {channel.webhook_url?.substring(0, 60)}
                        {channel.webhook_url?.length > 60 ? '...' : ''}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Switch
                      checked={channel.enabled === 1}
                      onCheckedChange={() => handleToggle(channel)}
                    />
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleTest(channel.id)}
                      disabled={testing === channel.id}
                    >
                      {testing === channel.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Send className="h-4 w-4" />
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(channel.id)}
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
                📖 Webhook 配置指南
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <div>
                <h4 className="font-medium text-blue-600">飞书</h4>
                <ol className="mt-1 list-inside list-decimal text-muted-foreground">
                  <li>打开飞书群 → 设置 → 群机器人 → 添加机器人 → 自定义机器人</li>
                  <li>复制 Webhook 地址填入上方</li>
                  <li>如启用了签名校验，将签名密钥也填入</li>
                </ol>
              </div>
              <div>
                <h4 className="font-medium text-green-600">企业微信</h4>
                <ol className="mt-1 list-inside list-decimal text-muted-foreground">
                  <li>打开企业微信群 → 添加群机器人</li>
                  <li>复制 Webhook 地址填入上方</li>
                </ol>
              </div>
              <div>
                <h4 className="font-medium text-blue-500">钉钉</h4>
                <ol className="mt-1 list-inside list-decimal text-muted-foreground">
                  <li>打开钉钉群 → 群设置 → 智能群助手 → 添加机器人 → 自定义</li>
                  <li>安全设置选择「加签」，复制签名密钥</li>
                  <li>复制 Webhook 地址和签名密钥填入上方</li>
                </ol>
              </div>
              <div>
                <h4 className="font-medium text-purple-600">自定义 Webhook</h4>
                <p className="mt-1 text-muted-foreground">
                  支持 POST JSON 格式（{"{"}"title", "content"{"}"}），可用于对接任意平台
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </ScrollArea>
  )
}
