# Zeabur 云端部署指南 V1

本文档用于把当前项目部署到 Zeabur。当前云端只运行 Python 标准库实现的 `scripts/server_v1.py` 服务。

当前版本先支持单产品：

```text
NB001
```

## 1. 部署目标

部署完成后，你会得到一个 Zeabur 公网地址，例如：

```text
https://mercadolibre-autodesign.zeabur.app
```

部署后依次测试：

```text
https://你的域名/
https://你的域名/health
https://你的域名/generate-test
```

n8n 后续正式调用：

```text
POST https://你的域名/generate
```

## 2. 当前服务接口

```text
GET  /
GET  /health
GET  /generate-test
POST /generate
GET  /preview_manifest
```

说明：
- `GET /` 是浏览器测试首页。
- `GET /health` 用于健康检查。
- `GET /generate-test` 用浏览器直接触发 NB001 测试生成。
- `POST /generate` 是正式接口，供 n8n 调用。
- `GET /preview_manifest` 用于读取预览包 manifest。

## 3. Dockerfile

项目根目录的 `Dockerfile` 必须是：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir pillow

ENV HOST=0.0.0.0
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["python", "scripts/server_v1.py"]
```

注意：
- 只安装 `pillow`。
- 当前 `server_v1.py` 使用 Python 标准库 `http.server`。
- 不添加本地图像生成引擎配置。
- 不启动额外后台服务。

## 4. Zeabur 环境变量

Zeabur 环境变量只需要：

```text
HOST=0.0.0.0
PORT=8080
PYTHONUNBUFFERED=1
```

含义：
- `HOST=0.0.0.0`：让容器服务可以被 Zeabur 公网路由访问。
- `PORT=8080`：与 Zeabur 公网 HTTP 端口保持一致。
- `PYTHONUNBUFFERED=1`：让日志实时输出，方便排查。

本地运行时不设置环境变量，服务默认使用：

```text
127.0.0.1:8899
```

云端运行时使用：

```text
0.0.0.0:8080
```

## 5. Zeabur 面板配置

1. 登录或注册 Zeabur。
2. 创建新 Project。
3. 添加 Service，选择 GitHub 仓库。
4. 构建方式选择 Dockerfile。
5. Root Directory 保持项目根目录。
6. Network / Public Port 选择 HTTP `:8080`。
7. 在 Variables 中填写：

```text
HOST=0.0.0.0
PORT=8080
PYTHONUNBUFFERED=1
```

8. 点击 Deploy。

部署成功后，日志必须看到：

```text
MercadoLibre AutoDesign Server V1 started at http://0.0.0.0:8080
```

## 6. 浏览器测试

打开首页：

```text
https://你的域名/
```

页面会显示：
- Health Check 按钮，跳转到 `/health`
- Generate NB001 按钮，跳转到 `/generate-test`
- Preview Manifest 按钮，如果预览 manifest 已生成则可访问

健康检查：

```text
https://你的域名/health
```

应返回：

```json
{
  "status": "ok",
  "service": "MercadoLibre AutoDesign Server V1"
}
```

浏览器触发测试生成：

```text
https://你的域名/generate-test
```

成功后会生成：

```text
output/NB001/final
output/NB001/cloud_preview/index.html
output/NB001/cloud_preview/NB001_cloud_preview.zip
```

## 7. n8n 调用示例

HTTP Request 节点：

```text
Method: POST
URL: https://你的域名/generate
Send Body: JSON
Content-Type: application/json
```

请求体：

```json
{
  "product_id": "NB001",
  "csv": "input/products/products_sample.csv",
  "plan": "plans/NB001_product_plan.json"
}
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

## 8. 502 Bad Gateway 排查

如果 Zeabur 公网访问显示 502，优先检查端口和监听地址。

必须满足：

```text
HOST=0.0.0.0
PORT=8080
```

Dockerfile 必须包含：

```text
EXPOSE 8080
```

Zeabur Network / Public Port 使用 HTTP `:8080`。

日志必须出现：

```text
MercadoLibre AutoDesign Server V1 started at http://0.0.0.0:8080
```

如果日志显示 `127.0.0.1:8899`，说明云端环境变量没有生效。

如果日志显示 `0.0.0.0:8899`，说明 `PORT=8080` 没有设置或没有生效。

如果日志显示 `0.0.0.0:8080` 但仍然 502，检查：
- Zeabur 是否使用 Dockerfile 构建。
- Network 端口是否选择 HTTP `:8080`。
- 部署日志中是否有 Python 报错。
- `/health` 是否能返回 JSON。

## 9. 本地测试

本地默认运行：

```bash
python scripts/server_v1.py
```

预期日志：

```text
MercadoLibre AutoDesign Server V1 started at http://127.0.0.1:8899
```

模拟 Zeabur 环境：

```bat
set HOST=0.0.0.0
set PORT=8080
python scripts/server_v1.py
```

预期日志：

```text
MercadoLibre AutoDesign Server V1 started at http://0.0.0.0:8080
```
