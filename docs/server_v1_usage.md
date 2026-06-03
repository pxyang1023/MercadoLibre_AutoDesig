# server_v1.py 使用说明

## 1. 服务用途

`scripts/server_v1.py` 是本地和 Zeabur 云端都可以运行的 HTTP 服务，用于触发美客多产品图片自动化链路。

服务会按产品执行：

1. 生成规则版文案。
2. 回写文案到 product plan。
3. 生成 assets 和 final 图片。
4. 导出静态预览包和 ZIP。

当前服务使用 Python 标准库 `http.server`。

## 2. 启动服务

本地启动：

```bash
python scripts/server_v1.py
```

本地默认地址：

```text
http://127.0.0.1:8899
```

Zeabur 云端环境变量：

```text
HOST=0.0.0.0
PORT=8080
PYTHONUNBUFFERED=1
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

## 4. 浏览器测试

打开首页：

```text
http://127.0.0.1:8899/
```

首页包含：

- `Health Check`
- `Generate NB001`
- `Generate Batch Test`

批量测试入口：

```text
http://127.0.0.1:8899/generate-batch-test
```

## 5. 单产品接口

```text
POST http://127.0.0.1:8899/generate
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

## 6. 批量接口

n8n 不需要 Code 节点，只需要 HTTP Request 调用：

```text
POST http://127.0.0.1:8899/generate-batch
Content-Type: application/json
```

请求体：

```json
{
  "items": [
    {
      "product_id": "NB001",
      "csv": "data/products.csv",
      "plan": "plans/NB001_product_plan.json"
    },
    {
      "product_id": "NB002",
      "csv": "data/products.csv",
      "plan": "plans/NB002_product_plan.json"
    },
    {
      "product_id": "NB003",
      "csv": "data/products.csv",
      "plan": "plans/NB003_product_plan.json"
    }
  ]
}
```

返回结果会包含：

- `status`
- `total`
- `success_count`
- `failed_count`
- `results`

每个产品单独返回：

- `product_id`
- `status`
- `preview_index`
- `zip_file`
- `images`
- `message`，仅失败时出现

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

## 8. Zeabur 测试

部署后测试：

```text
https://你的域名/
https://你的域名/health
https://你的域名/generate-batch-test
```

如果 Zeabur 显示 502，确认：

```text
HOST=0.0.0.0
PORT=8080
```

Dockerfile 需要：

```text
EXPOSE 8080
```
