# BiliNote 项目修改记录与功能文档

> 本文档记录了基于 BiliNote v2.3.3 的所有功能扩展、代码修改、项目结构和实现路径。

---

## 一、新增功能概览

### 1. 收藏视频监控

自动监控 Bilibili、抖音、快手、YouTube 的收藏夹，定时检测新增收藏视频并自动生成笔记。

| 特性 | 说明 |
|------|------|
| 支持平台 | Bilibili、抖音、快手、YouTube |
| 调度方式 | 后端 APScheduler 定时 + 前端手动触发 |
| 处理模式 | 轻量摘要（快速）/ 完整笔记（下载→转写→LLM总结） |
| 检查频率 | 可配置，默认每天 22:00 |
| 去重机制 | 基于 video_id + platform 判重，避免重复处理 |

### 2. 每日摘要生成

将每天收藏的视频笔记自动汇总为结构化 Markdown 文档。

| 特性 | 说明 |
|------|------|
| 输出格式 | Markdown 文件 + 网页查看 |
| 生成方式 | 手动模板 / AI 生成（需配置 LLM） |
| 保存位置 | `digest_results/digest_YYYY-MM-DD.md` |
| 导出 | 前端一键导出 Markdown 文件 |

### 3. 通知推送

每日摘要生成后自动推送到飞书、企业微信、钉钉等平台。

| 平台 | 推送格式 | 签名校验 |
|------|----------|----------|
| 飞书 | 富文本卡片消息 | ✅ 支持签名密钥 |
| 企业微信 | Markdown 消息 | ❌ 不需要 |
| 钉钉 | Markdown 消息 | ✅ 支持加签 |
| 自定义 Webhook | JSON POST | 可对接任意平台 |

| 通知事件 | 说明 |
|----------|------|
| 每日摘要生成 | 摘要生成完成后自动推送 |
| 新增收藏视频 | 可选，发现新收藏时推送 |
| 监控异常 | 可选，监控任务失败时推送 |

---

## 二、修改文件清单

### 后端新增文件

```
backend/
├── app/
│   ├── db/
│   │   ├── models/
│   │   │   └── monitor.py                          # 新增：MonitorSource、DailyDigest、FavoriteVideo、NotifyChannel 数据模型
│   │   └── monitor_dao.py                           # 新增：监控源、收藏视频、每日摘要、通知渠道 DAO 层
│   ├── downloaders/
│   │   └── favorites/                               # 新增：收藏夹抓取模块
│   │       ├── __init__.py                          # 平台注册表
│   │       ├── base.py                              # BaseFavoritesFetcher 抽象基类 + FavoriteVideoItem 数据类
│   │       ├── bilibili_favorites.py                # B站收藏夹 API（多收藏夹、分页、时间过滤）
│   │       ├── douyin_favorites.py                  # 抖音收藏列表 API（ABogus 签名）
│   │       ├── kuaishou_favorites.py                # 快手收藏列表 API（GraphQL）
│   │       └── youtube_favorites.py                 # YouTube 收藏/稍后观看 API（yt-dlp）
│   ├── routers/
│   │   └── monitor.py                               # 新增：16+ API 路由（监控源 CRUD、手动检查、摘要、通知渠道）
│   └── services/
│       ├── favorites_monitor.py                     # 新增：收藏监控核心服务
│       ├── daily_digest.py                          # 新增：每日摘要生成服务
│       ├── monitor_scheduler.py                     # 新增：APScheduler 调度器
│       └── notify_service.py                        # 新增：通知推送服务（飞书/企业微信/钉钉/自定义）
└── BiliNoteBackend.spec                             # 新增：PyInstaller 打包配置
```

### 后端修改文件

| 文件 | 修改内容 |
|------|----------|
| `app/__init__.py` | 注册 monitor 路由到 FastAPI 应用 |
| `app/db/init_db.py` | 导入 MonitorSource、DailyDigest、FavoriteVideo、NotifyChannel 模型 |
| `main.py` | lifespan 中启动/停止 APScheduler 调度器（步骤 5/6） |
| `requirements.txt` | 新增 `APScheduler>=3.10.0` |

### 前端新增文件

```
BillNote_frontend/src/
├── services/
│   └── monitor.ts                                   # 新增：收藏监控 API 服务层（所有接口封装）
└── pages/SettingPage/
    ├── FavoritesMonitor.tsx                          # 新增：收藏监控设置页面
    ├── DailyDigest.tsx                               # 新增：每日汇总查看页面
    └── NotifySettings.tsx                            # 新增：通知配置页面
```

### 前端修改文件

| 文件 | 修改内容 |
|------|----------|
| `src/App.tsx` | 新增 FavoritesMonitor、DailyDigest、NotifySettings 懒加载和路由 |
| `src/pages/SettingPage/Menu.tsx` | 新增「收藏监控」「每日汇总」「通知设置」三个菜单项 |

### 配置文件修改

| 文件 | 修改内容 |
|------|----------|
| `.env` | 新增 `DIGEST_OUTPUT_DIR`、`MONITOR_CRON` 配置项 |
| `backend/.env` | 同步新增配置项 |

---

## 三、数据库模型

### MonitorSource（监控源）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增主键 |
| platform | String | 平台标识（bilibili/douyin/kuaishou/youtube） |
| source_type | String | 来源类型，默认 favorites |
| source_id | String | 收藏夹 ID（B站）或播放列表 ID（YouTube） |
| source_name | String | 监控源名称 |
| enabled | Integer | 是否启用（1/0） |
| process_mode | String | 处理模式（summary/full） |
| cron_expression | String | Cron 表达式，默认 `0 22 * * *` |
| last_check_at | DateTime | 上次检查时间 |
| last_video_id | String | 上次检查到的最新视频 ID |
| model_name | String | 使用的 LLM 模型名称 |
| provider_id | String | 使用的 LLM 供应商 ID |
| note_style | String | 笔记风格 |
| note_format | String | 笔记格式 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### FavoriteVideo（收藏视频）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增主键 |
| video_id | String | 视频 ID |
| platform | String | 平台标识 |
| title | String | 视频标题 |
| url | String | 视频链接 |
| cover_url | String | 封面图 |
| author | String | 作者 |
| duration | Integer | 时长（秒） |
| favorited_at | DateTime | 收藏时间 |
| processed | Integer | 是否已处理（0/1） |
| task_id | String | 关联的笔记生成任务 ID |
| digest_id | Integer | 关联的每日摘要 ID |
| monitor_source_id | Integer | 关联的监控源 ID |
| created_at | DateTime | 创建时间 |

### DailyDigest（每日摘要）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增主键 |
| digest_date | String | 摘要日期（YYYY-MM-DD） |
| title | String | 摘要标题 |
| markdown_content | Text | Markdown 内容 |
| video_count | Integer | 视频数量 |
| platform | String | 涉及平台（逗号分隔） |
| file_path | String | 本地文件路径 |
| created_at | DateTime | 创建时间 |

### NotifyChannel（通知渠道）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增主键 |
| channel_type | String | 渠道类型（feishu/wechat_work/dingtalk/custom） |
| name | String | 渠道名称 |
| webhook_url | String | Webhook 地址 |
| secret | String | 签名密钥 |
| enabled | Integer | 是否启用 |
| notify_on_digest | Integer | 摘要生成时通知 |
| notify_on_new_favorite | Integer | 新收藏时通知 |
| notify_on_error | Integer | 异常时通知 |
| template | Text | 自定义消息模板 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

---

## 四、API 接口

### 监控源管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/monitor_source` | 创建监控源 |
| GET | `/api/monitor_sources` | 获取所有监控源 |
| GET | `/api/monitor_source/{id}` | 获取单个监控源 |
| PUT | `/api/monitor_source/{id}` | 更新监控源 |
| DELETE | `/api/monitor_source/{id}` | 删除监控源 |

### 监控操作

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/monitor/check` | 手动触发检查（可指定单个源） |
| POST | `/api/monitor/process` | 处理未处理的收藏视频 |
| POST | `/api/monitor/digest` | 手动生成每日摘要 |

### 每日摘要

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/digests` | 获取摘要列表 |
| GET | `/api/digest/{id}` | 获取摘要详情 |

### 收藏视频

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/favorite_videos` | 获取收藏视频列表 |

### 调度器控制

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/monitor/scheduler/start` | 启动调度器 |
| POST | `/api/monitor/scheduler/stop` | 停止调度器 |
| GET | `/api/monitor/scheduler/status` | 获取调度器状态 |
| PUT | `/api/monitor/scheduler/cron` | 更新调度频率 |

### 通知渠道

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/notify_channel` | 创建通知渠道 |
| GET | `/api/notify_channels` | 获取通知渠道列表 |
| PUT | `/api/notify_channel/{id}` | 更新通知渠道 |
| DELETE | `/api/notify_channel/{id}` | 删除通知渠道 |
| POST | `/api/notify_channel/{id}/test` | 测试通知渠道 |

---

## 五、实现路径与核心流程

### 5.1 收藏监控流程

```
APScheduler 定时触发 / 用户手动触发
        │
        ▼
FavoritesMonitorService.run_monitor_cycle()
        │
        ├── 遍历所有已启用的 MonitorSource
        │       │
        │       ▼
        │   get_favorites_fetcher(platform)  ← 根据平台获取对应 Fetcher
        │       │
        │       ▼
        │   fetcher.fetch_favorites(cookie, since=last_check_at)
        │       │
        │       ├── BilibiliFavoritesFetcher: 调用 /x/v3/fav/resource/list API
        │       ├── DouyinFavoritesFetcher: 调用 /aweme/v1/web/aweme/favorite/ API（含 ABogus 签名）
        │       ├── KuaishouFavoritesFetcher: 调用 GraphQL API
        │       └── YouTubeFavoritesFetcher: 使用 yt-dlp 提取播放列表
        │       │
        │       ▼
        │   过滤已存在的视频（FavoriteVideoDAO.exists 去重）
        │       │
        │       ▼
        │   FavoriteVideoDAO.create()  ← 保存新收藏视频到数据库
        │       │
        │       ▼
        │   MonitorSourceDAO.update_last_check()  ← 更新最后检查时间
        │
        ▼
FavoritesMonitorService.process_unprocessed_videos()
        │
        ├── 遍历未处理的 FavoriteVideo（processed=0）
        │       │
        │       ▼
        │   NoteGenerator.generate()  ← 调用现有笔记生成流程
        │       │
        │       ├── summary 模式: quality=fast, style=简洁
        │       └── full 模式: quality=medium, 完整下载→转写→LLM总结
        │       │
        │       ▼
        │   FavoriteVideoDAO.mark_processed()  ← 标记为已处理
        │
        ▼
    完成
```

### 5.2 每日摘要生成流程

```
DailyDigestService.generate_daily_digest(target_date)
        │
        ▼
FavoriteVideoDAO.get_by_date_range(start, end)  ← 查询当天收藏视频
        │
        ▼
遍历视频，读取关联笔记（note_results/{task_id}.json）
        │
        ▼
判断是否有 LLM 配置
        │
        ├── 有配置 → _build_ai_digest()  ← AI 生成结构化摘要
        │              │
        │              ▼
        │          GPTFactory.from_config() → gpt.summarize()
        │
        └── 无配置 → _build_manual_digest()  ← 模板生成摘要
                       │
                       ▼
                   按平台分类 + 视频信息 + 要点提取
        │
        ▼
_save_digest_file()  ← 保存为 digest_results/digest_YYYY-MM-DD.md
        │
        ▼
DailyDigestDAO.create/update()  ← 保存到数据库
        │
        ▼
NotifyService.notify_digest()  ← 推送通知到已配置的渠道
        │
        ├── 飞书: POST 富文本卡片（含签名校验）
        ├── 企业微信: POST Markdown 消息
        ├── 钉钉: POST Markdown 消息（含加签）
        └── 自定义: POST JSON
```

### 5.3 调度器流程

```
应用启动（main.py lifespan）
        │
        ▼
start_scheduler()
        │
        ▼
AsyncIOScheduler(timezone="Asia/Shanghai")
        │
        ▼
添加定时任务: _run_monitor_and_digest
        │   触发条件: MONITOR_CRON 环境变量（默认 0 22 * * *）
        │
        ▼
_run_monitor_and_digest()
        │
        ├── FavoritesMonitorService.run_monitor_cycle()  ← 检查收藏 + 处理视频
        │
        └── DailyDigestService.generate_daily_digest()  ← 生成每日摘要
        │
        ▼
应用关闭
        │
        ▼
stop_scheduler()  ← 优雅关闭调度器
```

### 5.4 通知推送流程

```
触发事件（摘要生成 / 新收藏 / 异常）
        │
        ▼
NotifyService.notify_xxx()
        │
        ▼
NotifyChannelDAO.get_enabled()  ← 获取所有已启用的通知渠道
        │
        ▼
遍历渠道，检查对应事件是否开启
        │
        ▼
NotifyService.send_to_channel()
        │
        ├── feishu → _send_feishu()
        │     POST {msg_type: "interactive", card: {...}}
        │     含签名: HMAC-SHA256(timestamp + "\n" + secret)
        │
        ├── wechat_work → _send_wechat_work()
        │     POST {msgtype: "markdown", markdown: {content: ...}}
        │
        ├── dingtalk → _send_dingtalk()
        │     POST {msgtype: "markdown", markdown: {title, text}}
        │     含加签: HMAC-SHA256(timestamp + "\n" + secret)
        │
        └── custom → _send_custom()
              POST {title, content}
```

---

## 六、完整项目结构

```
BiliNote/
│
├── .env                                    # 全局环境变量配置
├── docker-compose.yml                      # Docker Compose 编排
├── nginx/
│   └── default.conf                        # Nginx 反向代理配置
│
├── backend/                                # Python FastAPI 后端
│   ├── .env                                # 后端环境变量
│   ├── main.py                             # 应用入口（lifespan 启动序列）
│   ├── BiliNoteBackend.spec                # PyInstaller 打包配置
│   ├── requirements.txt                    # Python 依赖
│   ├── bili_note.db                        # SQLite 数据库（运行时生成）
│   │
│   ├── app/
│   │   ├── __init__.py                     # FastAPI 应用工厂（注册路由）
│   │   │
│   │   ├── routers/                        # API 路由层
│   │   │   ├── note.py                     # 笔记生成 API
│   │   │   ├── provider.py                 # LLM 供应商 API
│   │   │   ├── model.py                    # 模型管理 API
│   │   │   ├── config.py                   # 配置管理 API（Cookie 等）
│   │   │   ├── chat.py                     # AI 问答 API
│   │   │   └── monitor.py                  # 【新增】收藏监控 API（16+ 接口）
│   │   │
│   │   ├── services/                       # 业务逻辑层
│   │   │   ├── note.py                     # 笔记生成服务
│   │   │   ├── provider.py                 # 供应商管理
│   │   │   ├── cookie_manager.py           # Cookie 配置管理
│   │   │   ├── proxy_config_manager.py     # 代理配置管理
│   │   │   ├── task_serial_executor.py     # 任务串行执行器
│   │   │   ├── constant.py                 # 平台映射常量
│   │   │   ├── favorites_monitor.py        # 【新增】收藏监控核心服务
│   │   │   ├── daily_digest.py             # 【新增】每日摘要生成服务
│   │   │   ├── monitor_scheduler.py        # 【新增】APScheduler 调度器
│   │   │   └── notify_service.py           # 【新增】通知推送服务
│   │   │
│   │   ├── downloaders/                    # 下载器层
│   │   │   ├── base.py                     # 下载器抽象基类
│   │   │   ├── bilibili_downloader.py      # B站下载器（yt-dlp + cookie）
│   │   │   ├── bilibili_subtitle.py        # B站字幕抓取（player API）
│   │   │   ├── douyin_downloader.py        # 抖音下载器（ABogus 签名）
│   │   │   ├── youtube_downloader.py       # YouTube 下载器（yt-dlp）
│   │   │   ├── youtube_subtitle.py         # YouTube 字幕抓取
│   │   │   ├── kuaishou_downloader.py      # 快手下载器（GraphQL）
│   │   │   ├── local_downloader.py         # 本地视频下载器
│   │   │   │
│   │   │   ├── douyin_helper/              # 抖音反爬辅助
│   │   │   │   ├── abogus.py               # ABogus 签名（SM3 算法）
│   │   │   │   └── mstoken.py              # msToken 获取
│   │   │   │
│   │   │   ├── kuaishou_helper/            # 快手辅助
│   │   │   │   └── kuaishou.py             # GraphQL 请求
│   │   │   │
│   │   │   └── favorites/                  # 【新增】收藏夹抓取模块
│   │   │       ├── __init__.py             # 平台注册表
│   │   │       ├── base.py                 # 抽象基类 + FavoriteVideoItem
│   │   │       ├── bilibili_favorites.py   # B站收藏夹 API
│   │   │       ├── douyin_favorites.py     # 抖音收藏列表 API
│   │   │       ├── kuaishou_favorites.py   # 快手收藏列表 API
│   │   │       └── youtube_favorites.py    # YouTube 收藏 API
│   │   │
│   │   ├── gpt/                            # LLM 集成层
│   │   │   ├── base.py                     # GPT 抽象基类
│   │   │   ├── gpt_factory.py              # GPT 工厂（按供应商创建实例）
│   │   │   ├── openai_gpt.py               # OpenAI 实现
│   │   │   ├── deepseek_gpt.py             # DeepSeek 实现
│   │   │   └── qwen_gpt.py                 # 通义千问实现
│   │   │
│   │   ├── transcriber/                    # 音频转写层
│   │   │   ├── transcriber_provider.py     # 转写器工厂
│   │   │   ├── fast_whisper_transcriber.py # faster-whisper 实现
│   │   │   └── ...
│   │   │
│   │   ├── db/                             # 数据库层
│   │   │   ├── engine.py                   # SQLAlchemy 引擎
│   │   │   ├── init_db.py                  # 建表初始化
│   │   │   ├── models/
│   │   │   │   ├── models.py               # Model 模型
│   │   │   │   ├── providers.py            # Provider 模型
│   │   │   │   ├── video_tasks.py          # VideoTask 模型
│   │   │   │   └── monitor.py              # 【新增】MonitorSource/DailyDigest/FavoriteVideo/NotifyChannel
│   │   │   ├── model_dao.py                # Model DAO
│   │   │   ├── provider_dao.py             # Provider DAO
│   │   │   ├── video_task_dao.py           # VideoTask DAO
│   │   │   └── monitor_dao.py              # 【新增】MonitorSource/FavoriteVideo/DailyDigest/NotifyChannel DAO
│   │   │
│   │   ├── models/                         # Pydantic 模型
│   │   │   ├── model_config.py             # LLM 配置模型
│   │   │   ├── gpt_model.py                # GPT 请求模型
│   │   │   └── ...
│   │   │
│   │   ├── enmus/                          # 枚举
│   │   │   ├── task_status_enums.py        # 任务状态枚举
│   │   │   ├── note_enums.py              # 笔记枚举
│   │   │   └── ...
│   │   │
│   │   ├── events/                         # 事件处理
│   │   │   └── handler.py                  # 事件注册
│   │   │
│   │   └── utils/                          # 工具
│   │       ├── logger.py                   # 日志
│   │       ├── response.py                 # 统一响应封装
│   │       └── url_parser.py               # URL 解析
│   │
│   ├── config/                             # 运行时配置（JSON）
│   │   ├── transcriber.json                # 转写器配置
│   │   └── downloader.json                 # 下载器配置（含 Cookie）
│   │
│   ├── note_results/                       # 笔记输出目录
│   ├── digest_results/                     # 【新增】每日摘要输出目录
│   ├── static/screenshots/                 # 视频截图
│   └── uploads/                            # 上传文件
│
├── BillNote_frontend/                      # React 前端
│   ├── package.json                        # 依赖配置
│   ├── vite.config.ts                      # Vite 配置
│   ├── tailwind.config.js                  # TailwindCSS 配置
│   │
│   ├── src/
│   │   ├── App.tsx                         # 应用入口（路由定义）
│   │   ├── main.tsx                        # 渲染入口
│   │   │
│   │   ├── pages/
│   │   │   ├── Index.tsx                   # 首页布局
│   │   │   ├── HomePage/Home.tsx           # 主页（笔记生成）
│   │   │   ├── SettingPage/
│   │   │   │   ├── index.tsx               # 设置页布局
│   │   │   │   ├── Menu.tsx                # 设置菜单
│   │   │   │   ├── Model.tsx               # AI 模型设置
│   │   │   │   ├── Transcriber.tsx         # 转写器配置
│   │   │   │   ├── Downloader.tsx          # 下载配置
│   │   │   │   ├── Monitor.tsx             # 部署监控
│   │   │   │   ├── AboutPage.tsx           # 关于
│   │   │   │   ├── FavoritesMonitor.tsx    # 【新增】收藏监控设置
│   │   │   │   ├── DailyDigest.tsx         # 【新增】每日汇总查看
│   │   │   │   └── NotifySettings.tsx      # 【新增】通知配置
│   │   │   └── Onboarding/                 # 引导页
│   │   │
│   │   ├── services/                       # API 服务层
│   │   │   ├── system.ts                   # 系统服务
│   │   │   ├── downloader.ts              # 下载器服务
│   │   │   ├── model.ts                    # 模型服务
│   │   │   └── monitor.ts                  # 【新增】收藏监控 API 服务
│   │   │
│   │   ├── components/                     # UI 组件
│   │   │   ├── ui/                         # shadcn/ui 基础组件
│   │   │   ├── Form/                       # 表单组件
│   │   │   └── ...
│   │   │
│   │   ├── hooks/                          # React Hooks
│   │   │   ├── useTaskPolling.ts           # 任务轮询
│   │   │   └── ...
│   │   │
│   │   └── utils/
│   │       └── request.ts                  # HTTP 请求封装
│   │
│   └── src-tauri/                          # Tauri 桌面端
│       ├── tauri.conf.json                 # Tauri 配置
│       ├── Cargo.toml                      # Rust 依赖
│       ├── src/
│       │   ├── main.rs                     # Rust 入口
│       │   └── lib.rs                      # 核心逻辑（sidecar 管理、就绪探测）
│       ├── capabilities/default.json       # 权限配置
│       ├── icons/                          # 应用图标
│       └── bin/
│           └── BiliNoteBackend/            # 【新增】PyInstaller 打包的后端
│               ├── BiliNoteBackend.exe     # 后端可执行文件
│               └── _internal/              # Python 运行时依赖
│
├── BillNote_extension/                     # Vue 3 浏览器插件
│   ├── package.json
│   ├── src/
│   │   ├── sidepanel/                      # 侧边栏
│   │   ├── popup/                          # 弹窗
│   │   ├── options/                        # 选项页
│   │   └── logic/
│   │       ├── cookies.ts                  # Cookie 同步
│   │       └── bilibili-subtitle.ts        # B站字幕抓取
│   └── manifest.json                       # 浏览器插件清单
│
└── PROJECT_CHANGES.md                      # 本文档
```

---

## 七、环境变量配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DIGEST_OUTPUT_DIR` | `digest_results` | 每日摘要文件保存目录 |
| `MONITOR_CRON` | `0 22 * * *` | 收藏监控定时任务 Cron 表达式 |
| `BACKEND_PORT` | `8483` | 后端服务端口 |
| `APP_PORT` | `3015` | 前端/对外端口 |
| `TRANSCRIBER_TYPE` | `fast-whisper` | 转写器类型 |
| `WHISPER_MODEL_SIZE` | `tiny` | Whisper 模型大小 |

---

## 八、部署方式

### 8.1 Docker 部署（NAS / 服务器）

```bash
git clone https://github.com/JefferyHcool/BiliNote.git
cd BiliNote
# 编辑 .env 配置
docker-compose up -d --build
```

### 8.2 桌面客户端（Windows / macOS）

```bash
cd BillNote_frontend
pnpm install
pnpm tauri build
# 产出: src-tauri/target/release/bundle/nsis/BiliNote_x.x.x_x64-setup.exe
```

### 8.3 本地开发

```bash
# 后端
cd backend && pip install -r requirements.txt && python main.py

# 前端
cd BillNote_frontend && pnpm install && pnpm dev
```

---

## 九、用户使用流程

```
1. 部署/安装 BiliNote
2. 设置 → AI 模型设置 → 添加 LLM 供应商（DeepSeek/OpenAI/Qwen）
3. 设置 → 下载配置 → 配置对应平台 Cookie
4. 设置 → 收藏监控 → 添加监控源 → 启动调度器
5. 设置 → 通知设置 → 添加飞书/企业微信/钉钉 Webhook
6. 系统自动运行：定时检查收藏 → 生成笔记 → 生成摘要 → 推送通知
7. 设置 → 每日汇总 → 查看/导出 Markdown 文件
```
