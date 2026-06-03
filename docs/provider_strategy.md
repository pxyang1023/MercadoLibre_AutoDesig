# 图像 Provider 抽象策略

## 为什么需要 Provider 抽象层

项目最初以 ComfyUI 作为主要图像生成引擎，但后续实际业务中可能会根据成本、速度、质量、可用性和部署环境切换不同模型。因此项目引入 `image_provider` 抽象层，把“生成图片”的统一入口和具体模型实现分开。

这样做有几个好处：

- 上层流程不用关心图片来自 OpenAI、Gemini 还是本地 ComfyUI。
- Python 合成脚本和 n8n 自动化流程只需要调用统一的 `generate_image(prompt, output_path, reference_image=None)` 方法。
- 后续切换模型时，优先修改配置，而不是改动整条业务流程。
- 可以先用占位实现跑通流程，再逐步接入真实 API。
- 可以保留 ComfyUI 本地生成能力，同时支持云端图像模型。

## 当前支持的 Provider

当前骨架支持三个 provider：

- `openai`：云端 API 模式，配置项使用 `OPENAI_API_KEY` 环境变量。
- `gemini`：云端 API 模式，配置项使用 `GEMINI_API_KEY` 环境变量。
- `comfyui`：本地模式，默认地址为 `http://127.0.0.1:8188`。

本阶段所有 provider 都是占位实现，不会调用真实 API。调用时会生成一张 1024 x 1024 的占位图，用于验证流程、输出路径和脚本调用是否正常。

## 如何切换 Provider

在 `config/project_config.json` 中修改：

```json
{
  "image_provider": "openai"
}
```

可选值包括：

- `openai`
- `gemini`
- `comfyui`

例如切换到 Gemini：

```json
{
  "image_provider": "gemini"
}
```

例如切换到本地 ComfyUI：

```json
{
  "image_provider": "comfyui"
}
```

## 后续接入真实 API 的方向

后续可以在对应文件中补充真实调用逻辑：

- `scripts/providers/openai_provider.py`：读取 `OPENAI_API_KEY`，调用 OpenAI 图像模型。
- `scripts/providers/gemini_provider.py`：读取 `GEMINI_API_KEY`，调用 Gemini 图像模型。
- `scripts/providers/comfyui_provider.py`：读取 `base_url`，调用本地 ComfyUI API。

无论底层实现如何变化，外部脚本都继续通过 `scripts/image_provider_factory.py` 获取 provider，并调用统一的 `generate_image` 方法。
