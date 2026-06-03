# n8n 对接说明 V1

## 1. 目标

让 n8n 调用本地或 Zeabur 云端 HTTP 服务，自动生成美客多产品图片集。

因为当前 n8n 的 Code/Script 节点无法编辑，推荐直接调用批量接口：

```text
POST http://127.0.0.1:8899/generate-batch
```

n8n 只需要发送一个 JSON 数组，不需要写循环代码。

## 2. 前置条件

本地服务已启动：

```bash
python scripts/server_v1.py
```

健康检查返回 ok：

```text
http://127.0.0.1:8899/health
```

产品 CSV：

```text
data/products.csv
```

产品 plan：

```text
plans/NB001_product_plan.json
plans/NB002_product_plan.json
plans/NB003_product_plan.json
```

## 3. 最小工作流

不使用 Code 节点时，最小 n8n 工作流只需要：

1. `Manual Trigger`
2. `HTTP Request`

## 4. HTTP Request 节点配置

```text
Method: POST
URL: http://127.0.0.1:8899/generate-batch
Send Body: JSON
Content-Type: application/json
```

JSON Body：

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

## 5. 返回字段

批量接口返回：

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

顶层 `status`：

- `success`：全部产品成功。
- `partial_failed`：部分产品失败。
- `error`：全部产品失败。

## 6. 浏览器批量测试

不用 n8n 时，可以打开：

```text
http://127.0.0.1:8899/generate-batch-test
```

它会固定生成：

```text
NB001
NB002
NB003
```

## 7. 云端地址替换

本地地址：

```text
http://127.0.0.1:8899/generate-batch
```

Zeabur 地址示例：

```text
https://你的域名/generate-batch
```

## 8. 常见报错

### items 不是数组

`items` 必须是数组，且至少 1 项。

### 某个产品失败

批量接口不会中断整个任务，会在对应产品里返回：

```json
{
  "product_id": "NB002",
  "status": "error",
  "message": "错误说明"
}
```

### n8n Docker 无法访问 127.0.0.1

如果 n8n 跑在 Docker 容器里，`127.0.0.1` 指的是 n8n 容器自己。

可以尝试：

```text
http://host.docker.internal:8899/generate-batch
```

或者直接使用 Zeabur 公网地址。
