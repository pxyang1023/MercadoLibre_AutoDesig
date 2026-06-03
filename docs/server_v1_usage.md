# server_v1.py 使用说明

## 1. 服务用途

`scripts/server_v1.py` 是本地 HTTP 服务 V1，用于一键触发完整图片自动化链路。当前先支持单产品 `NB001`。

服务会依次执行：

1. `copywriting_pipeline_v1.py`
2. `apply_copywriting_to_plan_v1.py`
3. `run_pipeline_v1.py`
4. `export_cloud_preview_v1.py`

本版本使用 Python 标准库 `http.server`，不需要 Flask。

## 2. 如何启动

在项目根目录运行：

```bash
python scripts/server_v1.py
```

启动成功后会显示：

```text
MercadoLibre AutoDesign Server V1 started at http://127.0.0.1:8899
```

## 3. 如何测试 /health

### 浏览器方式

浏览器打开：

```text
http://127.0.0.1:8899/health
```

或使用 PowerShell：

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8899/health -Method GET
```

返回：

```json
{
  "status": "ok",
  "service": "MercadoLibre AutoDesign Server V1"
}
```

## 3.1 浏览器测试面板

现在可以直接用浏览器打开首页：

```text
http://127.0.0.1:8899/
```

首页包含：

- `Health Check`：跳转到 `/health`
- `Generate NB001`：跳转到 `/generate-test`
- `Preview Manifest`：如果已生成预览包，则跳转到 `/preview_manifest`

说明：

- `/generate` 是正式 POST 接口，给 n8n 和自动化流程使用。
- `/generate-test` 是浏览器测试接口，会用固定参数生成 NB001。
- 这样测试 Zeabur 服务时不需要 Postman，也不需要 curl。

## 4. 如何测试 /generate

PowerShell 示例：

```powershell
Invoke-RestMethod `
  -Uri http://127.0.0.1:8899/generate `
  -Method POST `
  -ContentType "application/json" `
  -Body "{\"product_id\":\"NB001\",\"csv\":\"input/products/products_sample.csv\",\"plan\":\"plans/NB001_product_plan.json\"}"
```

请求体：

```json
{
  "product_id": "NB001",
  "csv": "input/products/products_sample.csv",
  "plan": "plans/NB001_product_plan.json"
}
```

### 浏览器方式测试生成

打开：

```text
http://127.0.0.1:8899/generate-test
```

它会使用固定请求：

```json
{
  "product_id": "NB001",
  "csv": "input/products/products_sample.csv",
  "plan": "plans/NB001_product_plan.json"
}
```

成功后页面会显示：

- `status`
- `product_id`
- `final_folder`
- `preview_folder`
- `zip_file`
- `images`
- 原始 JSON 内容

Zeabur 云端测试时，把域名换成你的 Zeabur 域名即可：

```text
https://你的-zeabur-域名/
https://你的-zeabur-域名/generate-test
https://你的-zeabur-域名/preview_manifest
```

## 5. 本地生成结果在哪里

最终图片：

```text
output/NB001/final
```

云端预览包：

```text
output/NB001/cloud_preview
```

ZIP：

```text
output/NB001/cloud_preview/NB001_cloud_preview.zip
```

## 6. 如何打开本地 preview index.html

打开：

```text
output/NB001/cloud_preview/index.html
```

可以直接双击，也可以拖到浏览器中查看。

## 7. 后续如何接 n8n

n8n 可用 HTTP Request 节点调用：

1. `GET http://127.0.0.1:8899/health`
2. `POST http://127.0.0.1:8899/generate`

`/generate` 返回的 `preview_index`、`zip_file`、`final_folder` 和 `images` 字段可以回写到表格或商品任务系统。

## 8. 后续如何上传 cloud_preview 到 Cloudflare Workers / Pages

服务当前只负责本地生成，不上传云端。

后续可以让 n8n 在 `/generate` 成功后：

1. 读取 `output/NB001/cloud_preview`。
2. 上传整个目录到 Cloudflare Pages。
3. 或上传 `NB001_cloud_preview.zip` 到对象存储。
4. 将生成的云端 URL 回写到业务表格。
