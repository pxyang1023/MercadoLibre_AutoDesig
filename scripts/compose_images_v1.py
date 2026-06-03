import argparse
import json
import sys
import textwrap
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
except ImportError:
    print("Pillow is required. Please run: pip install pillow", file=sys.stderr)
    sys.exit(1)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN_PATH = PROJECT_ROOT / "plans" / "NB001_product_plan.json"
CONFIG_PATH = PROJECT_ROOT / "config" / "project_config.json"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
REGULAR_FONT_PATH = Path("C:/Windows/Fonts/arial.ttf")
BOLD_FONT_PATH = Path("C:/Windows/Fonts/arialbd.ttf")


def load_json(path):
    try:
        with Path(path).open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as exc:
        raise RuntimeError(f"JSON file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON file: {path}") from exc


def get_font(size, bold=False):
    font_path = BOLD_FONT_PATH if bold else REGULAR_FONT_PATH
    try:
        if font_path.exists():
            return ImageFont.truetype(str(font_path), size=size)
    except OSError:
        pass
    return ImageFont.load_default()


def load_fonts():
    return {
        "title": get_font(48, bold=True),
        "title_small": get_font(38, bold=True),
        "subtitle": get_font(32),
        "body": get_font(28),
        "small": get_font(24),
        "tiny": get_font(16),
        "hero": get_font(148, bold=True),
    }


def resize_image_keep_ratio(image, max_width=None, max_height=None):
    width, height = image.size
    ratios = []
    if max_width:
        ratios.append(max_width / width)
    if max_height:
        ratios.append(max_height / height)
    scale = min(ratios) if ratios else 1
    scale = min(scale, 1) if scale > 0 else 1
    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    return image.resize(new_size, Image.Resampling.LANCZOS)


def draw_gradient(draw, size, top_color, bottom_color):
    width, height = size
    top = tuple(int(top_color[i : i + 2], 16) for i in (1, 3, 5))
    bottom = tuple(int(bottom_color[i : i + 2], 16) for i in (1, 3, 5))
    for y in range(height):
        ratio = y / max(1, height - 1)
        color = tuple(int(top[i] * (1 - ratio) + bottom[i] * ratio) for i in range(3))
        draw.line([(0, y), (width, y)], fill=color)


def draw_rounded_card(draw, box, fill, radius=32, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def text_width(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def wrap_text_lines(draw, text, font, max_width, max_lines=None):
    words = str(text or "").split()
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if text_width(draw, candidate, font) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    if not lines and text:
        lines = textwrap.wrap(str(text), width=24) or [str(text)]

    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and text_width(draw, f"{last}...", font) > max_width:
            last = last[:-1].rstrip()
        lines[-1] = f"{last}..." if last else "..."

    return lines


def draw_wrapped_text(draw, text, xy, font, fill, max_width, line_spacing=10, max_lines=None):
    if not text:
        return xy[1]

    lines = wrap_text_lines(draw, text, font, max_width, max_lines=max_lines)
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        bbox = draw.textbbox((x, y), line, font=font)
        y += (bbox[3] - bbox[1]) + line_spacing
    return y


def fit_font_for_text(draw, text, max_width, max_lines, start_size=48, min_size=36, bold=True):
    for size in range(start_size, min_size - 1, -2):
        font = get_font(size, bold=bold)
        lines = wrap_text_lines(draw, text, font, max_width)
        if len(lines) <= max_lines and all(text_width(draw, line, font) <= max_width for line in lines):
            return font, size
    return get_font(min_size, bold=bold), min_size


def create_missing_product_placeholder(canvas_size, product_name):
    print("missing product image")
    card = Image.new("RGBA", (520, 760), (226, 232, 240, 255))
    draw = ImageDraw.Draw(card)
    draw.rounded_rectangle((0, 0, 519, 759), radius=44, fill=(226, 232, 240, 255), outline=(148, 163, 184, 255), width=4)
    draw.rectangle((110, 140, 410, 620), fill=(248, 250, 252, 255), outline=(148, 163, 184, 255), width=3)
    font = load_fonts()["body"]
    draw_wrapped_text(draw, product_name or "Product image", (76, 650), font, (71, 85, 105, 255), 380)
    return card


def list_input_images():
    images_dir = PROJECT_ROOT / "input" / "images"
    if not images_dir.exists():
        return []
    return sorted(
        path for path in images_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def resolve_product_image_path(plan):
    configured = plan.get("input_image", "input/images/nb_bottle.jpg")
    image_path = Path(configured)
    if not image_path.is_absolute():
        image_path = PROJECT_ROOT / image_path

    print(f"configured product image: {configured}")
    print(f"resolved product image path: {image_path}")

    if image_path.exists():
        print(f"product image found: {image_path}")
        return image_path, False

    available_images = list_input_images()
    print(f"product image missing: {image_path}")
    if available_images:
        print("available images in input/images:")
        for available in available_images:
            print(f"- {available}")
    else:
        print("available images in input/images: none")

    preferred_names = ["nb_bottle.png", "nb_bottle.jpg", "inputimagesnb_bottle.jpg"]
    for name in preferred_names:
        candidate = PROJECT_ROOT / "input" / "images" / name
        if candidate.exists():
            print(f"using fallback product image: {candidate}")
            return candidate, True

    if len(available_images) == 1:
        print(f"using fallback product image: {available_images[0]}")
        return available_images[0], True

    return None, False


def load_product_image(plan):
    image_path, used_fallback = resolve_product_image_path(plan)
    if image_path is None:
        return create_missing_product_placeholder((1024, 1024), plan.get("product_name", "Product")), None, True
    try:
        product = Image.open(image_path).convert("RGBA")
        return trim_product_whitespace(product), image_path, False
    except OSError as exc:
        print(f"product image cannot be opened: {image_path}", file=sys.stderr)
        if used_fallback:
            print("fallback product image failed; using placeholder", file=sys.stderr)
        return create_missing_product_placeholder((1024, 1024), plan.get("product_name", "Product")), image_path, True


def trim_product_whitespace(image, threshold=246, margin=28):
    rgb = image.convert("RGB")
    pixels = rgb.load()
    width, height = rgb.size
    left, top, right, bottom = width, height, 0, 0

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            if min(r, g, b) < threshold:
                left = min(left, x)
                top = min(top, y)
                right = max(right, x)
                bottom = max(bottom, y)

    if right <= left or bottom <= top:
        return image

    left = max(0, left - margin)
    top = max(0, top - margin)
    right = min(width, right + margin)
    bottom = min(height, bottom + margin)
    cropped = image.crop((left, top, right, bottom))
    print(f"product image trimmed: original={image.size[0]}x{image.size[1]} cropped={cropped.size[0]}x{cropped.size[1]}")
    return cropped


def paste_with_shadow(canvas, product, center, max_height, max_width=None):
    product = resize_image_keep_ratio(product, max_width=max_width, max_height=max_height)
    x = int(center[0] - product.width / 2)
    y = int(center[1] - product.height / 2)

    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        (x + 18, y + 24, x + product.width + 18, y + product.height + 24),
        radius=44,
        fill=(15, 23, 42, 52),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    canvas.alpha_composite(shadow)
    canvas.alpha_composite(product, (x, y))


def paste_product_card(canvas, product, center, max_height, max_width=None):
    product = resize_image_keep_ratio(product, max_width=max_width, max_height=max_height)
    x = int(center[0] - product.width / 2)
    y = int(center[1] - product.height / 2)
    padding = 26
    card_box = (
        x - padding,
        y - padding,
        x + product.width + padding,
        y + product.height + padding,
    )

    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        (card_box[0] + 16, card_box[1] + 20, card_box[2] + 16, card_box[3] + 20),
        radius=36,
        fill=(15, 23, 42, 45),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    canvas.alpha_composite(shadow)

    card_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card_layer)
    card_draw.rounded_rectangle(card_box, radius=36, fill=(255, 255, 255, 236))
    canvas.alpha_composite(card_layer)
    canvas.alpha_composite(product, (x, y))


def paste_product_in_box(canvas, product, box, max_height, max_width=None):
    left, top, right, bottom = box
    card_width = right - left
    card_height = bottom - top
    product = resize_image_keep_ratio(
        product,
        max_width=max_width or int(card_width * 0.86),
        max_height=max_height,
    )
    x = int(left + (card_width - product.width) / 2)
    y = int(top + (card_height - product.height) / 2)

    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        (left + 16, top + 20, right + 16, bottom + 20),
        radius=38,
        fill=(15, 23, 42, 50),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    canvas.alpha_composite(shadow)

    card_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card_layer)
    card_draw.rounded_rectangle(box, radius=38, fill=(255, 255, 255, 242), outline=(226, 232, 240, 170), width=2)
    canvas.alpha_composite(card_layer)
    canvas.alpha_composite(product, (x, y))


def find_asset_background(output_folder, image_spec):
    if output_folder is None:
        return None
    index = int(image_spec.get("index", 0))
    image_type = image_spec.get("type") or "image"
    if index <= 1:
        return None

    output_folder = Path(output_folder)
    if output_folder.name.lower() == "final":
        assets_dir = output_folder.parent / "assets"
    else:
        assets_dir = output_folder / "assets"
    asset_path = assets_dir / f"asset_{index:02d}_{image_type}.png"
    return asset_path if asset_path.exists() else None


def create_detail_canvas(image_spec, canvas_size, output_folder, top_color, bottom_color):
    asset_path = find_asset_background(output_folder, image_spec)
    if asset_path:
        try:
            background = Image.open(asset_path).convert("RGBA")
            background = background.resize(canvas_size, Image.Resampling.LANCZOS)
            # Provider V1 placeholders include text. Heavy blur + bright overlay keeps
            # the generated color mood but prevents prompt/provider words from showing.
            background = background.filter(ImageFilter.GaussianBlur(58))
            overlay = Image.new("RGBA", canvas_size, (232, 255, 255, 205))
            background.alpha_composite(overlay)
            print(f"using asset background: {asset_path}")
            return background, ImageDraw.Draw(background)
        except OSError:
            print(f"warning: cannot open asset background, using drawn gradient: {asset_path}")

    canvas = Image.new("RGBA", canvas_size)
    draw = ImageDraw.Draw(canvas)
    draw_gradient(draw, canvas_size, top_color, bottom_color)
    return canvas, draw


def draw_decorations(draw, size):
    width, height = size
    for box, color in [
        ((760, 80, 930, 250), (255, 255, 255, 82)),
        ((70, 720, 210, 860), (255, 211, 90, 115)),
        ((840, 720, 900, 780), (255, 255, 255, 125)),
        ((130, 130, 185, 185), (0, 166, 180, 80)),
    ]:
        draw.ellipse(box, fill=color)
    for x, y, r in [(720, 330, 12), (760, 378, 9), (802, 340, 7), (134, 620, 10)]:
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, 145))
    draw.arc((90, 300, 320, 430), 10, 170, fill=(255, 255, 255, 120), width=6)


def draw_soft_panel(draw, box, fill=(255, 255, 255, 226), radius=34):
    left, top, right, bottom = box
    draw.rounded_rectangle((left + 10, top + 12, right + 10, bottom + 12), radius=radius, fill=(15, 23, 42, 30))
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=(255, 255, 255, 175), width=2)


def draw_bullets(draw, bullets, start_xy, font, max_width, dot_fill="#FFD35A", text_fill="#0F172A", gap=20):
    x, y = start_xy
    for bullet in bullets:
        draw.rounded_rectangle((x, y + 7, x + 22, y + 29), radius=7, fill=dot_fill)
        next_y = draw_wrapped_text(
            draw,
            bullet,
            (x + 38, y),
            font,
            text_fill,
            max_width,
            line_spacing=8,
            max_lines=2,
        )
        y = next_y + gap
    return y


def draw_product_id(draw, canvas_size, product_id, fonts):
    text = product_id or ""
    if text:
        bbox = draw.textbbox((0, 0), text, font=fonts["tiny"])
        draw.text((canvas_size[0] - bbox[2] - 24, canvas_size[1] - 32), text, font=fonts["tiny"], fill="#CBD5E1")


def compose_main_white(plan, image_spec, product, canvas_size, fonts):
    canvas = Image.new("RGBA", canvas_size, "#FFFFFF")
    draw = ImageDraw.Draw(canvas)
    paste_with_shadow(canvas, product, (canvas_size[0] // 2, canvas_size[1] // 2), int(canvas_size[1] * 0.75), int(canvas_size[0] * 0.72))
    draw_product_id(draw, canvas_size, plan.get("product_id"), fonts)
    return canvas


def compose_selling_points(plan, image_spec, product, canvas_size, fonts, output_folder=None):
    canvas, draw = create_detail_canvas(image_spec, canvas_size, output_folder, "#D9FBFF", "#00A6B4")
    draw_decorations(draw, canvas_size)
    paste_product_in_box(canvas, product, (70, 250, 490, 770), 470, 370)
    draw_soft_panel(draw, (520, 160, 960, 865), (255, 255, 255, 232), radius=38)
    title_font, title_size = fit_font_for_text(draw, image_spec.get("title"), 380, 4, start_size=48, min_size=36, bold=True)
    y = draw_wrapped_text(draw, image_spec.get("title"), (540, 190), title_font, "#075985", 400, 10, max_lines=4)
    y = draw_wrapped_text(draw, image_spec.get("subtitle"), (540, y + 16), get_font(30), "#0F766E", 390, 12, max_lines=2)
    draw_bullets(draw, image_spec.get("bullets", []), (540, 610), get_font(28), 350, gap=22)
    print(f"layout debug: image 2 title_font={title_size} product_height_target=470")
    draw_product_id(draw, canvas_size, plan.get("product_id"), fonts)
    return canvas


def compose_flavor(plan, image_spec, product, canvas_size, fonts, output_folder=None):
    canvas, draw = create_detail_canvas(image_spec, canvas_size, output_folder, "#E0FBFF", "#7DD3FC")
    draw_decorations(draw, canvas_size)
    draw.ellipse((72, 88, 310, 326), fill=(255, 211, 90, 105))
    draw.ellipse((760, 710, 960, 910), fill=(0, 166, 180, 75))
    paste_product_in_box(canvas, product, (72, 360, 430, 855), 430, 310)
    draw_soft_panel(draw, (455, 205, 940, 805), (255, 255, 255, 232), radius=40)
    title_font, _ = fit_font_for_text(draw, image_spec.get("title"), 410, 2, start_size=48, min_size=38, bold=True)
    y = draw_wrapped_text(draw, image_spec.get("title"), (495, 250), title_font, "#075985", 405, 12, max_lines=2)
    y = draw_wrapped_text(draw, image_spec.get("subtitle"), (495, y + 10), get_font(30), "#0F766E", 405, 18, max_lines=2)
    draw_bullets(draw, image_spec.get("bullets", []), (495, y + 18), get_font(27), 365, dot_fill="#00A6B4", gap=20)
    draw_product_id(draw, canvas_size, plan.get("product_id"), fonts)
    return canvas


def compose_ingredients(plan, image_spec, product, canvas_size, fonts, output_folder=None):
    canvas, draw = create_detail_canvas(image_spec, canvas_size, output_folder, "#FFFFFF", "#D9FBFF")
    draw_decorations(draw, canvas_size)
    title_font, _ = fit_font_for_text(draw, image_spec.get("title"), 760, 2, start_size=48, min_size=38, bold=True)
    y = draw_wrapped_text(draw, image_spec.get("title"), (80, 70), title_font, "#075985", 760, 10, max_lines=2)
    draw_wrapped_text(draw, image_spec.get("subtitle"), (82, y + 8), get_font(30), "#0F766E", 760, max_lines=1)
    paste_product_in_box(canvas, product, (705, 320, 950, 815), 420, 210)
    card_y = 265
    colors = ["#BFF3F8", "#FFF1B8", "#D9F99D"]
    for idx, bullet in enumerate(image_spec.get("bullets", [])):
        top = card_y + idx * 175
        draw_soft_panel(draw, (80, top, 660, top + 138), (255, 255, 255, 235), radius=30)
        draw.ellipse((112, top + 35, 188, top + 111), fill=colors[idx % len(colors)])
        draw_wrapped_text(draw, bullet, (218, top + 38), get_font(28), "#0F172A", 390, 8, max_lines=2)
    draw_product_id(draw, canvas_size, plan.get("product_id"), fonts)
    return canvas


def compose_lifestyle(plan, image_spec, product, canvas_size, fonts, output_folder=None):
    canvas, draw = create_detail_canvas(image_spec, canvas_size, output_folder, "#E0F7FF", "#BAE6FD")
    draw.rectangle((0, 690, canvas_size[0], canvas_size[1]), fill=(255, 255, 255, 150))
    draw_decorations(draw, canvas_size)
    title_font, _ = fit_font_for_text(draw, image_spec.get("title"), 790, 2, start_size=48, min_size=38, bold=True)
    y = draw_wrapped_text(draw, image_spec.get("title"), (76, 78), title_font, "#075985", 790, 10, max_lines=2)
    draw_wrapped_text(draw, image_spec.get("subtitle"), (78, y + 8), get_font(30), "#0F766E", 680, 10, max_lines=2)
    paste_product_in_box(canvas, product, (610, 260, 930, 690), 390, 270)
    x = 72
    for bullet in image_spec.get("bullets", []):
        draw_soft_panel(draw, (x, 755, x + 276, 910), (255, 255, 255, 235), radius=28)
        draw.ellipse((x + 24, 785, x + 70, 831), fill="#FFD35A")
        draw_wrapped_text(draw, bullet, (x + 24, 848), get_font(23), "#0F172A", 225, 8, max_lines=2)
        x += 305
    draw_product_id(draw, canvas_size, plan.get("product_id"), fonts)
    return canvas


def compose_capacity(plan, image_spec, product, canvas_size, fonts, output_folder=None):
    canvas, draw = create_detail_canvas(image_spec, canvas_size, output_folder, "#E6FFFB", "#67E8F9")
    draw_decorations(draw, canvas_size)
    paste_product_in_box(canvas, product, (75, 270, 460, 825), 480, 330)
    draw.text((555, 170), plan.get("capacity", "1L"), font=fonts["hero"], fill="#075985")
    y = draw_wrapped_text(draw, image_spec.get("subtitle"), (570, 342), get_font(31), "#0F766E", 350, 18, max_lines=2)
    for bullet in image_spec.get("bullets", []):
        draw_soft_panel(draw, (555, y + 8, 930, y + 96), (255, 255, 255, 232), radius=24)
        draw_wrapped_text(draw, bullet, (585, y + 28), get_font(25), "#0F172A", 315, 8, max_lines=2)
        y += 112
    draw_product_id(draw, canvas_size, plan.get("product_id"), fonts)
    return canvas


def compose_summary(plan, image_spec, product, canvas_size, fonts, output_folder=None):
    canvas, draw = create_detail_canvas(image_spec, canvas_size, output_folder, "#F0FDFA", "#A5F3FC")
    draw_decorations(draw, canvas_size)
    title_font, _ = fit_font_for_text(draw, image_spec.get("title"), 820, 2, start_size=48, min_size=38, bold=True)
    y = draw_wrapped_text(draw, image_spec.get("title"), (100, 72), title_font, "#075985", 820, 10, max_lines=2)
    draw_wrapped_text(draw, image_spec.get("subtitle"), (120, y + 8), get_font(28), "#0F766E", 780, 8, max_lines=2)
    paste_product_in_box(canvas, product, (350, 300, 680, 710), 370, 275)
    x = 86
    for bullet in image_spec.get("bullets", []):
        draw_soft_panel(draw, (x, 750, x + 260, 930), (255, 255, 255, 235), radius=30)
        draw.ellipse((x + 96, 778, x + 164, 846), fill="#FFD35A")
        draw_wrapped_text(draw, bullet, (x + 24, 860), get_font(23), "#0F172A", 212, 8, max_lines=2)
        x += 300
    draw_product_id(draw, canvas_size, plan.get("product_id"), fonts)
    return canvas


COMPOSERS = {
    "main_white": compose_main_white,
    "selling_points": compose_selling_points,
    "flavor": compose_flavor,
    "ingredients": compose_ingredients,
    "lifestyle": compose_lifestyle,
    "capacity": compose_capacity,
    "summary": compose_summary,
}


def save_rgb(image, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(output_path, "PNG", optimize=True)


def compose_images(plan_path=DEFAULT_PLAN_PATH, output_folder_override=None):
    config = load_json(CONFIG_PATH)
    plan_path = Path(plan_path)
    if not plan_path.is_absolute():
        plan_path = PROJECT_ROOT / plan_path
    plan = load_json(plan_path)

    canvas_size = tuple(config.get("canvas_size", [1024, 1024]))
    if len(canvas_size) != 2:
        raise RuntimeError("config.canvas_size must contain width and height.")

    fonts = load_fonts()
    product, product_image_path, used_placeholder = load_product_image(plan)
    if output_folder_override is None:
        output_folder = PROJECT_ROOT / plan.get("output_folder", "output/NB001")
    else:
        output_folder = Path(output_folder_override)
        if not output_folder.is_absolute():
            output_folder = PROJECT_ROOT / output_folder
    outputs = []

    for image_spec in plan.get("images", []):
        image_type = image_spec.get("type")
        composer = COMPOSERS.get(image_type)
        if composer is None:
            raise RuntimeError(f"Unsupported image type: {image_type}")

        if image_type == "main_white":
            composed = composer(plan, image_spec, product, canvas_size, fonts)
        else:
            composed = composer(plan, image_spec, product, canvas_size, fonts, output_folder)
        output_path = output_folder / image_spec.get("filename", f"{image_type}.png")
        save_rgb(composed, output_path)
        outputs.append(output_path)
        print(
            "compose debug: "
            f"index={image_spec.get('index')} "
            f"type={image_type} "
            f"title={image_spec.get('title', '')!r} "
            f"bullets={len(image_spec.get('bullets', []))} "
            f"product_loaded={not used_placeholder} "
            f"output={output_path}"
        )

    if not outputs:
        raise RuntimeError("No images found in product plan.")

    return output_folder, outputs


def main():
    parser = argparse.ArgumentParser(description="Compose 1024x1024 ecommerce images from a product plan.")
    parser.add_argument("--plan", default=str(DEFAULT_PLAN_PATH), help="Path to product plan JSON.")
    args = parser.parse_args()

    try:
        compose_images(args.plan)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
