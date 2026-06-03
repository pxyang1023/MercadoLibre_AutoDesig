# Layout V1.2 Notes

## 目标

V1.2 优化 `compose_images_v1.py` 的最终详情图排版，让 `output/NB001/final` 中的 7 张图更接近电商详情页，而不是 provider 占位模板。

## 主要变化

- 第 2 到第 7 张图仍优先读取 `output/NB001/assets` 的中间素材，但会进行重度模糊和浅色遮罩处理，避免 provider 占位文字进入 final。
- 产品图统一放入白色展示卡片，增加轻微阴影。
- 标题最大字号限制为 48，并支持自动降到 36。
- bullet 文案支持最大宽度、最多 2 行和更稳定的间距。
- 第 2 张 selling points 采用左产品卡、右文案卡的详情页布局。

## 输出

最终图片仍输出到：

```text
output/NB001/final
```

每张图尺寸仍为：

```text
1024 x 1024
```
