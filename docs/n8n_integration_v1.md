# n8n 对接说明 V1

## 1. 目标

本说明用于快速创建一个最小可用的 n8n 工作流，让 n8n 调用本地 HTTP 服务：

```text
POST http://127.0.0.1:8899/generate
```

调用成功后，本地服务会自动生成 NB001 的图片集、文案结果、最终图片、云端预览页面和 zip 包。

## 2. 前置条件

请先确认：

- 本地服务已启动：

```bash
python scripts/server_v1.py
```

- 浏览器访问健康检查接口返回 `ok`：

```text
http://127.0.0.1:8899/health
```

- 以下文件已存在：

```text
input/products/products_sample.csv
plans/NB001_product_plan.json
```

## 3. 最小工作流结构

n8n 最小工作流建议包含：

1. `Manual Trigger`
2. `Set` 或 `Edit Fields`
3. `HTTP Request`

可选后续节点：

- `Code`：整理返回字段。
- `IF`：判断 `status` 是否为 `success`。
- `Google Sheets`：回填 `preview_index`、`zip_file`、`final_folder` 等字段。

## 4. HTTP Request 节点配置

节点类型：

```text
HTTP Request
```

配置：

```text
Method: POST
URL: http://127.0.0.1:8899/generate
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

## 5. 成功返回字段

成功后接口会返回：

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

关键字段说明：

- `status`：是否成功。
- `product_id`：产品 ID。
- `output_folder`：产品输出根目录。
- `final_folder`：最终 7 张图片目录。
- `preview_folder`：静态预览页目录。
- `preview_index`：本地预览 HTML 文件路径。
- `zip_file`：云端预览压缩包路径。
- `images`：最终图片文件名列表。

## 6. 如何把 preview_index、zip_file 回填到表格

如果使用 Google Sheets，可以在 `HTTP Request` 后接一个 `Google Sheets` 节点。

建议回填字段：

```text
product_id
status
preview_index
zip_file
final_folder
preview_folder
```

n8n 表达式示例：

```text
{{$json.product_id}}
{{$json.status}}
{{$json.preview_index}}
{{$json.zip_file}}
{{$json.final_folder}}
{{$json.preview_folder}}
```

如果要把图片列表合并成一个字符串：

```text
{{$json.images.join(", ")}}
```

## 7. 后续如何改造成批量产品生成

后续批量化可以按以下方向扩展：

1. 从 Google Sheets 读取多行产品。
2. 每一行包含 `product_id`、`csv`、`plan` 等字段。
3. 用 `Split In Batches` 或 `Loop Over Items` 逐个调用 `/generate`。
4. 根据返回的 `status` 判断是否成功。
5. 将 `preview_index`、`zip_file` 和错误信息回填到对应行。

当前本地服务 V1 先支持 `NB001`，后续可以扩展为多产品动态 plan。

## 8. 常见报错排查

### 连接失败

现象：

```text
ECONNREFUSED
```

排查：

- 确认 `python scripts/server_v1.py` 已启动。
- 确认服务地址是 `http://127.0.0.1:8899`。
- 确认 n8n 和 Python 服务在同一台机器上。

### /health 不是 ok

排查：

- 重启 `server_v1.py`。
- 检查终端是否有端口占用或 Python 报错。

### /generate 返回 error

排查：

- 查看返回 JSON 的 `message` 字段。
- 确认 `input/products/products_sample.csv` 存在。
- 确认 `plans/NB001_product_plan.json` 存在且 JSON 可解析。
- 确认 Pillow 已安装，因为图片合成需要 Pillow。
- 确认 `input/images` 下有可用产品图。

### n8n 在 Docker 里访问不到 127.0.0.1

如果 n8n 在 Docker 容器里运行，`127.0.0.1` 指的是容器自己，不是 Windows 主机。

可以尝试：

```text
http://host.docker.internal:8899/generate
```

或把 n8n 改成本机桌面版 / 本机进程运行。
