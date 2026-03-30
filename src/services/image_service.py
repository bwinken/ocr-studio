"""Image processing and text overlay service using Pillow."""

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.models import OverlayMode, TextBlock


class ImageService:
    def load_image(self, path: Path) -> Image.Image:
        img = Image.open(path)
        if img.mode != "RGB":
            img = img.convert("RGB")
        return img

    def image_to_bytes(self, img: Image.Image, fmt: str = "PNG") -> bytes:
        buf = io.BytesIO()
        img.save(buf, format=fmt)
        return buf.getvalue()

    def overlay_text_on_image(
        self,
        img: Image.Image,
        blocks: list[TextBlock],
        mode: OverlayMode,
        use_translated: bool = True,
    ) -> Image.Image:
        """Draw text at bbox positions on image."""
        result = img.copy()
        draw = ImageDraw.Draw(result)

        for block in blocks:
            text = block.translated_text if (use_translated and block.translated_text) else block.text
            if not text:
                continue

            bbox = block.bbox
            box_coords = [bbox.x0, bbox.y0, bbox.x1, bbox.y1]

            if mode in (OverlayMode.VISIBLE, OverlayMode.REPLACE):
                draw.rectangle(box_coords, fill="white")

            # Auto-fit font size based on bbox height
            font_size = max(8, int((bbox.y1 - bbox.y0) * 0.65))
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except (IOError, OSError):
                font = ImageFont.load_default()

            draw.text((bbox.x0 + 2, bbox.y0 + 1), text, fill="black", font=font)

        return result

    def save_with_overlay(
        self,
        image_path: Path,
        output_path: Path,
        blocks: list[TextBlock],
        mode: OverlayMode,
        use_translated: bool = True,
    ) -> Path:
        """Load image, overlay text, save to output_path."""
        img = self.load_image(image_path)
        result = self.overlay_text_on_image(img, blocks, mode, use_translated)
        result.save(str(output_path))
        img.close()
        result.close()
        return output_path
