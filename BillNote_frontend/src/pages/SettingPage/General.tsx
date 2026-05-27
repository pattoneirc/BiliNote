import { useEffect, useState } from 'react'
import { Switch } from '@/components/ui/switch'
import { Card, CardContent } from '@/components/ui/card'
import { Rocket, Monitor } from 'lucide-react'

export default function GeneralSettings() {
  const [autostartEnabled, setAutostartEnabled] = useState(false)
  const [loading, setLoading] = useState(true)
  const isTauri = typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window

  useEffect(() => {
    if (!isTauri) {
      setLoading(false)
      return
    }
    checkAutostart()
  }, [])

  async function checkAutostart() {
    try {
      const { isEnabled } = await import('@tauri-apps/plugin-autostart')
      const enabled = await isEnabled()
      setAutostartEnabled(enabled)
    } catch {
      console.error('Failed to check autostart status')
    } finally {
      setLoading(false)
    }
  }

  async function toggleAutostart(enabled: boolean) {
    if (!isTauri) return
    try {
      const autostart = await import('@tauri-apps/plugin-autostart')
      if (enabled) {
        await autostart.enable()
      } else {
        await autostart.disable()
      }
      setAutostartEnabled(enabled)
    } catch (e) {
      console.error('Failed to toggle autostart:', e)
    }
  }

  if (!isTauri) {
    return (
      <div className="flex h-full flex-col gap-6 p-6">
        <div>
          <h2 className="text-2xl font-medium">通用设置</h2>
          <p className="text-sm text-gray-500">应用基础配置</p>
        </div>
        <Card>
          <CardContent className="py-8 text-center text-gray-400">
            开机自启动仅支持桌面客户端
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col gap-6 p-6">
      <div>
        <h2 className="text-2xl font-medium">通用设置</h2>
        <p className="text-sm text-gray-500">应用基础配置</p>
      </div>

      <Card>
        <CardContent className="space-y-6 pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-primary/10 text-primary flex h-10 w-10 items-center justify-center rounded-lg">
                <Rocket className="h-5 w-5" />
              </div>
              <div>
                <p className="font-medium">开机自启动</p>
                <p className="text-sm text-gray-500">系统启动时自动运行 BiliNote</p>
              </div>
            </div>
            <Switch
              checked={autostartEnabled}
              onCheckedChange={toggleAutostart}
              disabled={loading}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-primary/10 text-primary flex h-10 w-10 items-center justify-center rounded-lg">
                <Monitor className="h-5 w-5" />
              </div>
              <div>
                <p className="font-medium">最小化到系统托盘</p>
                <p className="text-sm text-gray-500">关闭窗口时最小化到托盘而非退出</p>
              </div>
            </div>
            <Switch disabled checked={false} />
          </div>
        </CardContent>
      </Card>

      <p className="text-xs text-gray-400">
        开机自启动通过系统注册表实现，可在任务管理器「启动」选项卡中查看和管理。
      </p>
    </div>
  )
}
