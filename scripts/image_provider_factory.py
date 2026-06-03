import json
from pathlib import Path

try:
    from .providers.comfyui_provider import ComfyUIProvider
    from .providers.gemini_provider import GeminiProvider
    from .providers.openai_provider import OpenAIProvider
except ImportError:
    from providers.comfyui_provider import ComfyUIProvider
    from providers.gemini_provider import GeminiProvider
    from providers.openai_provider import OpenAIProvider


PROVIDER_CLASSES = {
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "comfyui": ComfyUIProvider,
}


def load_project_config(config_path=None):
    if config_path is None:
        project_root = Path(__file__).resolve().parents[1]
        config_path = project_root / "config" / "project_config.json"

    with Path(config_path).open("r", encoding="utf-8") as file:
        return json.load(file)


def get_image_provider(config_path=None):
    config = load_project_config(config_path)
    provider_name = config.get("image_provider", "openai")
    providers_config = config.get("providers", {})

    provider_class = PROVIDER_CLASSES.get(provider_name)
    if provider_class is None:
        available = ", ".join(sorted(PROVIDER_CLASSES))
        raise ValueError(
            f"Unsupported image_provider '{provider_name}'. Available providers: {available}"
        )

    return provider_class(providers_config.get(provider_name, {}))
