<div style="display: flex; justify-content: center; align-items: center; gap: 10px;">
    <p align="center">
  <img src="./doc/icon.svg" alt="BiliNote Banner" width="50" height="50"  />
</p>
<h1 align="center" > BiliNote v2.3.3</h1>
</div>

<p align="center"><i>AI 视频笔记生成工具 · 收藏监控 · 每日摘要 · 通知推送</i></p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue.svg" />
  <img src="https://img.shields.io/badge/frontend-react%2019-blue" />
  <img src="https://img.shields.io/badge/backend-fastapi-green" />
  <img src="https://img.shields.io/badge/GPT-openai%20%7C%20deepseek%20%7C%20qwen-ff69b4" />
  <img src="https://img.shields.io/badge/docker-supported-blue" />
  <img src="https://img.shields.io/badge/status-active-success" />
</p>

## ✨ 项目简介

BiliNote 是一个开源的 AI 视频笔记助手，支持通过哔哩哔哩、YouTube、抖音、快手等视频链接，自动提取内容并生成结构清晰、重点明确的 Markdown 格式笔记。支持插入截图、原片跳转、AI 问答、收藏监控、每日摘要、通知推送等功能。

## 🔧 功能特性

### 核心功能

- 支持多平台：Bilibili、YouTube、本地视频、抖音、快手
- 支持返回笔记格式选择
- 支持笔记风格选择
- 支持多模态视频理解
- 支持多版本记录保留
- 支持自行配置 GPT 大模型（OpenAI、DeepSeek、Qwen 等）
- 本地模型音频转写（支持 Fast-Whisper、MLX-Whisper、Groq、BCut）
- GPT 大模型总结视频内容
- 自动生成结构化 Markdown 笔记
- 可选插入截图（自动截取）
- 可选内容跳转链接（关联原视频）
- 任务记录与历史回看
- 基于 RAG 的笔记内容 AI 问答（支持 Function Calling）
- 笔记顶部视频封面 Banner 展示
- 工作区和生成历史面板支持折叠/展开

### 🆕 收藏视频监控

自动监控你在各平台的收藏夹，检测新增收藏视频并自动生成笔记：

- **多平台支持**：B站收藏夹、抖音收藏、快手收藏、YouTube 稍后观看
- **定时检查**：基于 APScheduler 的定时任务，支持 Cron 表达式自定义检查频率
- **手动触发**：随时可手动触发检查，无需等待定时任务
- **处理模式**：支持「轻量摘要」和「完整笔记」两种处理模式
- **去重检测**：自动识别已处理的视频，避免重复生成
- **调度器管理**：前端可视化启停调度器、查看运行状态

### 🆕 每日摘要

将每天收藏的视频笔记自动汇总成一份结构化文档：

- **AI 生成**：调用大模型对当天所有笔记进行智能总结
- **模板生成**：不依赖 AI，按预设模板拼接生成
- **Markdown 导出**：一键导出为 `.md` 文件，保存到本地
- **历史查看**：查看任意日期的摘要内容
- **自动触发**：每日定时自动生成，也可手动触发

### 🆕 通知推送

摘要生成后自动推送到你的即时通讯工具：

- **飞书**：Webhook 机器人 + 签名校验，富文本卡片消息
- **企业微信**：Webhook 群机器人，Markdown 消息
- **钉钉**：Webhook + 加签验证，Markdown 消息
- **自定义 Webhook**：POST JSON 到任意地址，可对接其他平台
- **多渠道配置**：同时配置多个通知渠道，支持启用/禁用
- **推送内容**：摘要标题、日期、视频数量、摘要正文

## 📦 桌面版下载

本项目提供了 Windows 和 macOS 桌面客户端，可在 [Releases](https://github.com/JefferyHcool/BiliNote/releases) 页面下载最新版本。

> Windows 用户请注意：一定要在没有中文路径的环境下运行。

## 📸 截图预览

![screenshot](./doc/image1.png)
![screenshot](./doc/image3.png)
![screenshot](./doc/image.png)
![screenshot](./doc/image4.png)
![screenshot](./doc/image5.png)

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

确保已安装 Docker，直接拉取预构建镜像运行：

```bash
docker pull ghcr.io/jefferyhcool/bilinote:latest

docker run -d -p 80:80 \
  -v bilinote-data:/app/backend/data \
  -v bilinote-config:/app/backend/config \
  -v bilinote-static:/app/backend/static \
  -v bilinote-models:/app/backend/models \
  --name bilinote \
  ghcr.io/jefferyhcool/bilinote:latest
```

上面四个卷分别持久化：`data`（SQLite 数据库 + 生成的笔记）、`config`（LLM 供应商配置 / Cookie / 转写设置）、`static`（笔记引用的视频截图）、`models`（Whisper 模型缓存，可选，避免每次重新下载）。这样 `docker pull` 升级新镜像、删旧容器重建后，配置和历史都不会丢。

> ⚠️ **不要**用 `-v 卷名:/app/backend` 挂整个后端目录——命名卷会用首次启动时的镜像内容固化，之后 `docker pull` 升级也会被旧代码盖住，导致「升级不生效」。只挂上面这些数据子目录即可。

访问：`http://localhost`

也可以使用 docker-compose 本地构建：

```bash
cp .env.example .env
docker-compose up --build -d

# GPU 加速部署（需要 NVIDIA GPU + NVIDIA Container Toolkit）
docker-compose -f docker-compose.gpu.yml up --build -d
```

#### Docker 部署常见问题（FAQ）

**0. 国内拉不到 docker.io（build 阶段报 `dial tcp ... i/o timeout`）**

- **方法 A：直接用预构建镜像**——`docker pull ghcr.io/jefferyhcool/bilinote:latest`
- **方法 B：配置 Docker daemon 镜像加速器**——编辑 `~/.docker/daemon.json`，加：
  ```json
  {
    "registry-mirrors": ["https://docker.m.daocloud.io"]
  }
  ```
- **方法 C：临时切换 base image 镜像源**——`BASE_REGISTRY=docker.m.daocloud.io docker-compose build`

**1. 容器一直 restart / unhealthy**

```bash
docker logs -f bilinote-backend
```
常见原因：转写器配置错误、Whisper 模型下载 OOM（改 `.env` 里 `WHISPER_MODEL_SIZE=tiny`）。

**2. 改了 `.env` 没生效**

- `VITE_*` 是构建时变量，改完需 `docker-compose build frontend && docker-compose up -d`
- 其他后端变量是运行时变量，改完 `docker-compose up -d` 即可

**3. 数据存在哪？删容器会丢吗？**

`docker-compose` 用的是 `./backend:/app` 绑挂，以下文件删容器不会丢：
- `./backend/bili_note.db` — SQLite 数据库
- `./backend/config/transcriber.json` — 转写器配置
- `./backend/static/screenshots/` — 视频截图
- `./backend/note_results/` — 生成的笔记
- `./backend/digest_results/` — 每日摘要

**4. 前端打开是空白页 / 报 502**

通常是 nginx 起来了但 backend 还没 healthy。`docker ps` 查看 backend 容器状态。

### 方式二：源码部署

#### 1. 克隆仓库

```bash
git clone https://github.com/JefferyHcool/BiliNote.git
cd BiliNote
mv .env.example .env
```

#### 2. 启动后端（FastAPI）

```bash
cd backend
pip install -r requirements.txt
python main.py
```

#### 3. 启动前端（Vite + React）

```bash
cd BillNote_frontend
pnpm install
pnpm dev
```

访问：`http://localhost:3015`

### 方式三：飞牛 NAS 部署

```bash
ssh admin@你的NAS_IP
mkdir -p /vol1/docker/bilinote
cd /vol1/docker/bilinote
git clone https://github.com/JefferyHcool/BiliNote.git .

# 编辑 .env 配置
cat > .env << 'EOF'
BACKEND_PORT=8483
FRONTEND_PORT=3015
BACKEND_HOST=0.0.0.0
APP_PORT=3015
ENV=production
STATIC=/static
OUT_DIR=./static/screenshots
NOTE_OUTPUT_DIR=note_results
IMAGE_BASE_URL=/static/screenshots
DATA_DIR=data
DIGEST_OUTPUT_DIR=digest_results
MONITOR_CRON=0 22 * * *
TRANSCRIBER_TYPE=fast-whisper
WHISPER_MODEL_SIZE=tiny
EOF

docker-compose up -d --build
```

如需将摘要文件保存到 NAS 共享文件夹，在 `docker-compose.yml` 中添加卷映射：

```yaml
volumes:
  - ./backend:/app
  - /vol1/共享文件夹/视频摘要:/app/digest_results
```

## ⚙️ 依赖说明

### 🎬 FFmpeg

本项目依赖 ffmpeg 用于音频处理与转码，源码部署时必须安装：

```bash
# Mac (brew)
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# Windows
# 请从官网下载安装：https://ffmpeg.org/download.html
```

> ⚠️ 若系统无法识别 ffmpeg，请将其加入系统环境变量 PATH
>
> Docker 部署已内置 FFmpeg，无需额外安装。

### 🚀 CUDA 加速（可选）

若你希望更快地执行音频转写任务，可使用具备 NVIDIA GPU 的机器，并启用 fast-whisper + CUDA 加速版本。

具体配置方法请参考：[fast-whisper 项目地址](http://github.com/SYSTRAN/faster-whisper#requirements)

## 📖 使用指南

### 基本使用（单视频笔记）

1. 启动应用后，在首页粘贴视频链接
2. 选择 AI 模型和笔记风格
3. 点击生成，等待笔记完成

### 收藏监控设置

1. **配置 Cookie**：设置 → 下载配置 → 填入对应平台的 Cookie
2. **添加监控源**：设置 → 收藏监控 → 添加监控源（选择平台、处理模式、检查频率）
3. **启动调度器**：点击「启动」按钮，系统按设定频率自动检查
4. **手动检查**：随时点击「立即检查」手动触发

### 每日摘要

1. 设置 → 每日汇总 → 查看自动生成的摘要
2. 点击卡片查看详情
3. 点击「导出」下载 Markdown 文件
4. 也可手动生成指定日期的摘要

### 通知推送

1. 设置 → 通知设置 → 添加通知渠道
2. **飞书**：群设置 → 群机器人 → 添加自定义机器人 → 复制 Webhook
3. **企业微信**：群设置 → 添加群机器人 → 复制 Webhook
4. **钉钉**：群设置 → 智能群助手 → 添加机器人 → 复制 Webhook + 加签
5. 保存后，每日摘要生成时自动推送

## 🧠 TODO

- [x] 支持抖音及快手等视频平台
- [x] 支持前端设置切换 AI 模型切换、语音转文字模型
- [x] AI 摘要风格自定义（学术风、口语风、重点提取等）
- [x] 加入更多模型支持
- [x] 加入更多音频转文本模型支持
- [x] 基于 RAG 的笔记内容 AI 问答
- [x] 收藏视频自动监控
- [x] 每日摘要自动生成
- [x] 通知推送（飞书/企业微信/钉钉）
- [ ] 笔记导出为 PDF / Word / Notion
- [ ] 支持更多平台收藏监控（小红书等）
- [ ] 微信个人号推送

## 🙏 致谢

- 本项目基于 [JefferyHcool/BiliNote](https://github.com/JefferyHcool/BiliNote) 开发，感谢原作者的贡献
- 本项目中的 `抖音下载功能` 部分代码参考引用自：[Evil0ctal/Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API)

## 📜 License

MIT License

---

💬 你的支持与反馈是我持续优化的动力！欢迎 PR、提 issue、Star ⭐️
