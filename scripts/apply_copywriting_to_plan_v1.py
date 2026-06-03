import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COPY_PATH = PROJECT_ROOT / "output" / "NB001" / "copywriting_result.json"
DEFAULT_PLAN_PATH = PROJECT_ROOT / "plans" / "NB001_product_plan.json"


def load_json(path):
    path = Path(path)
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as exc:
        raise RuntimeError(f"JSON file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON file: {path}") from exc


def save_json(path, data):
    with Path(path).open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def resolve_project_path(path):
    path = Path(path)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def build_backup_path(plan_path):
    backup_path = plan_path.with_name(f"{plan_path.stem}.backup{plan_path.suffix}")
    if not backup_path.exists():
        return backup_path

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return plan_path.with_name(f"{plan_path.stem}.backup_{timestamp}{plan_path.suffix}")


def create_backup(plan_path):
    backup_path = build_backup_path(plan_path)
    shutil.copy2(plan_path, backup_path)
    return backup_path


def get_image_by_index(plan_data, index):
    for image in plan_data.get("images", []):
        if image.get("index") == index:
            return image
    raise RuntimeError(f"Image index not found in plan: {index}")


def update_image(image, title=None, subtitle=None, bullets=None):
    if title is not None:
        image["title"] = title
    if subtitle is not None:
        image["subtitle"] = subtitle
    if bullets is not None:
        image["bullets"] = bullets


def apply_copywriting(copy_data, plan_data):
    new_title = copy_data.get("new_title", "")
    five_bullets = copy_data.get("five_bullets", [])

    plan_data["copywriting"] = {
        "new_title": new_title,
        "five_bullets": five_bullets,
        "background_keywords": copy_data.get("background_keywords", ""),
        "qc_result": copy_data.get("qc_result", ""),
        "problem_note": copy_data.get("problem_note", ""),
    }

    updated_indexes = []

    update_image(get_image_by_index(plan_data, 1), title="", subtitle="", bullets=[])
    updated_indexes.append(1)

    update_image(
        get_image_by_index(plan_data, 2),
        title=new_title,
        subtitle="Sabor fresco para compartir",
        bullets=five_bullets[:3],
    )
    updated_indexes.append(2)

    update_image(
        get_image_by_index(plan_data, 3),
        title="Sabor fresco y refrescante",
        subtitle=five_bullets[0] if len(five_bullets) >= 1 else "",
        bullets=five_bullets[:3],
    )
    updated_indexes.append(3)

    update_image(
        get_image_by_index(plan_data, 4),
        title="Detalles del producto",
        subtitle="Características principales",
        bullets=five_bullets[1:4],
    )
    updated_indexes.append(4)

    update_image(
        get_image_by_index(plan_data, 5),
        title="Para disfrutar en cualquier momento",
        subtitle=five_bullets[3] if len(five_bullets) >= 4 else "",
        bullets=five_bullets[2:5],
    )
    updated_indexes.append(5)

    update_image(
        get_image_by_index(plan_data, 6),
        title="Botella de 1L",
        subtitle="Más contenido para compartir",
        bullets=five_bullets[-3:],
    )
    updated_indexes.append(6)

    update_image(
        get_image_by_index(plan_data, 7),
        title="Frescura, sabor y practicidad",
        subtitle=new_title,
        bullets=five_bullets[:3],
    )
    updated_indexes.append(7)

    return updated_indexes


def run_apply(copy_path=DEFAULT_COPY_PATH, plan_path=DEFAULT_PLAN_PATH):
    copy_path = resolve_project_path(copy_path)
    plan_path = resolve_project_path(plan_path)

    copy_data = load_json(copy_path)
    qc_result = copy_data.get("qc_result", "")
    if qc_result != "pass":
        problem_note = copy_data.get("problem_note", "")
        raise RuntimeError(f"Copywriting QC did not pass: {qc_result}. {problem_note}")

    plan_data = load_json(plan_path)
    backup_path = create_backup(plan_path)
    updated_indexes = apply_copywriting(copy_data, plan_data)
    save_json(plan_path, plan_data)

    print(f"copywriting_result: {copy_path}")
    print(f"product_plan: {plan_path}")
    print(f"backup: {backup_path}")
    print(f"qc_result: {qc_result}")
    print(f"updated image indexes: {', '.join(str(index) for index in updated_indexes)}")
    print("apply copywriting to plan success")

    return {
        "copy_path": copy_path,
        "plan_path": plan_path,
        "backup_path": backup_path,
        "updated_indexes": updated_indexes,
    }


def main():
    parser = argparse.ArgumentParser(description="Apply copywriting_result.json to product_plan.json.")
    parser.add_argument("--copy", default=str(DEFAULT_COPY_PATH), help="Path to copywriting_result.json.")
    parser.add_argument("--plan", default=str(DEFAULT_PLAN_PATH), help="Path to product plan JSON.")
    args = parser.parse_args()

    try:
        run_apply(args.copy, args.plan)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
