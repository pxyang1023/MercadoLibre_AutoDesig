# Zeabur 云端部署指南 V1

本文档用于把本地 `scripts/server_v1.py` 服务部署到 Zeabur，让图片自动化链路可以在云端运行，并方便 n8n 调用。

当前版本先支持单产品：

```text
NB001
```

后续可扩展为批量产品。

## 1. 部署目标

部署完成后，你会得到一个 Zeabur 云端服务地址，例如：

```text
https://mercadolibre-autodesign.zeabur.app
```

可访问：

```text
GET  /health
POST /generate
```

n8n 调用：

```text
POST https://mercadolibre-autodesign.zeabur.app/generate
```

## 2. 本次新增文件

项目根目录：

```text
Dockerfile
.env.zeabur.example
```

文档和示例：

```text
docs/zeabur_deployment_v1.md
workflows/n8n_zeabur_generate_nb001_example.json
```

## 3. Dockerfile

项目根目录已生成：

```dockerfile
# 基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . .

# 安装依赖
RUN pip install --no-cache-dir pillow

# 设置环境变量
ENV HOST=0.0.0.0
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 8080

# 启动服务
CMD ["python", "scripts/server_v1.py"]
```

说明：

- `pillow` 用于图片合成。
- `HOST=0.0.0.0` 是云端容器必须项，否则外部无法访问服务。
- `PORT=8080` 与 Zeabur 当前公网 HTTP 端口匹配，避免 502。

## 4. Zeabur 前置准备

你需要：

1. 一个 GitHub 账号。
2. 一个 Zeabur 账号。
3. 本项目已经推送到 GitHub 仓库。

建议仓库名：

```text
MercadoLibre_AutoDesign
```

## 5. 推送到 GitHub

如果项目还没有 Git 仓库：

```bash
git init
git add .
git commit -m "Add Zeabur deployment template"
git branch -M main
git remote add origin https://github.com/YOUR_NAME/MercadoLibre_AutoDesign.git
git push -u origin main
```

如果已有 Git 仓库：

```bash
git add .
git commit -m "Add Zeabur deployment template"
git push
```

建议不要提交大量生成图片到 GitHub。后续可加 `.gitignore` 排除：

```text
output/
__pycache__/
*.pyc
```

如果你希望云端首次部署就带上 NB001 样例输出，可以暂时保留 `output/`。

## 6. Zeabur 注册 / 登录

1. 打开 Zeabur 官网。
2. 点击 Login / Sign up。
3. 使用 GitHub 登录。
4. 授权 Zeabur 访问你的 GitHub 仓库。

## 7. Zeabur 创建项目

1. 进入 Zeabur Dashboard。
2. 点击 `New Project`。
3. 选择一个区域，例如 Hong Kong / Singapore / US。
4. 点击 `Add Service`。
5. 选择 `GitHub`。
6. 选择仓库：

```text
MercadoLibre_AutoDesign
```

## 8. Zeabur 服务配置示例

Service Name：

```text
mercadolibre-autodesign
```

Root Directory：

```text
/
```

Build Method：

```text
Dockerfile
```

Dockerfile Path：

```text
Dockerfile
```

Start Command：

```text
由 Dockerfile CMD 控制
```

Port：

```text
8080
```

## 9. Zeabur 环境变量配置

在 Zeabur Service -> Environment Variables 中填写：

```text
HOST=0.0.0.0
PORT=8080
PYTHONUNBUFFERED=1
APP_ENV=production
API_TOKEN=replace-with-a-long-random-token
DEFAULT_PRODUCT_ID=NB001
DEFAULT_CSV=input/products/products_sample.csv
DEFAULT_PLAN=plans/NB001_product_plan.json
```

说明：

- `HOST=0.0.0.0`：云端必须。
- `PORT=8080`：Zeabur 云端服务监听端口。
- `PYTHONUNBUFFERED=1`：让日志实时输出。
- `API_TOKEN`：当前 V1 未强制校验，后续可用于接口鉴权。

## 10. Zeabur 部署完成后的访问链接

部署成功后，Zeabur 会给你一个域名，例如：

```text
https://mercadolibre-autodesign.zeabur.app
```

健康检查：

```text
https://mercadolibre-autodesign.zeabur.app/health
```

生成接口：

```text
https://mercadolibre-autodesign.zeabur.app/generate
```

## 11. 云端测试命令

### Windows PowerShell

```powershell
Invoke-RestMethod `
  -Uri https://mercadolibre-autodesign.zeabur.app/health `
  -Method GET
```

```powershell
Invoke-RestMethod `
  -Uri https://mercadolibre-autodesign.zeabur.app/generate `
  -Method POST `
  -ContentType "application/json" `
  -Body "{\"product_id\":\"NB001\",\"csv\":\"input/products/products_sample.csv\",\"plan\":\"plans/NB001_product_plan.json\"}"
```

### curl

```bash
curl https://mercadolibre-autodesign.zeabur.app/health
```

```bash
curl -X POST https://mercadolibre-autodesign.zeabur.app/generate \
  -H "Content-Type: application/json" \
  -d '{"product_id":"NB001","csv":"input/products/products_sample.csv","plan":"plans/NB001_product_plan.json"}'
```

成功返回示例：

```json
{
  "status": "success",
  "product_id": "NB001",
  "output_folder": "output/NB001",
  "final_folder": "output/NB001/final",
  "preview_folder": "output/NB001/cloud_preview",
  "preview_index": "output/NB001/cloud_preview/index.html",
  "zip_file": "output/NB001/cloud_preview/NB001_cloud_preview.zip",
  "images": [
    "01_main_white.png",
    "02_selling_points.png",
    "03_flavor.png",
    "04_ingredients.png",
    "05_lifestyle.png",
    "06_capacity.png",
    "07_summary.png"
  ]
}
```

## 12. n8n 调用 Zeabur 服务

n8n HTTP Request 节点配置：

```text
Method: POST
URL: https://mercadolibre-autodesign.zeabur.app/generate
Send Body: JSON
Content-Type: application/json
```

JSON Body：

```json
{
  "product_id": "NB001",
  "csv": "input/products/products_sample.csv",
  "plan": "plans/NB001_product_plan.json"
}
```

返回后可回填字段：

```text
{{$json.status}}
{{$json.product_id}}
{{$json.preview_index}}
{{$json.zip_file}}
{{$json.final_folder}}
{{$json.preview_folder}}
```

示例 workflow 文件：

```text
workflows/n8n_zeabur_generate_nb001_example.json
```

## 13. 常见问题

### 1. Zeabur 部署成功但访问失败

检查：

- `HOST` 是否为 `0.0.0.0`
- `PORT` 是否为 `8080`
- Dockerfile 是否有 `EXPOSE 8080`
- Zeabur 服务端口是否识别正确

### 2. Pillow 报错

检查 Dockerfile：

```dockerfile
RUN pip install --no-cache-dir pillow
```

### 3. /generate 返回 plan 或 csv 不存在

检查仓库中是否提交了：

```text
input/products/products_sample.csv
plans/NB001_product_plan.json
input/images/inputimagesnb_bottle.jpg
```

### 4. 生成结果重启后消失

容器本地文件通常不是长期存储方案。后续建议：

- 上传 `cloud_preview` 到 Cloudflare Pages / R2 / S3
- 或配置 Zeabur Volume
- 或让 n8n 生成后立即下载 zip 并存到云盘

## 13.1 502 Bad Gateway 排查重点

如果 Zeabur 公网访问显示 `502 Bad Gateway`，优先检查服务监听端口。

Zeabur 当前公网访问显示 HTTP `:8080`，因此 Dockerfile 和环境变量必须使用：

```text
HOST=0.0.0.0
PORT=8080
```

`server_v1.py` 必须监听 `0.0.0.0:8080`，不能只监听 `127.0.0.1`。如果只监听 `127.0.0.1`，容器内部服务虽然启动了，但 Zeabur 的公网路由访问不到。

部署后测试：

```text
https://你的域名/health
```

如果仍然 502，进入 Zeabur 日志查看启动输出是否出现：

```text
MercadoLibre AutoDesign Server V1 started at http://0.0.0.0:8080
```

如果日志里仍是 `127.0.0.1:8899`，说明 Zeabur 环境变量没有生效，或部署的不是最新镜像。请重新部署并确认 Environment Variables。

## 14. 后续扩展批量产品

当前 V1 只支持 NB001。

后续批量化方向：

1. CSV 中增加多个产品行。
2. 每个产品生成自己的 `plans/{product_id}_product_plan.json`。
3. 服务 `/generate` 支持动态 `product_id`。
4. 输出到：

```text
output/{product_id}/final
output/{product_id}/cloud_preview
```

5. n8n 使用 Split In Batches 循环调用 `/generate`。
