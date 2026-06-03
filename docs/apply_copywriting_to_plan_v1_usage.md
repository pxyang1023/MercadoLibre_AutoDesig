# apply_copywriting_to_plan_v1.py 使用说明

## 1. 脚本用途

`scripts/apply_copywriting_to_plan_v1.py` 用于把 `copywriting_result.json` 回写到 `product_plan.json`，让图片链路使用最新生成的标题、卖点和文案。

脚本会在修改 plan 前自动备份原文件。

## 2. 输入 copywriting_result.json 在哪里

默认读取：

```text
output/NB001/copywriting_result.json
```

也可以通过命令行指定：

```bash
python scripts/apply_copywriting_to_plan_v1.py --copy output/NB001/copywriting_result.json --plan plans/NB001_product_plan.json
```

## 3. 修改 product_plan.json 的哪些字段

脚本会新增或更新顶层字段：

```json
{
  "copywriting": {
    "new_title": "...",
    "five_bullets": [],
    "background_keywords": "...",
    "qc_result": "pass",
    "problem_note": "无问题"
  }
}
```

同时会更新 `images` 数组中第 2 到第 7 张图的标题、副标题和 bullets。第 1 张主白底图保持空标题、空副标题和空 bullets。

## 4. 如何运行

在项目根目录运行：

```bash
python scripts/apply_copywriting_to_plan_v1.py
```

或显式指定文件：

```bash
python scripts/apply_copywriting_to_plan_v1.py --copy output/NB001/copywriting_result.json --plan plans/NB001_product_plan.json
```

## 5. 如果 qc_result 不是 pass 会怎样

如果 `copywriting_result.json` 中的 `qc_result` 不是 `pass`，脚本会停止回写，并打印质检未通过的原因。

这种情况下不会修改 `product_plan.json`。

## 6. 回写后如何重新运行图片 pipeline

回写成功后，重新运行图片链路：

```bash
python scripts/run_pipeline_v1.py --plan plans/NB001_product_plan.json
```

最终图片会输出到：

```text
output/NB001/final
```
