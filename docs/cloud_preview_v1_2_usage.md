# 云端预览包 V1.2 使用说明

## 1. 预览页用途

云端预览包用于把某个产品的 7 张美客多图片整理成一个可分享的静态网页，方便朋友、团队或客户直接查看图片效果。

V1.2 页面包含产品信息、图片类型、文件名、下载按钮、复制图片相对路径按钮，以及 manifest / copywriting 文件入口。

## 2. 如何生成

在项目根目录运行：

```bash
python scripts/export_cloud_preview_v1.py --product NB001
```

默认产品也是 `NB001`，所以也可以运行：

```bash
python scripts/export_cloud_preview_v1.py
```

## 3. 如何本地打开 index.html

生成后打开：

```text
output/NB001/cloud_preview/index.html
```

可以直接双击，也可以拖到浏览器里查看。

## 4. 如何上传到 Cloudflare Workers / Pages

最简单方式是上传整个目录：

```text
output/NB001/cloud_preview
```

Cloudflare Pages 需要保持以下结构：

```text
index.html
preview_manifest.json
manifest.json
copywriting_result.json
images/
```

也可以上传 `NB001_cloud_preview.zip`，在云端解压后作为静态站点目录。

## 5. ZIP 里有哪些文件

标准 zip 结构：

```text
index.html
preview_manifest.json
manifest.json
copywriting_result.json
images/01_main_white.png
images/02_selling_points.png
images/03_flavor.png
images/04_ingredients.png
images/05_lifestyle.png
images/06_capacity.png
images/07_summary.png
```

如果 `manifest.json` 或 `copywriting_result.json` 不存在，脚本会跳过并打印 warning。

## 6. n8n 如何读取 preview_manifest.json

n8n 可以通过 HTTP Request 节点读取：

```text
preview_manifest.json
```

重点字段：

- `product_id`
- `product_name`
- `language`
- `market`
- `zip_file`
- `images[].relative_path`
- `images[].download_name`

后续可用这些字段生成云端图片 URL，并回写到表格或商品管理系统。

## 7. 如何为每个产品生成独立预览页

每个产品使用独立 product_id：

```bash
python scripts/export_cloud_preview_v1.py --product NB001
python scripts/export_cloud_preview_v1.py --product NB002
```

每个产品会生成自己的目录：

```text
output/NB001/cloud_preview
output/NB002/cloud_preview
```
