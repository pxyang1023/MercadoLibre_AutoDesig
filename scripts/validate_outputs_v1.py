import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow is required. Please run: pip install pillow", file=sys.stderr)
    sys.exit(1)

try:
    from .compose_images_v1 import load_json, resolve_product_image_path
except ImportError:
    from compose_images_v1 import load_json, resolve_product_image_path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = PROJECT_ROOT / "plans" / "NB001_product_plan.json"
FINAL_DIR = PROJECT_ROOT / "output" / "NB001" / "final"
EXPECTED_SIZE = (1024, 1024)


def check_product_image(plan):
    print("product image check:")
    image_path, used_fallback = resolve_product_image_path(plan)
    if image_path is None:
        print("warning: no usable product image found; final images may contain placeholder product card")
        return False, True

    print(f"product image usable: {image_path}")
    if used_fallback:
        print("warning: product plan image was missing; fallback product image was used")
    return True, False


def check_final_images(plan):
    print("")
    print("final image check:")
    if not FINAL_DIR.exists():
        print(f"error: final directory not found: {FINAL_DIR}")
        return False

    ok = True
    expected_images = plan.get("images", [])
    for image_spec in expected_images:
        filename = image_spec.get("filename")
        path = FINAL_DIR / filename
        if not path.exists():
            print(f"error: missing final image: {path}")
            ok = False
            continue

        try:
            with Image.open(path) as image:
                size = image.size
        except OSError:
            print(f"error: cannot open final image: {path}")
            ok = False
            continue

        if size != EXPECTED_SIZE:
            print(f"error: wrong size for {path.name}: {size[0]}x{size[1]}")
            ok = False
        else:
            print(f"ok: {path.name} {size[0]}x{size[1]}")

    if len(expected_images) != 7:
        print(f"warning: plan contains {len(expected_images)} images, expected 7")
        ok = False

    return ok


def main():
    try:
        plan = load_json(PLAN_PATH)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    product_ok, placeholder_warning = check_product_image(plan)
    final_ok = check_final_images(plan)

    print("")
    print("summary:")
    print(f"- product_image_found: {product_ok}")
    print(f"- placeholder_warning: {placeholder_warning}")
    print(f"- final_images_ok: {final_ok}")

    if not product_ok or not final_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
