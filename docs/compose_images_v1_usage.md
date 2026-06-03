# compose_images_v1.py 使用说明

## 1. 脚本用途

`scripts/compose_images_v1.py` 是第一版 Python 图片合成脚本。它会读取 `plans/NB001_product_plan.json`，根据其中的 `images` 配置自动生成 7 张 1024 x 1024 电商详情图。

V1 不调用真实 AI 图像模型，只使用 Pillow 绘制渐变背景、圆角卡片、半透明色块、气泡装饰和文字排版。

## 2. 依赖 Pillow

脚本只依赖 Python 标准库和 Pillow。

如果运行时报错提示缺少 Pillow，请手动执行：

```bash
pip install pillow
```

脚本不会自动安装依赖。

## 3. 如何运行

在项目根目录 `D:\AI\MercadoLibre_AutoDesign` 下运行：

```bash
python scripts/compose_images_v1.py
```

也可以显式指定 plan 文件：

```bash
python scripts/compose_images_v1.py --plan plans/NB001_product_plan.json
```

## 4. 输入文件在哪里

脚本会读取：

- 项目配置：`config/project_config.json`
- 产品计划：`plans/NB001_product_plan.json`
- 产品图片：由 plan 里的 `input_image` 字段决定，当前默认是 `input/images/nb_bottle.jpg`

## 5. 输出文件在哪里

输出目录由 plan 里的 `output_folder` 字段决定，当前默认是：

```text
output/NB001
```

脚本会根据 `images` 数组中的 `filename` 输出 7 张图片：

- `01_main_white.png`
- `02_selling_points.png`
- `03_flavor.png`
- `04_ingredients.png`
- `05_lifestyle.png`
- `06_capacity.png`
- `07_summary.png`

运行时控制台会打印每张输出图片的路径。

## 6. 如果产品图缺失会发生什么

如果 `input_image` 指向的产品图不存在，脚本不会崩溃。

它会在控制台提示：

```text
missing product image
```

然后自动生成一个灰色占位产品卡片，并继续输出 7 张测试用详情图。

## 7. 下一步如何接入 image_provider 和 n8n

后续可以把 `scripts/image_provider_factory.py` 接入到合成流程中：

1. 先根据 `product_plan.json` 中的 `comfy_prompt` 调用当前 `image_provider`。
2. 生成每张详情图需要的背景图或素材图。
3. 再由 `compose_images_v1.py` 读取这些素材并合成最终图。
4. n8n 可以调用本地 HTTP 服务或命令行脚本，传入 plan 路径并触发整条生成流程。

这样可以让 OpenAI、Gemini 和 ComfyUI 作为可替换图像生成后端，而图片合成脚本保持稳定。
