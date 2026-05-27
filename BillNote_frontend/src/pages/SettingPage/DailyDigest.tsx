import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Calendar,
  FileText,
  Loader2,
  RefreshCw,
  Sparkles,
  Video,
  Download,
} from 'lucide-react'
import toast from 'react-hot-toast'
import {
  DailyDigest,
  getDigests,
  getDigest,
  generateDigest,
} from '@/services/monitor'

export default function DailyDigestPage() {
  const [digests, setDigests] = useState<DailyDigest[]>([])
  const [selectedDigest, setSelectedDigest] = useState<DailyDigest | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [detailOpen, setDetailOpen] = useState(false)

  const fetchDigests = useCallback(async () => {
    try {
      const data = await getDigests(30)
      setDigests(data as any)
    } catch {
      toast.error('获取摘要列表失败')
    }
  }, [])

  useEffect(() => {
    setLoading(true)
    fetchDigests().finally(() => setLoading(false))
  }, [fetchDigests])

  const handleViewDigest = async (id: number) => {
    try {
      const data = await getDigest(id)
      setSelectedDigest(data as any)
      setDetailOpen(true)
    } catch {
      toast.error('获取摘要详情失败')
    }
  }

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      await generateDigest()
      toast.success('摘要生成任务已启动，请稍后刷新查看')
      setTimeout(() => fetchDigests(), 3000)
    } catch {
      toast.error('生成摘要失败')
    } finally {
      setGenerating(false)
    }
  }

  const handleExport = (digest: DailyDigest) => {
    if (!digest.markdown_content) {
      toast.error('摘要内容为空')
      return
    }
    const blob = new Blob([digest.markdown_content], {
      type: 'text/markdown;charset=utf-8',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `digest_${digest.digest_date}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <ScrollArea className="h-full overflow-y-auto bg-white">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">每日汇总</h1>
            <p className="text-muted-foreground text-sm">
              查看和管理每日视频收藏摘要
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchDigests()}
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              刷新
            </Button>
            <Button
              size="sm"
              onClick={handleGenerate}
              disabled={generating}
            >
              {generating ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="mr-2 h-4 w-4" />
              )}
              生成本日摘要
            </Button>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        ) : digests.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <FileText className="mb-4 h-12 w-12 text-gray-300" />
              <p className="text-lg font-medium text-gray-500">
                暂无每日摘要
              </p>
              <p className="text-sm text-gray-400">
                配置收藏监控后，系统会自动生成每日摘要
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {digests.map(digest => (
              <Card
                key={digest.id}
                className="cursor-pointer transition-shadow hover:shadow-md"
                onClick={() => handleViewDigest(digest.id)}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base font-medium">
                      {digest.digest_date}
                    </CardTitle>
                    <div className="flex items-center gap-1">
                      {digest.platform?.split(',').map(p => (
                        <Badge key={p} variant="outline" className="text-xs">
                          {p}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <Video className="h-3.5 w-3.5" />
                      {digest.video_count} 个视频
                    </div>
                    <div className="flex items-center gap-1">
                      <Calendar className="h-3.5 w-3.5" />
                      {new Date(digest.created_at || '').toLocaleDateString('zh-CN')}
                    </div>
                  </div>
                  <div className="mt-3 flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={e => {
                        e.stopPropagation()
                        handleExport(digest)
                      }}
                    >
                      <Download className="mr-1 h-3.5 w-3.5" />
                      导出
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
          <DialogContent className="max-w-3xl max-h-[80vh]">
            <DialogHeader>
              <DialogTitle>
                {selectedDigest?.title || '每日摘要'}
              </DialogTitle>
            </DialogHeader>
            <ScrollArea className="max-h-[60vh] pr-4">
              {selectedDigest?.markdown_content ? (
                <div className="prose prose-sm max-w-none">
                  <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">
                    {selectedDigest.markdown_content}
                  </pre>
                </div>
              ) : (
                <div className="py-8 text-center text-muted-foreground">
                  摘要内容为空
                </div>
              )}
            </ScrollArea>
            {selectedDigest && (
              <div className="flex justify-end pt-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleExport(selectedDigest)}
                >
                  <Download className="mr-2 h-4 w-4" />
                  导出 Markdown
                </Button>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </ScrollArea>
  )
}
