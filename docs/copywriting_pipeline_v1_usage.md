# copywriting_pipeline_v1.py 使用说明

## 1. 脚本用途

`scripts/copywriting_pipeline_v1.py` 是美客多文案自动化链路 V1。它根据产品基础信息生成商品标题、五点描述、后台搜索词和质检结果。

V1 是规则和模板版本，不调用真实 API，也不联网搜索。

## 2. 输入 CSV 在哪里

默认输入文件：

```text
input/products/products_sample.csv
```

CSV 字段包括：

```text
product_id,product_name,category,language,market,selling_points,capacity,input_image,status
```

## 3. 输出 JSON 在哪里

每个产品会输出到：

```text
output/{product_id}/copywriting_result.json
```

例如：

```text
output/NB001/copywriting_result.json
```

## 4. 西语/葡语字符限制规则

- `language=es`：标题使用拉美西语风格，控制在 60 字符以内。
- `language=pt`：标题使用巴西葡语风格，控制在 50 字符以内。

脚本会生成 5 条五点描述，覆盖产品核心卖点、规格、使用场景、购买理由和适用场景。

后台关键词会生成 10 到 20 个，用英文逗号分隔。

质检会检查标题长度、标题是否为空、五点数量、关键词是否为空，以及是否有明显重复堆砌。

## 5. 如何运行

在项目根目录运行：

```bash
python scripts/copywriting_pipeline_v1.py
```

或指定 CSV：

```bash
python scripts/copywriting_pipeline_v1.py --csv input/products/products_sample.csv
```

## 6. 后续如何接入 OpenAI/Gemini/香蕉

后续可以把当前规则生成函数替换为文案模型 provider：

1. 读取 CSV 产品信息。
2. 构造 prompt，包含语言、市场、类目、卖点、容量和禁用词规则。
3. 调用 OpenAI、Gemini、香蕉等文案模型。
4. 保留当前质检逻辑作为输出校验层。
5. 如果模型输出不合格，可以自动重试或回退到模板版。

## 7. 后续如何和 product_plan / 图片链路合并

后续可以把 `copywriting_result.json` 合并进 `product_plan.json`：

- `new_title` 可用于商品标题或主图标题。
- `five_bullets` 可用于详情图卖点文案。
- `background_keywords` 可用于刊登后台搜索词。
- `qc_result` 和 `problem_note` 可用于 n8n 判断是否继续生成图片。

完整链路可以扩展为：

```text
products_sample.csv -> copywriting_result.json -> product_plan.json -> run_pipeline_v1.py -> final images
```
