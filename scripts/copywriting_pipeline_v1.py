import argparse
import csv
import json
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV_PATH = PROJECT_ROOT / "input" / "products" / "products_sample.csv"


STOP_WORDS = {
    "de", "con", "para", "y", "a", "el", "la", "los", "las", "un", "una",
    "en", "por", "do", "da", "com", "e", "o", "aos", "as", "os",
}


FORBIDDEN_WORDS = {
    "mejor", "perfecto", "perfecta", "maximo", "maximo", "increible",
    "milagroso", "garantizado", "garantizada", "best", "top", "numero",
}


def clean_text(value):
    text = (value or "").strip()
    text = text.replace("\ufffd\ufffdcido", "\u00e1cido")
    return re.sub(r"\s+", " ", text)


def split_selling_points(value):
    points = [clean_text(part) for part in (value or "").split(";")]
    return [point for point in points if point]


def trim_title(title, limit):
    title = clean_text(title)
    if len(title) <= limit:
        return title

    cut = title[:limit].rstrip()
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(" ,.-")


def build_title(product):
    language = clean_text(product.get("language")).lower()
    name = clean_text(product.get("product_name"))
    capacity = clean_text(product.get("capacity"))

    if language == "pt":
        base = f"{name} {capacity} Bebida Refrescante".strip()
        return trim_title(base, 50)

    base = f"{name} {capacity} Bebida Refrescante".strip()
    return trim_title(base, 60)


def build_five_bullets(product):
    language = clean_text(product.get("language")).lower()
    category = clean_text(product.get("category"))
    capacity = clean_text(product.get("capacity"))
    points = split_selling_points(product.get("selling_points"))

    if language == "pt":
        templates = [
            "Sabor leve e refrescante para o dia a dia",
            f"Formato de {capacity} pratico para compartilhar" if capacity else "Formato pratico para compartilhar",
            "Boa opcao para consumir gelado",
            "Ideal para refeicoes, reunioes e momentos em casa",
            f"Categoria {category} com perfil frutado e comercial" if category else "Perfil frutado e comercial",
        ]
    else:
        templates = [
            "Sabor fresco y agradable para disfrutar en frio",
            f"Presentacion de {capacity} practica para compartir" if capacity else "Presentacion practica para compartir",
            "Ideal para comidas, reuniones y momentos en casa",
            "Perfil frutal con sensacion ligera y refrescante",
            f"Opcion de categoria {category} para venta en linea" if category else "Opcion practica para venta en linea",
        ]

    bullets = []
    for point in points:
        bullets.append(point)
    for template in templates:
        if len(bullets) >= 5:
            break
        bullets.append(template)

    return [clean_text(bullet) for bullet in bullets[:5]]


def tokenize(text):
    words = re.findall(r"[A-Za-z0-9\u00c0-\u017f]+", clean_text(text).lower())
    return [word for word in words if word not in STOP_WORDS and len(word) > 1]


def build_keywords(product, bullets):
    language = clean_text(product.get("language")).lower()
    fields = [
        product.get("product_name", ""),
        product.get("category", ""),
        product.get("capacity", ""),
        product.get("selling_points", ""),
        " ".join(bullets),
    ]
    keywords = []
    for word in tokenize(" ".join(fields)):
        if word not in keywords:
            keywords.append(word)

    defaults = (
        ["bebida", "guayaba", "ciruela", "refrescante", "botella", "1l", "latam", "frutal", "te", "frio"]
        if language != "pt"
        else ["bebida", "goiaba", "ameixa", "refrescante", "garrafa", "1l", "brasil", "frutado", "cha", "gelado"]
    )
    for word in defaults:
        if word not in keywords:
            keywords.append(word)
        if len(keywords) >= 20:
            break

    return ", ".join(keywords[:20])


def has_obvious_repetition(text):
    words = tokenize(text)
    for first, second, third in zip(words, words[1:], words[2:]):
        if first == second == third:
            return True

    counts = {}
    for word in words:
        counts[word] = counts.get(word, 0) + 1
    return any(count >= 6 for count in counts.values())


def run_qc(product, title, bullets, keywords):
    language = clean_text(product.get("language")).lower()
    title_limit = 50 if language == "pt" else 60
    problems = []

    if not title:
        problems.append("\u6807\u9898\u4e3a\u7a7a")
    if len(title) > title_limit:
        problems.append(f"\u6807\u9898\u8d85\u8fc7 {title_limit} \u5b57\u7b26")
    if len(bullets) != 5:
        problems.append("\u4e94\u70b9\u63cf\u8ff0\u4e0d\u662f 5 \u6761")
    if not keywords:
        problems.append("\u540e\u53f0\u5173\u952e\u8bcd\u4e3a\u7a7a")

    text_for_checks = " ".join([title, keywords] + bullets).lower()
    normalized = text_for_checks.replace("\u00e1", "a").replace("\u00e9", "e").replace("\u00ed", "i").replace("\u00f3", "o").replace("\u00fa", "u")
    if any(word in normalized for word in FORBIDDEN_WORDS):
        problems.append("\u5305\u542b\u5938\u5f20\u8bcd\u6216\u6781\u9650\u8bcd")
    if has_obvious_repetition(text_for_checks):
        problems.append("\u5b58\u5728\u660e\u663e\u91cd\u590d\u8bcd")

    if problems:
        return "fail", "\uff1b".join(problems)
    return "pass", "\u65e0\u95ee\u9898"


def generate_copywriting(product):
    language = clean_text(product.get("language")) or "es"
    market = clean_text(product.get("market")) or "LatAm"
    title = build_title(product)
    bullets = build_five_bullets(product)
    keywords = build_keywords(product, bullets)
    qc_result, problem_note = run_qc(product, title, bullets, keywords)

    return {
        "product_id": clean_text(product.get("product_id")),
        "language": language,
        "market": market,
        "new_title": title,
        "five_bullets": bullets,
        "background_keywords": keywords,
        "qc_result": qc_result,
        "problem_note": problem_note,
    }


def write_result(result):
    product_id = result["product_id"]
    output_dir = PROJECT_ROOT / "output" / product_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "copywriting_result.json"
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=2)
    return output_path


def run_pipeline(csv_path=DEFAULT_CSV_PATH):
    csv_path = Path(csv_path)
    if not csv_path.is_absolute():
        csv_path = PROJECT_ROOT / csv_path
    if not csv_path.exists():
        raise RuntimeError(f"CSV file not found: {csv_path}")

    outputs = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            cleaned_row = {key: clean_text(value) for key, value in row.items()}
            result = generate_copywriting(cleaned_row)
            output_path = write_result(result)
            outputs.append((output_path, result))
            print(f"copywriting_result: {output_path}")
            print(f"new_title: {result['new_title']}")
            print(f"qc_result: {result['qc_result']}")

    if not outputs:
        raise RuntimeError(f"No product rows found in CSV: {csv_path}")
    return outputs


def main():
    parser = argparse.ArgumentParser(description="Generate rule-based MercadoLibre copywriting results.")
    parser.add_argument("--csv", default=str(DEFAULT_CSV_PATH), help="Path to products CSV.")
    args = parser.parse_args()

    try:
        run_pipeline(args.csv)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
