# run_pipeline_v1.py 使用说明

## 1. 脚本用途

`scripts/run_pipeline_v1.py` 是项目的一键总控脚本，用于把 V1 流程串起来：

1. 读取 `config/project_config.json`。
2. 读取产品计划文件 `plans/NB001_product_plan.json`。
3. 通过 `scripts/image_provider_factory.py` 获取当前 `image_provider`。
4. 遍历 plan 中的 `images` 数组，用每一项的 `comfy_prompt` 生成中间素材。
5. 调用 `compose_images_v1.py` 的合成逻辑，输出最终 7 张电商详情图。

当前 provider 即使只是占位实现，也可以完整跑通流程，不会调用真实 API。

## 2. 如何运行

在项目根目录运行：

```bash
python scripts/run_pipeline_v1.py
```

也可以显式指定 plan：

```bash
python scripts/run_pipeline_v1.py --plan plans/NB001_product_plan.json
```

## 3. 输入文件在哪里

总控脚本读取以下文件：

- `config/project_config.json`
- `plans/NB001_product_plan.json`

产品图路径来自 plan 中的 `input_image` 字段，例如：

```text
input/images/nb_bottle.jpg
```

如果产品图不存在，最终合成阶段会沿用 `compose_images_v1.py` 的逻辑，生成灰色占位产品图并继续运行。

## 4. provider 如何切换

打开 `config/project_config.json`，修改：

```json
{
  "image_provider": "openai"
}
```

可选值：

- `openai`
- `gemini`
- `comfyui`

切换后重新运行总控脚本即可。上层流程不需要改代码。

## 5. assets 和 final 的区别

`assets` 是 provider 生成的中间素材目录，用于保存每张图对应的背景、场景或占位素材。

`final` 是最终电商详情图目录，用于保存已经完成排版、文案和产品图合成的 7 张 PNG。

## 6. 输出目录在哪里

输出根目录来自 plan 中的 `output_folder` 字段，当前默认是：

```text
output/NB001
```

中间素材输出到：

```text
output/NB001/assets
```

最终图片输出到：

```text
output/NB001/final
```

最终图片文件名保持：

- `01_main_white.png`
- `02_selling_points.png`
- `03_flavor.png`
- `04_ingredients.png`
- `05_lifestyle.png`
- `06_capacity.png`
- `07_summary.png`

## 7. 依赖说明

脚本只使用 Python 标准库和 Pillow。

如果提示缺少 Pillow，请手动运行：

```bash
pip install pillow
```

脚本不会自动安装依赖。

## 8. 后续如何接入 HTTP 服务和 n8n

后续可以增加一个本地 HTTP 服务，把 `run_pipeline_v1.py` 的逻辑包装成接口，例如：

- `POST /run-product`：传入 plan 路径或 product_id，触发生成流程。
- `GET /job-status`：查询生成进度。
- `GET /outputs`：返回 assets 和 final 图片路径。

n8n 可以通过 HTTP Request 节点调用这些接口，实现从表格、商品数据库或后台系统自动触发图片生成，并把输出路径回写到表格或业务系统。
