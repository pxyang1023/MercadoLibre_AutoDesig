import argparse
import json
import shutil
import sys
import zipfile
from datetime import datetime
from html import escape
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_IMAGES = [
    "01_main_white.png",
    "02_selling_points.png",
    "03_flavor.png",
    "04_ingredients.png",
    "05_lifestyle.png",
    "06_capacity.png",
    "07_summary.png",
]


def load_json_if_exists(path):
    path = Path(path)
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def project_relative(path):
    path = Path(path)
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def validate_final_images(final_dir):
    if not final_dir.exists():
        raise RuntimeError(f"Final folder not found: {final_dir}. Please run scripts/run_pipeline_v1.py first.")

    missing = [filename for filename in EXPECTED_IMAGES if not (final_dir / filename).exists()]
    if missing:
        raise RuntimeError("Missing final images: " + ", ".join(missing))


def copy_images(final_dir, images_dir):
    images_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for filename in EXPECTED_IMAGES:
        source = final_dir / filename
        target = images_dir / filename
        shutil.copy2(source, target)
        copied.append(target)
    return copied


def copy_optional_json(output_dir, preview_dir, filename):
    source = output_dir / filename
    if not source.exists():
        print(f"warning: optional file not found, skipped: {source}")
        return None
    target = preview_dir / filename
    shutil.copy2(source, target)
    print(f"copied: {target}")
    return target


def get_image_specs(plan_data):
    if not plan_data:
        return {}
    return {
        image.get("filename"): {
            "index": image.get("index"),
            "type": image.get("type"),
        }
        for image in plan_data.get("images", [])
    }


def build_manifest(product_id, final_dir, preview_dir, plan_data, copywriting_exists):
    specs = get_image_specs(plan_data)
    product_name = (plan_data or {}).get("product_name", "")
    language = (plan_data or {}).get("language", "")
    market = (plan_data or {}).get("market", "")

    return {
        "product_id": product_id,
        "product_name": product_name,
        "language": language,
        "market": market,
        "source_folder": project_relative(final_dir),
        "preview_folder": project_relative(preview_dir),
        "zip_file": f"{product_id}_cloud_preview.zip",
        "copywriting_result": "copywriting_result.json" if copywriting_exists else "",
        "images": [
            {
                "index": specs.get(filename, {}).get("index", index),
                "type": specs.get(filename, {}).get("type", filename.removeprefix(f"{index:02d}_").removesuffix(".png")),
                "filename": filename,
                "relative_path": f"images/{filename}",
                "download_name": f"{product_id}_{filename}",
            }
            for index, filename in enumerate(EXPECTED_IMAGES, start=1)
        ],
    }


def write_manifest(preview_dir, manifest):
    manifest_path = preview_dir / "preview_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, ensure_ascii=False, indent=2)
        file.write("\n")
    return manifest_path


def build_product_meta(product_id, manifest, output_time):
    items = [
        ("product_id", product_id),
        ("product_name", manifest.get("product_name", "")),
        ("language", manifest.get("language", "")),
        ("market", manifest.get("market", "")),
        ("output_time", output_time),
        ("total_images", str(len(manifest.get("images", [])))),
    ]
    return "\n".join(
        f'<div class="meta-item"><span>{escape(label)}</span><strong>{escape(value or "-")}</strong></div>'
        for label, value in items
    )


def build_html(product_id, manifest, has_copywriting, has_manifest_json, output_time):
    cards = []
    for image in manifest["images"]:
        filename = escape(image["filename"])
        image_type = escape(image["type"])
        relative_path = escape(image["relative_path"])
        download_name = escape(image["download_name"])
        cards.append(
            f"""
      <article class="card">
        <div class="card-head">
          <div>
            <span class="index">#{image['index']:02d}</span>
            <span class="type">{image_type}</span>
          </div>
          <span class="filename">{filename}</span>
        </div>
        <img src="{relative_path}" alt="{filename}">
        <div class="actions">
          <a class="button" href="{relative_path}" download="{download_name}">下载图片</a>
          <button type="button" data-copy="{relative_path}">复制相对路径</button>
        </div>
      </article>"""
        )

    copywriting_link = '<a class="top-button" href="copywriting_result.json" target="_blank">打开 copywriting_result.json</a>' if has_copywriting else ""
    manifest_link = '<a class="top-button" href="manifest.json" target="_blank">打开 manifest.json</a>' if has_manifest_json else ""

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MercadoLibre 产品图片预览 - {escape(product_id)}</title>
  <style>
    :root {{
      --bg: #f3f6f8;
      --card: #ffffff;
      --ink: #0f172a;
      --muted: #64748b;
      --accent: #00a6b4;
      --accent-dark: #075985;
      --line: #e2e8f0;
      --warm: #ffd35a;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, "Microsoft YaHei", "PingFang SC", sans-serif;
      background: var(--bg);
      color: var(--ink);
    }}
    header {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 38px 22px 20px;
    }}
    h1 {{
      margin: 0 0 18px;
      font-size: clamp(28px, 4vw, 46px);
      line-height: 1.12;
      color: var(--accent-dark);
    }}
    .toolbar {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin: 18px 0 22px;
    }}
    .top-button, .button, button {{
      appearance: none;
      border: 0;
      border-radius: 10px;
      background: var(--accent);
      color: white;
      padding: 10px 14px;
      font-size: 14px;
      font-weight: 700;
      text-decoration: none;
      cursor: pointer;
    }}
    .top-button.secondary {{
      background: var(--accent-dark);
    }}
    .meta-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      padding: 16px;
      background: white;
      border: 1px solid var(--line);
      border-radius: 16px;
      box-shadow: 0 14px 34px rgba(15, 23, 42, 0.07);
    }}
    .meta-item {{
      min-width: 0;
      padding: 12px;
      border-radius: 12px;
      background: #f8fafc;
    }}
    .meta-item span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 6px;
    }}
    .meta-item strong {{
      display: block;
      font-size: 15px;
      overflow-wrap: anywhere;
    }}
    .grid {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 20px 22px 56px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
      gap: 26px;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: 0 18px 42px rgba(15, 23, 42, 0.09);
      overflow: hidden;
    }}
    .card-head {{
      min-height: 72px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      padding: 16px;
      border-bottom: 1px solid var(--line);
      background: linear-gradient(90deg, #ecfeff, #ffffff);
    }}
    .index {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 48px;
      height: 30px;
      border-radius: 999px;
      background: var(--accent);
      color: white;
      font-weight: 700;
      font-size: 14px;
      margin-right: 8px;
    }}
    .type {{
      color: var(--accent-dark);
      font-weight: 700;
      font-size: 15px;
    }}
    .filename {{
      color: var(--muted);
      font-size: 14px;
      text-align: right;
      overflow-wrap: anywhere;
    }}
    img {{
      display: block;
      width: 100%;
      height: auto;
      background: #fff;
    }}
    .actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      padding: 14px 16px 18px;
      border-top: 1px solid var(--line);
    }}
    .actions button {{
      background: var(--accent-dark);
    }}
    .toast {{
      position: fixed;
      left: 50%;
      bottom: 22px;
      transform: translateX(-50%);
      padding: 10px 14px;
      border-radius: 999px;
      background: #0f172a;
      color: white;
      opacity: 0;
      pointer-events: none;
      transition: opacity .2s ease;
    }}
    .toast.show {{
      opacity: 1;
    }}
    @media (max-width: 560px) {{
      header {{ padding: 26px 14px 14px; }}
      .grid {{ grid-template-columns: 1fr; padding: 14px; }}
      .card-head {{ align-items: flex-start; flex-direction: column; }}
      .filename {{ text-align: left; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>MercadoLibre 产品图片预览 - {escape(product_id)}</h1>
    <div class="toolbar">
      <a class="top-button secondary" href="{escape(manifest['zip_file'])}" download>下载全部 ZIP</a>
      {manifest_link}
      <a class="top-button" href="preview_manifest.json" target="_blank">打开 preview_manifest.json</a>
      {copywriting_link}
    </div>
    <section class="meta-grid">
      {build_product_meta(product_id, manifest, output_time)}
    </section>
  </header>
  <main class="grid">
{''.join(cards)}
  </main>
  <div id="toast" class="toast">已复制</div>
  <script>
    const toast = document.getElementById('toast');
    function showToast(text) {{
      toast.textContent = text;
      toast.classList.add('show');
      setTimeout(() => toast.classList.remove('show'), 1300);
    }}
    document.querySelectorAll('[data-copy]').forEach((button) => {{
      button.addEventListener('click', async () => {{
        const value = button.getAttribute('data-copy');
        try {{
          await navigator.clipboard.writeText(value);
          showToast('已复制: ' + value);
        }} catch (error) {{
          const textarea = document.createElement('textarea');
          textarea.value = value;
          document.body.appendChild(textarea);
          textarea.select();
          document.execCommand('copy');
          textarea.remove();
          showToast('已复制: ' + value);
        }}
      }});
    }});
  </script>
</body>
</html>
"""


def write_html(preview_dir, product_id, manifest, has_copywriting, has_manifest_json, output_time):
    html_path = preview_dir / "index.html"
    html_path.write_text(
        build_html(product_id, manifest, has_copywriting, has_manifest_json, output_time),
        encoding="utf-8",
    )
    return html_path


def write_zip(preview_dir, product_id, has_copywriting, has_manifest_json):
    zip_path = preview_dir / f"{product_id}_cloud_preview.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(preview_dir / "index.html", "index.html")
        archive.write(preview_dir / "preview_manifest.json", "preview_manifest.json")
        if has_manifest_json:
            archive.write(preview_dir / "manifest.json", "manifest.json")
        if has_copywriting:
            archive.write(preview_dir / "copywriting_result.json", "copywriting_result.json")
        for filename in EXPECTED_IMAGES:
            archive.write(preview_dir / "images" / filename, f"images/{filename}")
    return zip_path


def export_preview(product_id):
    output_dir = PROJECT_ROOT / "output" / product_id
    final_dir = output_dir / "final"
    preview_dir = output_dir / "cloud_preview"
    images_dir = preview_dir / "images"
    plan_path = PROJECT_ROOT / "plans" / f"{product_id}_product_plan.json"

    validate_final_images(final_dir)
    preview_dir.mkdir(parents=True, exist_ok=True)

    plan_data = load_json_if_exists(plan_path)
    if plan_data is None:
        print(f"warning: product plan not found, product metadata will be partial: {plan_path}")

    copied_images = copy_images(final_dir, images_dir)
    copied_copywriting = copy_optional_json(output_dir, preview_dir, "copywriting_result.json")
    copied_manifest = copy_optional_json(output_dir, preview_dir, "manifest.json")

    output_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    manifest = build_manifest(product_id, final_dir, preview_dir, plan_data, copied_copywriting is not None)
    manifest_path = write_manifest(preview_dir, manifest)
    html_path = write_html(
        preview_dir,
        product_id,
        manifest,
        has_copywriting=copied_copywriting is not None,
        has_manifest_json=copied_manifest is not None,
        output_time=output_time,
    )
    zip_path = write_zip(
        preview_dir,
        product_id,
        has_copywriting=copied_copywriting is not None,
        has_manifest_json=copied_manifest is not None,
    )

    print(f"cloud_preview_dir: {preview_dir}")
    print(f"index_html: {html_path}")
    print(f"images_dir: {images_dir}")
    for image in copied_images:
        print(f"image: {image}")
    print(f"preview_manifest: {manifest_path}")
    print(f"zip: {zip_path}")
    print("export cloud preview success")

    return {
        "preview_dir": preview_dir,
        "html_path": html_path,
        "images_dir": images_dir,
        "manifest_path": manifest_path,
        "zip_path": zip_path,
        "copied_copywriting": copied_copywriting,
        "copied_manifest": copied_manifest,
    }


def main():
    parser = argparse.ArgumentParser(description="Export a static cloud preview package for product images.")
    parser.add_argument("--product", default="NB001", help="Product ID. Defaults to NB001.")
    args = parser.parse_args()

    try:
        export_preview(args.product)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
