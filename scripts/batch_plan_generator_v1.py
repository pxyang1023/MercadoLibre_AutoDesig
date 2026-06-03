from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = PROJECT_ROOT / "input" / "products" / "products_batch_sample.csv"
PLANS_DIR = PROJECT_ROOT / "plans"


IMAGE_LAYOUTS = [
    (1, "main_white", "01_main_white.png"),
    (2, "selling_points", "02_selling_points.png"),
    (3, "flavor", "03_flavor.png"),
    (4, "ingredients", "04_ingredients.png"),
    (5, "lifestyle", "05_lifestyle.png"),
    (6, "capacity", "06_capacity.png"),
    (7, "summary", "07_summary.png"),
]


CATEGORY_TITLES = {
    "beverage": "Sabor fresco y práctico",
    "tools": "Diseño práctico y preciso",
    "home": "Solución práctica para el hogar",
}


def project_path(path_text: str | Path) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def split_selling_points(value: str) -> list[str]:
    parts = re.split(r"[;；]", value or "")
    return [part.strip() for part in parts if part.strip()]


def slice_points(points: list[str], start: int, end: int) -> list[str]:
    return points[start:end]


def last_points(points: list[str], count: int = 3) -> list[str]:
    return points[-count:] if len(points) >= count else points[:]


def make_image(index: int, image_type: str, filename: str) -> dict[str, Any]:
    return {
        "index": index,
        "type": image_type,
        "filename": filename,
        "title": "",
        "subtitle": "",
        "bullets": [],
    }


def build_images(row: dict[str, str], selling_points: list[str]) -> list[dict[str, Any]]:
    images = [make_image(*item) for item in IMAGE_LAYOUTS]
    product_name = row["product_name"].strip()
    category = row.get("category", "").strip().lower()
    capacity = row.get("capacity", "").strip()

    images[1].update(
        {
            "title": product_name,
            "subtitle": "Características principales",
            "bullets": slice_points(selling_points, 0, 3),
        }
    )
    images[2].update(
        {
            "title": CATEGORY_TITLES.get(category, "Características destacadas"),
            "subtitle": selling_points[0] if selling_points else "",
            "bullets": slice_points(selling_points, 0, 3),
        }
    )
    images[3].update(
        {
            "title": "Detalles del producto",
            "subtitle": "Características principales",
            "bullets": slice_points(selling_points, 1, 4),
        }
    )
    images[4].update(
        {
            "title": "Para usar en cualquier momento",
            "subtitle": selling_points[2] if len(selling_points) >= 3 else "",
            "bullets": last_points(selling_points, 3),
        }
    )
    images[5].update(
        {
            "title": capacity,
            "subtitle": "Información del producto",
            "bullets": last_points(selling_points, 3),
        }
    )
    images[6].update(
        {
            "title": "Resumen del producto",
            "subtitle": product_name,
            "bullets": slice_points(selling_points, 0, 3),
        }
    )
    return images


def build_plan(row: dict[str, str], selling_points: list[str]) -> dict[str, Any]:
    product_id = row["product_id"].strip()
    input_image = row["input_image"].strip()
    image_path = input_image if "/" in input_image or "\\" in input_image else f"input/images/{input_image}"

    return {
        "product_id": product_id,
        "product_name": row["product_name"].strip(),
        "category": row.get("category", "").strip(),
        "language": row.get("language", "").strip() or "es",
        "market": row.get("market", "").strip() or "LatAm",
        "capacity": row.get("capacity", "").strip(),
        "input_image": image_path.replace("\\", "/"),
        "output_folder": f"output/{product_id}",
        "selling_points": selling_points,
        "images": build_images(row, selling_points),
    }


def validate_row(row: dict[str, str], row_number: int) -> tuple[bool, list[str], list[str]]:
    errors: list[str] = []
    missing_images: list[str] = []
    product_id = (row.get("product_id") or "").strip()
    product_name = (row.get("product_name") or "").strip()
    input_image = (row.get("input_image") or "").strip()
    selling_points = split_selling_points(row.get("selling_points") or "")

    if not product_id:
        errors.append(f"row {row_number}: product_id is empty")
    if not product_name:
        errors.append(f"row {row_number}: product_name is empty")
    if not input_image:
        errors.append(f"row {row_number}: input_image is empty")
        if product_id:
            missing_images.append(product_id)
    if len(selling_points) < 2:
        errors.append(f"row {row_number}: selling_points must include at least 2 items")

    return not errors, errors, missing_images


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def generate_plans(csv_path: Path, overwrite: bool = False) -> dict[str, Any]:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    rows: list[dict[str, str]] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            rows.append({key: (value or "") for key, value in row.items()})

    PLANS_DIR.mkdir(parents=True, exist_ok=True)

    pending_rows = [row for row in rows if row.get("status", "").strip().lower() == "pending"]
    generated: list[str] = []
    skipped: list[str] = []
    failed: list[str] = []
    missing_input_image_products: list[str] = []

    for index, row in enumerate(pending_rows, start=2):
        product_id = row.get("product_id", "").strip()
        is_valid, errors, missing_images = validate_row(row, index)
        missing_input_image_products.extend(missing_images)
        if not is_valid:
            failed.extend(errors)
            for error in errors:
                print(f"validation failed: {error}")
            continue

        selling_points = split_selling_points(row["selling_points"])
        plan = build_plan(row, selling_points)
        if len(plan["images"]) != 7:
            failed.append(f"row {index}: images must include exactly 7 items")
            print(f"validation failed: row {index}: images must include exactly 7 items")
            continue

        plan_path = PLANS_DIR / f"{product_id}_product_plan.json"
        if plan_path.exists() and not overwrite:
            skipped.append(product_id)
            print(f"{plan_path} already exists, skipped")
            continue

        write_json(plan_path, plan)
        generated.append(product_id)
        print(f"generated: {plan_path}")

    summary = {
        "rows_read": len(rows),
        "pending_rows": len(pending_rows),
        "generated_count": len(generated),
        "skipped_count": len(skipped),
        "failed_count": len(failed),
        "generated": generated,
        "skipped": skipped,
        "failed": failed,
        "missing_input_image_products": missing_input_image_products,
    }

    print("\nsummary")
    print(f"rows_read: {summary['rows_read']}")
    print(f"pending_rows: {summary['pending_rows']}")
    print(f"generated_plans: {summary['generated_count']}")
    print(f"skipped_existing: {summary['skipped_count']}")
    print(f"validation_failed: {summary['failed_count']}")
    print(f"missing_input_image_products: {', '.join(missing_input_image_products) if missing_input_image_products else 'none'}")

    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate product_plan.json files from batch product CSV.")
    parser.add_argument("--csv", default=str(DEFAULT_CSV), help="Path to products batch CSV.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing product plan files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    csv_path = project_path(args.csv)
    try:
        generate_plans(csv_path, overwrite=args.overwrite)
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
