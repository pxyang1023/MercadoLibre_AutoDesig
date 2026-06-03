try:
    from .base_provider import ImageProvider
except ImportError:
    from providers.base_provider import ImageProvider


class OpenAIProvider(ImageProvider):
    """Placeholder OpenAI image provider."""

    provider_name = "openai"

    def generate_image(self, prompt, output_path, reference_image=None):
        return self._create_placeholder_image(self.provider_name, prompt, output_path)
