# OpenAI 图片包 V2 使用说明

## 1. 目标

OpenAI 图片包 V2 用于生成美客多商品图片包，只做图片，不做视频，不接 Banana。

当前版本支持：

1. 云端上传原图
2. 云端图片识别与分析
3. 产品理解
4. 提示词优化
5. 人工提示词覆盖入口
6. 主图生成
7. 西语详情图生成
8. 葡语详情图生成
9. 对比预览 HTML
10. 上架数据包占位
11. 飞书通知工作流占位

## 2. 环境变量

必须配置：

```text
OPENAI_API_KEY=你的 OpenAI API Key
```

可选配置：

```text
OPENAI_TEXT_MODEL=gpt-4.1-mini
OPENAI_IMAGE_MODEL=gpt-image-1.5
```

Zeabur 中请在 Variables 面板加入 `OPENAI_API_KEY`。

## 3. 上传原图接口

```text
POST /upload_source_images
```

请求类型：

```text
multipart/form-data
```

字段：

- `product_id`：产品 ID
- `images`：图片文件字段名，支持 1-5 张

图片保存到：

```text
output/{product_id}/source_images/
```

同时生成：

```text
output/{product_id}/source_images/uploaded_images_manifest.json
```

返回示例：

```json
{
  "status": "success",
  "product_id": "PILLOW001",
  "uploaded_images": [
    "https://你的域名/files/output/PILLOW001/source_images/01_image.png"
  ],
  "uploaded_images_manifest": "https://你的域名/files/output/PILLOW001/source_images/uploaded_images_manifest.json"
}
```

## 4. 图片识别与分析接口

```text
POST /analyze_source_images
```

请求体：

```json
{
  "product_id": "PILLOW001",
  "title": "二次元角色抱枕",
  "keywords": "抱枕, 动漫抱枕, 靠枕",
  "source_images": [
    "图片URL1",
    "图片URL2"
  ]
}
```

输出文件：

```text
output/{product_id}/openai_pack_v2/visual_analysis.json
```

格式：

```json
{
  "visual_analysis": {
    "detected_product_type": "",
    "main_subject": "",
    "visual_style": "",
    "colors": [],
    "materials": [],
    "shape": "",
    "usage_scenarios": [],
    "important_visual_features": [],
    "do_not_change": [],
    "watermark_or_text_detected": true,
    "notes": ""
  }
}
```

## 5. OpenAI 图片包生成接口

### 异步提交接口，推荐 n8n 使用

```text
POST /submit_openai_image_pack_job
```

请求体与 `/generate_openai_image_pack` 一致。

接口会立即返回：

```json
{
  "status": "accepted",
  "job_id": "job_...",
  "status_url": "/job_status/job_...",
  "result_url": "/job_result/job_..."
}
```

任务文件保存到：

```text
output/jobs/{job_id}/job.json
output/jobs/{job_id}/status.json
output/jobs/{job_id}/result.json
```

状态查询：

```text
GET /job_status/{job_id}
```

状态值：

- `queued`
- `running`
- `succeeded`
- `failed`

`progress` 范围是 `0-100`。

`message` 会显示当前阶段：

- `analyzing`
- `prompt_generating`
- `main_image_generating`
- `detail_images_generating`
- `packaging`
- `done`

结果查询：

```text
GET /job_result/{job_id}
```

如果任务未完成，会返回：

```json
{
  "status": "running",
  "job_id": "job_...",
  "message": "任务未完成"
}
```

如果任务成功，会返回最终图片包结果。

### 同步测试接口，保留给本地调试

```text
POST /generate_openai_image_pack
```

请求体：

```json
{
  "product_id": "SKU001",
  "title": "产品标题",
  "keywords": "关键词",
  "target_country": "MX",
  "source_images": [
    "图片URL或本地路径"
  ],
  "detail_count_per_language": 6,
  "manual_override": {
    "enabled": false,
    "main_image_prompt": "",
    "detail_prompts_es": [],
    "detail_prompts_pt": [],
    "global_style_note": "",
    "negative_prompt": ""
  },
  "output_options": {
    "create_preview_html": true,
    "create_listing_package": true,
    "notify_feishu": false
  }
}
```

如果 `output/{product_id}/openai_pack_v2/visual_analysis.json` 已存在，生成接口会自动读取并结合到 prompt_pack 生成中。

## 6. 输出目录

所有输出保存到：

```text
output/{product_id}/openai_pack_v2/
```

主要文件：

```text
visual_analysis.json
product_analysis.json
main_image.png
detail_es_01.png
detail_pt_01.png
preview_manifest.json
preview.html
listing_ready.json
```

## 7. n8n 工作流

新增可导入文件：

```text
n8n_openai_cloud_upload_image_pack_v2.json
```

流程：

```text
手动触发 → 上传原图 → 图片识别与分析 → 提示词优化 → 人工修改提示词入口 → OpenAI图片包生成 → 整理结果 → 对比预览和上架预留 → 飞书通知
```

注意：

- 不使用 IF
- 不使用 Merge
- 不使用视频
- 不接 Banana
- 飞书 webhook 保留 `REPLACE_WITH_YOUR_WEBHOOK`

## 8. 多人使用说明

为支持多人同时使用，请确保每个任务使用不同的 `product_id`。

推荐命名：

```text
PILLOW001
PILLOW002
SKU_客户名_日期_序号
```

每个产品会独立写入：

```text
output/{product_id}/source_images/
output/{product_id}/openai_pack_v2/
```
