# export_cloud_preview_v1.py 使用说明

## 1. 脚本用途

`scripts/export_cloud_preview_v1.py` 用于把 `output/NB001/final` 里的 7 张电商图整理成一个可上传到云端预览的静态网页包。

它会生成：

- `index.html`
- `images/`
- `preview_manifest.json`
- `NB001_cloud_preview.zip`

## 2. 如何运行

在项目根目录运行：

```bash
python scripts/export_cloud_preview_v1.py
```

或指定产品 ID：

```bash
python scripts/export_cloud_preview_v1.py --product NB001
```

## 3. 输出文件在哪里

输出目录：

```text
output/NB001/cloud_preview
```

目录结构：

```text
output/NB001/cloud_preview/
  index.html
  preview_manifest.json
  NB001_cloud_preview.zip
  images/
    01_main_white.png
    02_selling_points.png
    03_flavor.png
    04_ingredients.png
    05_lifestyle.png
    06_capacity.png
    07_summary.png
```

## 4. 如何打开本地 index.html 预览

直接双击打开：

```text
output/NB001/cloud_preview/index.html
```

也可以在浏览器地址栏打开该本地文件。

## 5. 如何上传到云端

可以上传整个 `cloud_preview` 文件夹，也可以上传：

```text
output/NB001/cloud_preview/NB001_cloud_preview.zip
```

上传后需要确保云端保留相对路径：

```text
index.html
preview_manifest.json
images/...
```

## 6. 后续如何接入 n8n / 云盘 / Zeabur / Cloudflare Pages

后续可以让 n8n 在图片生成完成后调用该脚本，然后执行：

- 上传 `cloud_preview` 文件夹到云盘。
- 上传 zip 到对象存储或共享目录。
- 将 `cloud_preview` 推送到 Zeabur 静态站点。
- 将 `cloud_preview` 推送到 Cloudflare Pages。
- 把预览链接回写到表格或商品任务系统。

如果 `final` 目录不存在，请先运行：

```bash
python scripts/run_pipeline_v1.py --plan plans/NB001_product_plan.json
```
