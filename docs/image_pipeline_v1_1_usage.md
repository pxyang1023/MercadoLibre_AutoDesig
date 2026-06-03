# 图片链路 V1.1 使用说明

## 1. 图片链路现在怎么跑

V1.1 流程由 `scripts/run_pipeline_v1.py` 统一调度：

1. 读取 `config/project_config.json` 和 `plans/NB001_product_plan.json`。
2. 检查并解析产品图路径。
3. 调用当前 `image_provider`，根据每张图的 `comfy_prompt` 生成中间素材。
4. 将中间素材保存到 `output/NB001/assets`。
5. 调用 `compose_images_v1.py`，生成最终 7 张图片。
6. 将最终图片保存到 `output/NB001/final`。
7. 生成 `output/NB001/manifest.json`，记录本次输出结果。

## 2. 产品图应该放在哪里

产品图建议放在：

```text
input/images
```

推荐文件名：

- `input/images/nb_bottle.png`
- `input/images/nb_bottle.jpg`

当前脚本也兼容历史文件名：

- `input/images/inputimagesnb_bottle.jpg`

## 3. product_plan.json 的 input_image 怎么写

在 `plans/NB001_product_plan.json` 中配置：

```json
{
  "input_image": "input/images/nb_bottle.png"
}
```

也可以写成：

```json
{
  "input_image": "input/images/nb_bottle.jpg"
}
```

如果 plan 指定的图片不存在，但 `input/images` 下只有一个可用图片，脚本会自动使用该图片，并打印：

```text
using fallback product image: 路径
```

只有当 `input/images` 中没有任何可用图片时，才会使用灰色占位产品卡片。

## 4. assets 和 final 的区别

`assets` 是 provider 生成的中间素材目录：

```text
output/NB001/assets
```

`final` 是最终排版完成的电商详情图目录：

```text
output/NB001/final
```

V1.1 中，第 2 到第 7 张图会优先使用对应 asset 作为背景底图。例如：

```text
output/NB001/assets/asset_02_selling_points.png
```

如果 asset 不存在，脚本会回退到 Pillow 绘制的渐变背景。

## 5. 如何运行 pipeline

在项目根目录运行：

```bash
python scripts/run_pipeline_v1.py --plan plans/NB001_product_plan.json
```

运行成功后会输出：

- 当前 provider
- 产品图解析路径
- assets 输出路径
- final 输出路径
- manifest 路径

## 6. 如何运行 validate_outputs_v1.py

运行：

```bash
python scripts/validate_outputs_v1.py
```

验证脚本会检查：

- 产品图是否能找到
- `output/NB001/final` 是否存在 7 张图
- 每张 final 图片是否为 1024 x 1024
- 是否可能仍在使用灰色占位产品卡片

## 7. 如果出现灰色占位图，如何排查

请按顺序检查：

1. `plans/NB001_product_plan.json` 的 `input_image` 是否写对。
2. `input/images` 下是否真的有产品图。
3. 文件扩展名是否为 `.png`、`.jpg`、`.jpeg` 或 `.webp`。
4. 控制台是否出现 `product image found` 或 `using fallback product image`。
5. 如果出现 `available images in input/images: none`，说明产品图目录为空，需要先放入产品图。
