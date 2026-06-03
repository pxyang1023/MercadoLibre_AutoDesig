try:
    from .base_provider import ImageProvider
except ImportError:
    from providers.base_provider import ImageProvider


class ComfyUIProvider(ImageProvider):
    """Placeholder ComfyUI image provider."""

    provider_name = "comfyui"

    def generate_image(self, prompt, output_path, reference_image=None):
        return self._create_placeholder_image(self.provider_name, prompt, output_path)
