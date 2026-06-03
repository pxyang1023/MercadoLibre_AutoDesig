from abc import ABC, abstractmethod
from pathlib import Path


class ImageProvider(ABC):
    """Base class for interchangeable image generation providers."""

    def __init__(self, config=None):
        self.config = config or {}

    @abstractmethod
    def generate_image(self, prompt, output_path, reference_image=None):
        """Generate an image from a prompt and save it to output_path."""
        raise NotImplementedError

    def _create_placeholder_image(self, provider_name, prompt, output_path):
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError as exc:
            raise RuntimeError(
                "Pillow is required to create placeholder provider images. "
                "Install it with: pip install pillow"
            ) from exc

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        image = Image.new("RGB", (1024, 1024), "#F7FAFC")
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()

        prompt_preview = (prompt or "")[:80]
        lines = [
            "Image Provider Placeholder",
            f"Provider: {provider_name}",
            "",
            "Prompt preview:",
            prompt_preview,
        ]

        x = 72
        y = 420
        line_height = 28
        for line in lines:
            draw.text((x, y), line, fill="#1F2937", font=font)
            y += line_height

        draw.rectangle((48, 48, 976, 976), outline="#00A6B4", width=4)
        image.save(output)
        return str(output)
