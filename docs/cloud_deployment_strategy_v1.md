# MercadoLibre AutoDesign 云端部署方案 V1

本文档说明如何把本地图片自动化服务 `scripts/server_v1.py` 部署到 Zeabur、Railway、Vercel、Cloudflare Workers / Pages 等云端平台。

当前项目特点：

- Python 标准库 HTTP 服务，入口为 `scripts/server_v1.py`
- 图片合成依赖 Pillow
- 运行时会读写本地目录：`input/`、`plans/`、`output/`
- `/generate` 会执行完整链路并生成 PNG、HTML、JSON、ZIP

因此，最适合的部署方式是“容器 + 持久文件目录”。Zeabur 和 Railway 更适合当前项目。Cloudflare Workers / Vercel 更适合拆分后的轻量 API、代理层或静态预览页托管。

## 平台推荐度

| 平台 | 推荐度 | 适用场景 | 主要优点 | 主要限制 |
| --- | --- | --- | --- | --- |
| Zeabur | 5/5 | 当前项目完整部署 | Dockerfile 友好、GitHub 部署简单、适合长运行服务 | 文件持久化需要额外规划 Volume 或对象存储 |
| Railway | 4.5/5 | 当前项目完整部署 | Dockerfile / Python 部署成熟，日志和变量配置清晰 | 免费额度和文件持久化策略需关注 |
| Cloudflare Pages | 4/5 | 托管 `cloud_preview` 静态网页 | 全球 CDN、静态文件快、适合预览页 | 不适合直接跑 Pillow 生成链路 |
| Cloudflare Workers | 2.5/5 | API 网关、鉴权、代理、触发远端生成服务 | 边缘运行、绑定 KV/R2/AI 等资源 | 当前完整 Python/Pillow/本地文件流水线不适合直接跑在 Worker |
| Vercel | 2.5/5 | 轻量 API 或前端预览 | GitHub 集成好、Serverless 简单 | 不适合长任务和持久写 `output/` |

## 推荐架构

### 最小云端可运行架构

```text
GitHub Repo -> Zeabur/Railway Docker Service -> server_v1.py
                                     |
                                     -> output/NB001/final
                                     -> output/NB001/cloud_preview
```

### 更稳的生产架构

```text
n8n / Frontend
  |
  v
Cloudflare Worker API Gateway
  |
  v
Zeabur/Railway Python Generator Service
  |
  v
R2 / S3 / Cloudflare Pages / Google Drive
```

## 通用云端改造点

云端服务通常会提供动态端口，所以建议让 `server_v1.py` 读取环境变量：

```python
PORT = int(os.environ.get("PORT", "8899"))
HOST = os.environ.get("HOST", "0.0.0.0")
```

本项目当前仍监听 `127.0.0.1:8899`，本地开发没问题。真正部署到 Zeabur/Railway 时，需要改成 `0.0.0.0` 并读取平台端口。

建议后续环境变量：

```text
HOST=0.0.0.0
PORT=8899
APP_ENV=production
API_TOKEN=your-secret-token
DEFAULT_PRODUCT_ID=NB001
```

安全建议：

- `/generate` 后续应增加 `Authorization: Bearer <API_TOKEN>`。
- 不要把 OpenAI / Gemini / 云盘密钥写入代码。
- 云端变量放到平台 Environment Variables。
- 生成结果建议上传到对象存储，而不是长期依赖容器本地磁盘。

## Zeabur 部署步骤

Zeabur 官方支持从 GitHub/Git 集成部署，也支持使用 Dockerfile。项目根目录有 Dockerfile 时，Zeabur 会自动用 Dockerfile 构建。

### 1. 注册 / 登录

1. 打开 Zeabur 官网。
2. 使用 GitHub 登录或注册。
3. 授权 Zeabur 访问你的 GitHub 仓库。

### 2. 准备 GitHub 仓库

把项目提交到 GitHub：

```bash
git init
git add .
git commit -m "Initial MercadoLibre AutoDesign cloud deployment"
git branch -M main
git remote add origin https://github.com/YOUR_NAME/MercadoLibre_AutoDesign.git
git push -u origin main
```

如果你不想把输出图片提交到 GitHub，请在 `.gitignore` 排除：

```text
output/
__pycache__/
*.pyc
```

### 3. 添加 Dockerfile

可以把模板复制到项目根目录：

```bash
copy deploy_templates\zeabur\Dockerfile Dockerfile
copy deploy_templates\zeabur\requirements.txt requirements.txt
```

### 4. Zeabur 创建服务

1. Zeabur Dashboard -> New Project
2. Add Service -> GitHub
3. 选择你的仓库
4. Framework / Runtime 选择 Dockerfile 或让 Zeabur 自动检测
5. Root Directory 填：

```text
/
```

如果 Dockerfile 不在根目录，可配置：

```text
ZBPACK_DOCKERFILE_PATH=deploy_templates/zeabur/Dockerfile
```

但更推荐把 Dockerfile 放根目录。

### 5. Zeabur 配置面板示例

Service Name:

```text
mercadolibre-autodesign
```

Environment Variables:

```text
HOST=0.0.0.0
PORT=8899
APP_ENV=production
API_TOKEN=replace-with-a-long-random-token
```

Port:

```text
8899
```

Start Command:

```bash
python scripts/server_v1.py
```

如果使用 Dockerfile，Start Command 通常由 Dockerfile 的 `CMD` 决定。

### 6. Zeabur 测试

部署完成后会得到类似链接：

```text
https://mercadolibre-autodesign.zeabur.app
```

测试健康检查：

```bash
curl https://mercadolibre-autodesign.zeabur.app/health
```

测试生成：

```bash
curl -X POST https://mercadolibre-autodesign.zeabur.app/generate ^
  -H "Content-Type: application/json" ^
  -d "{\"product_id\":\"NB001\",\"csv\":\"input/products/products_sample.csv\",\"plan\":\"plans/NB001_product_plan.json\"}"
```

Linux/macOS:

```bash
curl -X POST https://mercadolibre-autodesign.zeabur.app/generate \
  -H "Content-Type: application/json" \
  -d '{"product_id":"NB001","csv":"input/products/products_sample.csv","plan":"plans/NB001_product_plan.json"}'
```

### 7. Zeabur 调试

- 查看 Service Logs。
- 如果端口访问失败，确认服务监听 `0.0.0.0`，不是 `127.0.0.1`。
- 如果 Pillow 报错，确认 `requirements.txt` 有 `pillow`。
- 如果生成文件丢失，确认容器是否重启，是否配置持久化 Volume。

## Railway 部署步骤

Railway 支持 CLI 部署，也能识别 Dockerfile 并构建服务。

### 1. 准备 Dockerfile

复制模板到项目根目录：

```bash
copy deploy_templates\railway\Dockerfile Dockerfile
copy deploy_templates\railway\requirements.txt requirements.txt
```

### 2. Railway 控制台部署

1. 打开 Railway。
2. New Project。
3. Deploy from GitHub repo。
4. 选择仓库。
5. Railway 检测 Dockerfile 后构建部署。

### 3. Railway CLI 部署

```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

### 4. Railway 环境变量

```text
HOST=0.0.0.0
PORT=8899
APP_ENV=production
API_TOKEN=replace-with-a-long-random-token
```

Railway 可能会注入自己的 `PORT`，优先使用平台提供端口。

### 5. Railway 测试

```bash
curl https://your-service.up.railway.app/health
```

```bash
curl -X POST https://your-service.up.railway.app/generate \
  -H "Content-Type: application/json" \
  -d '{"product_id":"NB001","csv":"input/products/products_sample.csv","plan":"plans/NB001_product_plan.json"}'
```

## Cloudflare Workers 方案

Cloudflare Workers 适合做 API 网关，不推荐直接运行当前完整图片生成链路。

推荐用途：

- 校验 API Token。
- 接收 n8n / 前端请求。
- 转发到 Zeabur/Railway 后端。
- 将结果 URL 标准化返回。
- 后续绑定 KV、R2、D1 保存状态和文件信息。

### 1. Worker 打包方式

创建 Worker 项目：

```bash
npm create cloudflare@latest mercadolibre-worker
cd mercadolibre-worker
npm install
```

如果使用 Python Worker，可参考 Cloudflare Python Workers 和 pywrangler；但当前项目依赖 Pillow 和本地文件写入，不建议直接迁移。

### 2. wrangler.toml 示例

见：

```text
deploy_templates/cloudflare_workers/wrangler.toml
deploy_templates/cloudflare_workers/worker.js
```

### 3. 权限绑定说明

后续可以绑定：

```text
KV: 保存任务状态
R2: 保存图片和 zip
D1: 保存产品任务记录
Secrets: 保存 API_TOKEN / 后端服务 URL
```

设置 secret：

```bash
npx wrangler secret put API_TOKEN
npx wrangler secret put GENERATOR_BASE_URL
```

本地测试：

```bash
npx wrangler dev
```

部署：

```bash
npx wrangler deploy
```

## Cloudflare Pages 方案

Cloudflare Pages 适合托管 `output/NB001/cloud_preview` 静态网页。

步骤：

1. 先本地生成预览包：

```bash
python scripts/export_cloud_preview_v1.py --product NB001
```

2. 上传目录：

```text
output/NB001/cloud_preview
```

3. Pages 构建设置：

```text
Build command: 空
Build output directory: output/NB001/cloud_preview
```

此方案只能展示已有结果，不负责生成图片。

## Vercel 部署方案

Vercel 的 Python Runtime 适合单个 HTTP Handler 或轻量 Serverless Functions。当前完整流水线会写本地文件并可能运行较久，不推荐直接跑完整服务。

适合用途：

- 展示前端预览页。
- 提供一个轻量 API，转发请求到 Zeabur/Railway。
- 做结果查询接口。

模板见：

```text
deploy_templates/vercel/vercel.json
deploy_templates/vercel/api_generate.py
```

部署：

```bash
npm install -g vercel
vercel login
vercel
vercel --prod
```

环境变量：

```text
GENERATOR_BASE_URL=https://your-zeabur-service.zeabur.app
API_TOKEN=replace-with-a-long-random-token
```

## Windows 和 Linux 差异

### Windows

路径示例：

```text
D:\AI\MercadoLibre_AutoDesign
```

命令分行使用 `^`：

```bash
curl -X POST http://127.0.0.1:8899/generate ^
  -H "Content-Type: application/json" ^
  -d "{\"product_id\":\"NB001\"}"
```

复制文件：

```powershell
copy deploy_templates\zeabur\Dockerfile Dockerfile
```

### Linux

路径示例：

```text
/app
```

命令分行使用 `\`：

```bash
curl -X POST http://127.0.0.1:8899/generate \
  -H "Content-Type: application/json" \
  -d '{"product_id":"NB001"}'
```

复制文件：

```bash
cp deploy_templates/zeabur/Dockerfile Dockerfile
```

Docker / 云端容器一般是 Linux 环境，所以不要依赖 Windows 字体路径。当前脚本如果找不到 Windows Arial，会回退到 Pillow 默认字体。

## GitHub Actions 示例

模板：

```text
.github/workflows/deploy-cloud-preview-example.yml
```

用途：

- 作为未来自动部署静态预览页的参考。
- 当前完整图片生成仍建议在 Zeabur/Railway 后端执行。

## 最优方案选择

### 你现在应该选 Zeabur

原因：

- 当前项目是长运行 HTTP 服务。
- 需要 Pillow。
- 需要写 `output/`。
- Zeabur 用 Dockerfile 部署最直接。
- 后续接 n8n 的 URL 最简单。

### 如果你更重视日志和后端部署成熟度

选 Railway。

### 如果你只想分享预览页

选 Cloudflare Pages。

### 如果你想加一层全球 API 网关

选 Cloudflare Workers 转发到 Zeabur/Railway。

### 如果你想做前端管理台

Vercel 适合作为前端或轻量 API，不建议直接跑当前图片生成服务。

## 参考官方文档

- Zeabur Dockerfile 部署文档：https://zeabur.com/docs/en-US/deploy/methods/dockerfile
- Zeabur Deployment Methods：https://zeabur.com/docs/en-US/deploy/methods
- Cloudflare Python Workers：https://developers.cloudflare.com/workers/languages/python/
- Cloudflare Wrangler Configuration：https://developers.cloudflare.com/workers/wrangler/configuration/
- Railway CLI Deploying：https://docs.railway.com/cli/deploying
- Railway FastAPI Dockerfile Guide：https://docs.railway.com/guides/fastapi
- Vercel Python Runtime：https://vercel.com/docs/functions/runtimes
