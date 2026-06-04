from __future__ import annotations

import base64
import json
import mimetypes
import os
import re
import time
import urllib.error
import urllib.request
from html import escape
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini")
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1.5")
DEFAULT_DETAIL_COUNT = 6


def project_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def resolve_project_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else PROJECT_ROOT / path


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def require_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Set it in Zeabur environment variables.")
    return api_key


def openai_json_request(endpoint: str, payload: dict[str, Any], api_key: str, timeout: int = 180) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{OPENAI_API_BASE}{endpoint}",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenAI API network error: {exc}") from exc


def local_image_to_data_url(path: Path) -> str:
    mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
    return f"data:{mime_type};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def normalize_source_image(image: str) -> str:
    if image.startswith(("http://", "https://", "data:image/")):
        return image
    path = resolve_project_path(image)
    return local_image_to_data_url(path) if path.exists() else image


def extract_text_from_responses(response: dict[str, Any]) -> str:
    if isinstance(response.get("output_text"), str):
        return response["output_text"]
    chunks: list[str] = []
    for output in response.get("output", []) or []:
        for content in output.get("content", []) or []:
            if isinstance(content.get("text"), str):
                chunks.append(content["text"])
    return "\n".join(chunks) if chunks else json.dumps(response, ensure_ascii=False)


def parse_json_from_text(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def response_json_schema(name: str, schema: dict[str, Any]) -> dict[str, Any]:
    return {"format": {"type": "json_schema", "name": name, "schema": schema, "strict": False}}


VISUAL_SCHEMA = {
    "type": "object",
    "properties": {
        "visual_analysis": {
            "type": "object",
            "properties": {
                "detected_product_type": {"type": "string"},
                "main_subject": {"type": "string"},
                "visual_style": {"type": "string"},
                "colors": {"type": "array", "items": {"type": "string"}},
                "materials": {"type": "array", "items": {"type": "string"}},
                "shape": {"type": "string"},
                "usage_scenarios": {"type": "array", "items": {"type": "string"}},
                "important_visual_features": {"type": "array", "items": {"type": "string"}},
                "do_not_change": {"type": "array", "items": {"type": "string"}},
                "watermark_or_text_detected": {"type": "boolean"},
                "notes": {"type": "string"},
            },
            "required": [
                "detected_product_type",
                "main_subject",
                "visual_style",
                "colors",
                "materials",
                "shape",
                "usage_scenarios",
                "important_visual_features",
                "do_not_change",
                "watermark_or_text_detected",
                "notes",
            ],
        }
    },
    "required": ["visual_analysis"],
}


def analyze_source_images(request_data: dict[str, Any]) -> dict[str, Any]:
    api_key = require_api_key()
    product_id = str(request_data.get("product_id", "")).strip()
    if not product_id:
        raise RuntimeError("product_id is required.")
    source_images = request_data.get("source_images") or request_data.get("uploaded_images") or []
    if not isinstance(source_images, list) or not source_images:
        raise RuntimeError("source_images must be a non-empty array.")

    output_dir = ensure_dir(PROJECT_ROOT / "output" / product_id / "openai_pack_v2")
    content: list[dict[str, Any]] = [
        {
            "type": "input_text",
            "text": (
                f"Title: {request_data.get('title', '')}\n"
                f"Keywords: {request_data.get('keywords', '')}\n"
                "Analyze the product images for ecommerce image generation. "
                "Return product type, subject, style, colors, materials, shape, scenarios, important features, do_not_change, watermark/text detection, notes."
            ),
        }
    ]
    for image in source_images[:5]:
        content.append({"type": "input_image", "image_url": normalize_source_image(str(image))})

    response = openai_json_request(
        "/responses",
        {
            "model": OPENAI_TEXT_MODEL,
            "input": [
                {"role": "system", "content": [{"type": "input_text", "text": "Return only valid JSON for visual product analysis."}]},
                {"role": "user", "content": content},
            ],
            "text": response_json_schema("visual_analysis_result", VISUAL_SCHEMA),
        },
        api_key,
    )
    data = parse_json_from_text(extract_text_from_responses(response))
    if "visual_analysis" not in data:
        raise RuntimeError("OpenAI visual analysis did not return visual_analysis.")
    analysis_path = output_dir / "visual_analysis.json"
    write_json(analysis_path, data)
    return {
        "status": "success",
        "product_id": product_id,
        "visual_analysis": data["visual_analysis"],
        "visual_analysis_url": project_relative(analysis_path),
    }


def build_planner_content(request_data: dict[str, Any]) -> list[dict[str, Any]]:
    visual_analysis = request_data.get("visual_analysis") or {}
    content: list[dict[str, Any]] = [
        {
            "type": "input_text",
            "text": (
                "Create a MercadoLibre image prompt pack. No video. No Banana. "
                f"Title: {request_data.get('title', '')}\n"
                f"Keywords: {request_data.get('keywords', '')}\n"
                f"Target country: {request_data.get('target_country', '')}\n"
                f"Detail count per language: {request_data.get('detail_count_per_language', DEFAULT_DETAIL_COUNT)}\n"
                f"Visual analysis: {json.dumps(visual_analysis, ensure_ascii=False)}\n"
                "MX/CO/CL use Latin American Spanish. BR uses Brazilian Portuguese. Use short clear text in images."
            ),
        }
    ]
    for image in (request_data.get("source_images") or [])[:5]:
        content.append({"type": "input_image", "image_url": normalize_source_image(str(image))})
    return content


def call_prompt_planner(request_data: dict[str, Any], api_key: str) -> dict[str, Any]:
    schema = {
        "type": "object",
        "properties": {
            "product_analysis": {"type": "object"},
            "prompt_pack": {
                "type": "object",
                "properties": {
                    "main_image_prompt": {"type": "string"},
                    "detail_prompts_es": {"type": "array", "items": {"type": "string"}},
                    "detail_prompts_pt": {"type": "array", "items": {"type": "string"}},
                    "copy_es": {"type": "object"},
                    "copy_pt": {"type": "object"},
                    "qc_checklist": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["main_image_prompt", "detail_prompts_es", "detail_prompts_pt", "copy_es", "copy_pt", "qc_checklist"],
            },
        },
        "required": ["product_analysis", "prompt_pack"],
    }
    response = openai_json_request(
        "/responses",
        {
            "model": OPENAI_TEXT_MODEL,
            "input": [
                {"role": "system", "content": [{"type": "input_text", "text": "You are a MercadoLibre ecommerce creative director. Return only valid JSON."}]},
                {"role": "user", "content": build_planner_content(request_data)},
            ],
            "text": response_json_schema("prompt_pack_result", schema),
        },
        api_key,
    )
    data = parse_json_from_text(extract_text_from_responses(response))
    if not isinstance(data.get("prompt_pack"), dict):
        raise RuntimeError("OpenAI prompt planner did not return prompt_pack.")
    return data


def prompt_list(value: Any, count: int, fallback: str) -> list[str]:
    items = [str(item).strip() for item in value] if isinstance(value, list) else []
    items = [item for item in items if item]
    while len(items) < count:
        items.append(f"{fallback} {len(items) + 1}: clean ecommerce detail image, short readable text, premium composition.")
    return items[:count]


def merge_prompt_pack(auto_pack: dict[str, Any], manual: dict[str, Any], count: int) -> dict[str, Any]:
    merged = dict(auto_pack)
    merged["detail_prompts_es"] = prompt_list(auto_pack.get("detail_prompts_es"), count, "Spanish detail")
    merged["detail_prompts_pt"] = prompt_list(auto_pack.get("detail_prompts_pt"), count, "Portuguese detail")
    merged["main_image_prompt"] = str(auto_pack.get("main_image_prompt", "")).strip() or "Clean 1:1 ecommerce main product image on pure white background."
    if manual.get("enabled"):
        if manual.get("main_image_prompt"):
            merged["main_image_prompt"] = str(manual["main_image_prompt"]).strip()
        for key in ("detail_prompts_es", "detail_prompts_pt"):
            values = manual.get(key) or []
            if isinstance(values, list):
                for index, value in enumerate(values[:count]):
                    if str(value).strip():
                        merged[key][index] = str(value).strip()
        suffix = " ".join(
            part
            for part in [
                f"Style note: {manual.get('global_style_note', '')}".strip(),
                f"Avoid: {manual.get('negative_prompt', '')}".strip(),
            ]
            if part and not part.endswith(":")
        )
        if suffix:
            merged["main_image_prompt"] += " " + suffix
            merged["detail_prompts_es"] = [prompt + " " + suffix for prompt in merged["detail_prompts_es"]]
            merged["detail_prompts_pt"] = [prompt + " " + suffix for prompt in merged["detail_prompts_pt"]]
    return merged


def generate_image(prompt: str, output_path: Path, api_key: str, is_main: bool = False) -> None:
    suffix = "1:1 square image. No video. No watermark. "
    suffix += "Pure white background, subtle natural context, clean studio lighting." if is_main else "Non-white ecommerce detail background, short clear text only."
    response = openai_json_request(
        "/images/generations",
        {"model": OPENAI_IMAGE_MODEL, "prompt": prompt + " " + suffix, "size": "1024x1024", "n": 1, "background": "opaque"},
        api_key,
        timeout=300,
    )
    item = (response.get("data") or [{}])[0]
    if item.get("b64_json"):
        output_path.write_bytes(base64.b64decode(item["b64_json"]))
        return
    if item.get("url"):
        with urllib.request.urlopen(item["url"], timeout=180) as image_response:
            output_path.write_bytes(image_response.read())
        return
    raise RuntimeError(f"OpenAI image response did not include image data for {output_path.name}.")


def render_preview_html(request_data: dict[str, Any], output_dir: Path, result: dict[str, Any]) -> None:
    template_path = PROJECT_ROOT / "templates" / "preview_template.html"
    template = template_path.read_text(encoding="utf-8") if template_path.exists() else "<html><body>{{GENERATED_IMAGES}}</body></html>"
    source_html = "".join(f"<div class='source'><code>{escape(str(image))}</code></div>" for image in request_data.get("source_images", []) or [])
    cards = [("主图", result["main_image_url"])]
    cards += [(f"ES {i + 1}", path) for i, path in enumerate(result["detail_images_es"])]
    cards += [(f"PT {i + 1}", path) for i, path in enumerate(result["detail_images_pt"])]
    generated = "".join(
        f'<article class="card"><h3>{escape(label)}</h3><img src="{escape(Path(path).name)}" alt="{escape(label)}"></article>'
        for label, path in cards
    )
    html = (
        template.replace("{{TITLE}}", f"OpenAI Image Pack V2 - {escape(str(request_data.get('product_id', '')))}")
        .replace("{{PRODUCT_ID}}", escape(str(request_data.get("product_id", ""))))
        .replace("{{PRODUCT_TITLE}}", escape(str(request_data.get("title", ""))))
        .replace("{{KEYWORDS}}", escape(str(request_data.get("keywords", ""))))
        .replace("{{TARGET_COUNTRY}}", escape(str(request_data.get("target_country", ""))))
        .replace("{{SOURCE_IMAGES}}", source_html or "<p>No source images provided.</p>")
        .replace("{{GENERATED_IMAGES}}", generated)
        .replace("{{MANIFEST_URL}}", "preview_manifest.json")
        .replace("{{LISTING_READY_URL}}", "listing_ready.json")
    )
    (output_dir / "preview.html").write_text(html, encoding="utf-8")


StatusCallback = Callable[[str, int, str], None]


def run_openai_image_pack(request_data: dict[str, Any], status_callback: StatusCallback | None = None) -> dict[str, Any]:
    def update(status: str, progress: int, message: str) -> None:
        if status_callback:
            status_callback(status, progress, message)

    update("running", 5, "analyzing")
    api_key = require_api_key()
    if not request_data.get("source_images") and request_data.get("uploaded_images"):
        request_data["source_images"] = request_data.get("uploaded_images")
    product_id = str(request_data.get("product_id", "")).strip()
    if not product_id:
        raise RuntimeError("product_id is required.")
    if not request_data.get("title"):
        raise RuntimeError("title is required.")
    count = max(6, min(8, int(request_data.get("detail_count_per_language") or DEFAULT_DETAIL_COUNT)))
    output_dir = ensure_dir(PROJECT_ROOT / "output" / product_id / "openai_pack_v2")

    if not request_data.get("visual_analysis"):
        analysis_path = output_dir / "visual_analysis.json"
        if analysis_path.exists():
            request_data["visual_analysis"] = json.loads(analysis_path.read_text(encoding="utf-8")).get("visual_analysis", {})

    update("running", 20, "prompt_generating")
    planner = call_prompt_planner(request_data, api_key)
    prompt_pack = merge_prompt_pack(planner["prompt_pack"], request_data.get("manual_override") or {}, count)
    planner["prompt_pack"] = prompt_pack
    write_json(output_dir / "product_analysis.json", planner)

    update("running", 35, "main_image_generating")
    prefix = f"Product title: {request_data.get('title', '')}. Keywords: {request_data.get('keywords', '')}. Preserve product identity from references. "
    main_path = output_dir / "main_image.png"
    generate_image(prefix + prompt_pack["main_image_prompt"], main_path, api_key, True)

    update("running", 45, "detail_images_generating")
    es_paths: list[str] = []
    for index, prompt in enumerate(prompt_pack["detail_prompts_es"], start=1):
        path = output_dir / f"detail_es_{index:02d}.png"
        generate_image(prefix + prompt, path, api_key)
        es_paths.append(project_relative(path))
        update("running", min(65, 45 + int(index * 20 / max(1, count))), "detail_images_generating")
    pt_paths: list[str] = []
    for index, prompt in enumerate(prompt_pack["detail_prompts_pt"], start=1):
        path = output_dir / f"detail_pt_{index:02d}.png"
        generate_image(prefix + prompt, path, api_key)
        pt_paths.append(project_relative(path))
        update("running", min(85, 65 + int(index * 20 / max(1, count))), "detail_images_generating")

    update("running", 90, "packaging")
    result = {
        "status": "success",
        "product_id": product_id,
        "main_image_url": project_relative(main_path),
        "detail_images_es": es_paths,
        "detail_images_pt": pt_paths,
        "preview_url": project_relative(output_dir / "preview.html"),
        "listing_ready_url": project_relative(output_dir / "listing_ready.json"),
        "manifest_url": project_relative(output_dir / "preview_manifest.json"),
        "output_folder": project_relative(output_dir),
        "manual_review_required": True,
    }
    listing = {
        "product_id": product_id,
        "title": request_data.get("title"),
        "keywords": request_data.get("keywords"),
        "target_country": request_data.get("target_country"),
        "copy_es": prompt_pack.get("copy_es", {}),
        "copy_pt": prompt_pack.get("copy_pt", {}),
        "images": result,
        "mercadolibre_api_ready": False,
    }
    write_json(output_dir / "listing_ready.json", listing)
    write_json(
        output_dir / "preview_manifest.json",
        {
            "product_id": product_id,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "request": request_data,
            "openai": {"text_model": OPENAI_TEXT_MODEL, "image_model": OPENAI_IMAGE_MODEL},
            "prompt_pack": prompt_pack,
            "outputs": result,
        },
    )
    if (request_data.get("output_options") or {}).get("create_preview_html", True):
        render_preview_html(request_data, output_dir, result)
    return result
