# 批量产品录入助手 V1 使用说明

## 1. 脚本用途

`scripts/batch_plan_generator_v1.py` 用于把批量产品 CSV 自动转换成多个 `product_plan.json`。

它的目标是减少人工填写 `plans/{product_id}_product_plan.json` 的工作量，为后续 n8n 批量生成图片做准备。

当前版本只做规则版生成：
- 不调用 GPT。
- 不调用绘画模型。
- 不覆盖已有 plan，除非显式使用 `--overwrite`。

## 2. CSV 文件位置

默认读取：

```text
input/products/products_batch_sample.csv
```

字段必须包括：

```text
product_id,product_name,category,language,market,selling_points,capacity,input_image,status
```

字段说明：
- `product_id`：产品编号，例如 `NB002`。
- `product_name`：产品名称。
- `category`：产品类目，例如 `beverage`、`tools`、`home`。
- `language`：语言，例如 `es`。
- `market`：市场，例如 `LatAm`。
- `selling_points`：卖点列表。
- `capacity`：规格或容量。
- `input_image`：产品图文件名或相对路径。
- `status`：只有 `pending` 的行会生成 plan。

## 3. selling_points 写法

`selling_points` 可以使用英文分号或中文分号分隔：

```text
Hoja de doble filo; Mango cómodo; Corte preciso para madera
```

或：

```text
Hoja de doble filo；Mango cómodo；Corte preciso para madera
```

脚本会自动拆成数组。

## 4. 如何运行

使用默认 CSV：

```bash
python scripts/batch_plan_generator_v1.py
```

指定 CSV：

```bash
python scripts/batch_plan_generator_v1.py --csv input/products/products_batch_sample.csv
```

生成结果位于：

```text
plans/{product_id}_product_plan.json
```

例如：

```text
plans/NB002_product_plan.json
plans/NB003_product_plan.json
```

## 5. 如何覆盖已有 plan

默认情况下，如果 plan 已存在，脚本会跳过并打印：

```text
already exists, skipped
```

如果确认要覆盖，运行：

```bash
python scripts/batch_plan_generator_v1.py --csv input/products/products_batch_sample.csv --overwrite
```

注意：覆盖会改写已有 `plans/{product_id}_product_plan.json`，使用前请确认不影响已调好的产品。

## 6. 自动填充规则

脚本会自动生成 7 张图的基础结构：

```text
01_main_white.png
02_selling_points.png
03_flavor.png
04_ingredients.png
05_lifestyle.png
06_capacity.png
07_summary.png
```

第 2-7 张会根据产品名称、类目、容量和卖点自动填入基础标题、字幕和 bullets。

类目标题规则：
- `beverage` → `Sabor fresco y práctico`
- `tools` → `Diseño práctico y preciso`
- `home` → `Solución práctica para el hogar`
- 其他 → `Características destacadas`

## 7. 校验规则

如果某行不合格，脚本不会生成 plan，并会打印原因。

校验项：
- `product_id` 不能为空。
- `product_name` 不能为空。
- `input_image` 不能为空。
- `selling_points` 至少 2 条。
- `images` 必须正好 7 项。

## 8. 如何配合 n8n 批量生成

后续 n8n 可以按以下流程扩展：

1. 从 Google Sheets 或 CSV 读取产品列表。
2. 调用本脚本生成多个 `product_plan.json`。
3. 对每个 `product_id` 调用本地或云端 `/generate` 接口。
4. 把 `preview_index`、`zip_file`、`final_folder` 回填到表格。

当前 V1 先在本地生成 plan，为后续批量 HTTP 触发做准备。

## 9. 后续接 GPT 自动生成 selling_points

未来可以增加文案模型步骤：

1. 从 CSV 读取产品基础信息。
2. 调用 OpenAI、Gemini 或其他文案模型生成标题和卖点。
3. 把生成结果写入 `copywriting_result.json`。
4. 回写到 `product_plan.json`。
5. 再进入图片自动化 pipeline。
