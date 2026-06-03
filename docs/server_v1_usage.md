# server_v1.py 使用说明

## 1. 服务用途

`scripts/server_v1.py` 是本地和 Zeabur 云端都可以运行的 HTTP 服务，用于触发美客多产品图片自动化链路。

服务会按产品执行：

1. 生成规则版文案：`copywriting_pipeline_v1.py`
2. 回写文案到 plan：`apply_copywriting_to_plan_v1.py`
3. 生成 assets 和 final 图片：`run_pipeline_v1.py`
4. 导出静态预览包：`export_cloud_preview_v1.py`

当前服务使用 Python 标准库 `http.server`，不需要额外 Web 框架。

## 2. 启动服务

在项目根目录运行：

```bash
python scripts/server_v1.py
```

本地默认监听：

```text
http://127.0.0.1:8899
```

Zeabur 云端使用环境变量：

```text
HOST=0.0.0.0
PORT=8080
```

## 3. 可用接口

```text
GET  /
GET  /health
GET  /generate-test
GET  /generate-batch-test
GET  /preview_manifest
POST /generate
POST /generate-batch
```

说明：
- `GET /`：浏览器测试面板。
- `GET /health`：健康检查。
- `GET /generate-test`：浏览器测试生成 NB001。
- `GET /generate-batch-test`：浏览器测试批量生成 NB001、NB002、NB003。
- `POST /generate`：正式单产品接口。
- `POST /generate-batch`：正式批量接口，适合 n8n 直接调用。

## 4. 浏览器测试方式

打开：

```text
http://127.0.0.1:8899/
```

页面里有三个常用按钮：
- `Health Check`
- `Generate NB001`
- `Generate Batch Test`

批量浏览器测试：

```text
http://127.0.0.1:8899/generate-batch-test
```

它会使用固定参数生成：

```text
NB001
NB002
NB003
```

## 5. 单产品接口

请求：

```text
POST http://127.0.0.1:8899/generate
Content-Type: application/json
```

Body：

```json
{
  "product_id": "NB001",
  "csv": "input/products/products_sample.csv",
  "plan": "plans/NB001_product_plan.json"
}
```

成功返回：

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

## 6. 批量接口

n8n 如果不能编辑 Code/Script 节点，可以直接用 HTTP Request 调用批量接口。

请求：

```text
POST http://127.0.0.1:8899/generate-batch
Content-Type: application/json
```

Body：

```json
{
  "items": [
    {
      "product_id": "NB001",
      "csv": "input/products/products_batch_sample.csv",
      "plan": "plans/NB001_product_plan.json"
    },
    {
      "product_id": "NB002",
      "csv": "input/products/products_batch_sample.csv",
      "plan": "plans/NB002_product_plan.json"
    },
    {
      "product_id": "NB003",
      "csv": "input/products/products_batch_sample.csv",
      "plan": "plans/NB003_product_plan.json"
    }
  ]
}
```

返回示例：

```json
{
  "status": "success",
  "total": 3,
  "success_count": 3,
  "failed_count": 0,
  "results": [
    {
      "product_id": "NB001",
      "status": "success",
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
  ]
}
```

如果某个产品失败，不会影响其他产品继续执行。顶层 `status` 可能是：
- `success`：全部成功。
- `partial_failed`：部分成功、部分失败。
- `error`：全部失败。

每个产品的具体结果在 `results` 数组里。

## 7. 输出目录

每个产品会生成独立目录：

```text
output/{product_id}/final
output/{product_id}/cloud_preview
```

例如：

```text
output/NB002/final
output/NB002/cloud_preview/index.html
output/NB002/cloud_preview/NB002_cloud_preview.zip
```

## 8. n8n 对接建议

最小工作流：

1. `Manual Trigger`
2. `HTTP Request`

HTTP Request 节点直接调用：

```text
POST http://127.0.0.1:8899/generate-batch
```

Body 选择 JSON，填入 `items` 数组即可。

后续可以把返回的 `results` 回填到 Google Sheets：
- `product_id`
- `status`
- `preview_index`
- `zip_file`
- `message`

## 9. 常见问题

### items 为空

接口会返回：

```json
{
  "status": "error",
  "message": "items must be a non-empty array."
}
```

### 某个产品失败

批量接口会继续执行后面的产品，并在该产品结果中返回：

```json
{
  "product_id": "NB002",
  "status": "error",
  "message": "错误说明"
}
```

### Zeabur 502

确认环境变量：

```text
HOST=0.0.0.0
PORT=8080
```

确认 Dockerfile：

```text
EXPOSE 8080
```
