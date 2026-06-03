import argparse
import json
import sys
from pathlib import Path

try:
    from .compose_images_v1 import compose_images, resolve_product_image_path
    from .image_provider_factory import get_image_provider
except ImportError:
    from compose_images_v1 import compose_images, resolve_product_image_path
    from image_provider_factory import get_image_provider


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "project_config.json"
DEFAULT_PLAN_PATH = PROJECT_ROOT / "plans" / "NB001_product_plan.json"


def load_json(path):
    path = Path(path)
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as exc:
        raise RuntimeError(f"File not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON file: {path}") from exc


def ensure_dir(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_project_path(path):
    path = Path(path)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def build_asset_output_path(assets_dir, image_spec):
    index = int(image_spec.get("index", 0))
    if index <= 0:
        index = 1
    image_type = image_spec.get("type") or "image"
    return assets_dir / f"asset_{index:02d}_{image_type}.png"


def to_project_relative(path):
    path = Path(path)
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def run_asset_generation(plan_data, config_data, assets_dir):
    try:
        provider = get_image_provider(CONFIG_PATH)
    except Exception as exc:
        raise RuntimeError(f"Provider initialization failed: {exc}") from exc

    provider_name = config_data.get("image_provider", "openai")
    print(f"provider: {provider_name}")
    print(f"assets_dir: {assets_dir}")

    asset_paths = []
    for image_spec in plan_data.get("images", []):
        prompt = image_spec.get("comfy_prompt", "")
        output_path = build_asset_output_path(assets_dir, image_spec)
        try:
            provider.generate_image(
                prompt=prompt,
                output_path=output_path,
                reference_image=None,
            )
        except RuntimeError as exc:
            raise RuntimeError(f"Asset generation failed for {output_path.name}: {exc}") from exc

        asset_paths.append(output_path)
        print(f"asset_generated: {output_path}")

    if not asset_paths:
        raise RuntimeError("No images found in product plan.")

    return asset_paths


def write_manifest(plan_path, plan_data, output_folder, assets_dir, final_dir, final_paths, product_image_path):
    images = []
    final_by_name = {Path(path).name: Path(path) for path in final_paths}
    for image_spec in plan_data.get("images", []):
        filename = image_spec.get("filename", "")
        images.append(
            {
                "index": image_spec.get("index"),
                "filename": filename,
                "path": to_project_relative(final_by_name.get(filename, final_dir / filename)),
                "type": image_spec.get("type"),
            }
        )

    manifest = {
        "product_id": plan_data.get("product_id", ""),
        "plan": to_project_relative(plan_path),
        "input_image": to_project_relative(product_image_path) if product_image_path else "",
        "assets_folder": to_project_relative(assets_dir),
        "final_folder": to_project_relative(final_dir),
        "images": images,
    }

    manifest_path = output_folder / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, ensure_ascii=False, indent=2)
    print(f"manifest_generated: {manifest_path}")
    return manifest_path


def run_final_composition(plan_path, final_dir):
    print(f"final_dir: {final_dir}")
    output_folder, final_paths = compose_images(
        plan_path=plan_path,
        output_folder_override=final_dir,
    )
    for final_path in final_paths:
        print(f"final_generated: {final_path}")
    return output_folder, final_paths


def run_pipeline(plan_path=DEFAULT_PLAN_PATH):
    if not CONFIG_PATH.exists():
        raise RuntimeError(f"Config file not found: {CONFIG_PATH}")

    plan_path = resolve_project_path(plan_path)
    if not plan_path.exists():
        raise RuntimeError(f"Plan file not found: {plan_path}")

    config_data = load_json(CONFIG_PATH)
    plan_data = load_json(plan_path)
    product_id = plan_data.get("product_id", "UNKNOWN")
    output_folder = resolve_project_path(plan_data.get("output_folder", f"output/{product_id}"))
    assets_dir = ensure_dir(output_folder / "assets")
    final_dir = ensure_dir(output_folder / "final")

    print(f"plan_path: {plan_path}")
    print(f"output_folder: {output_folder}")
    print(f"input_image: {plan_data.get('input_image', '')}")
    product_image_path, used_fallback = resolve_product_image_path(plan_data)

    asset_paths = run_asset_generation(plan_data, config_data, assets_dir)
    _, final_paths = run_final_composition(plan_path, final_dir)
    manifest_path = write_manifest(
        plan_path=plan_path,
        plan_data=plan_data,
        output_folder=output_folder,
        assets_dir=assets_dir,
        final_dir=final_dir,
        final_paths=final_paths,
        product_image_path=product_image_path,
    )

    print("")
    print("summary:")
    print(f"- provider: {config_data.get('image_provider', 'openai')}")
    print(f"- product_id: {product_id}")
    print(f"- assets_generated: {len(asset_paths)}")
    print(f"- final_generated: {len(final_paths)}")
    print(f"- output_folder: {output_folder}")
    print(f"- manifest: {manifest_path}")

    return {
        "provider": config_data.get("image_provider", "openai"),
        "product_id": product_id,
        "output_folder": output_folder,
        "input_image": product_image_path,
        "assets": asset_paths,
        "final": final_paths,
        "manifest": manifest_path,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Run provider asset generation and final ecommerce image composition."
    )
    parser.add_argument(
        "--plan",
        default=str(DEFAULT_PLAN_PATH),
        help="Path to product plan JSON. Defaults to plans/NB001_product_plan.json.",
    )
    args = parser.parse_args()

    try:
        run_pipeline(args.plan)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
