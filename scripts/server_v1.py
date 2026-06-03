import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

try:
    from .apply_copywriting_to_plan_v1 import run_apply
    from .copywriting_pipeline_v1 import run_pipeline as run_copywriting
    from .export_cloud_preview_v1 import export_preview
    from .run_pipeline_v1 import run_pipeline as run_image_pipeline
except ImportError:
    from apply_copywriting_to_plan_v1 import run_apply
    from copywriting_pipeline_v1 import run_pipeline as run_copywriting
    from export_cloud_preview_v1 import export_preview
    from run_pipeline_v1 import run_pipeline as run_image_pipeline


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8899"))
SERVICE_NAME = "MercadoLibre AutoDesign Server V1"
DEFAULT_PRODUCT_ID = "NB001"
DEFAULT_CSV = "input/products/products_sample.csv"
DEFAULT_PLAN = "plans/NB001_product_plan.json"
FINAL_IMAGE_NAMES = [
    "01_main_white.png",
    "02_selling_points.png",
    "03_flavor.png",
    "04_ingredients.png",
    "05_lifestyle.png",
    "06_capacity.png",
    "07_summary.png",
]


def to_project_relative(path):
    path = Path(path)
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def resolve_project_path(path):
    path = Path(path)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def run_full_generation(request_data):
    product_id = request_data.get("product_id", DEFAULT_PRODUCT_ID)
    if product_id != DEFAULT_PRODUCT_ID:
        raise RuntimeError("Server V1 currently supports only product_id NB001.")

    csv_path = request_data.get("csv", DEFAULT_CSV)
    plan_path = request_data.get("plan", DEFAULT_PLAN)
    copy_path = Path("output") / product_id / "copywriting_result.json"

    print(f"generate request: product_id={product_id} csv={csv_path} plan={plan_path}")

    copywriting_outputs = run_copywriting(csv_path)
    print(f"step copywriting complete: {len(copywriting_outputs)} result(s)")

    apply_result = run_apply(copy_path, plan_path)
    print(f"step apply copywriting complete: {apply_result['plan_path']}")

    pipeline_result = run_image_pipeline(plan_path)
    print(f"step image pipeline complete: {pipeline_result['output_folder']}")

    preview_result = export_preview(product_id)
    print(f"step cloud preview export complete: {preview_result['preview_dir']}")

    output_folder = Path("output") / product_id
    final_folder = output_folder / "final"
    preview_folder = output_folder / "cloud_preview"
    preview_index = preview_folder / "index.html"
    zip_file = preview_folder / f"{product_id}_cloud_preview.zip"

    return {
        "status": "success",
        "product_id": product_id,
        "output_folder": to_project_relative(output_folder),
        "final_folder": to_project_relative(final_folder),
        "preview_folder": to_project_relative(preview_folder),
        "preview_index": to_project_relative(preview_index),
        "zip_file": to_project_relative(zip_file),
        "images": FINAL_IMAGE_NAMES,
    }


class ServerV1Handler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, payload):
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._send_json(
                200,
                {
                    "status": "ok",
                    "service": SERVICE_NAME,
                },
            )
            return

        self._send_json(
            404,
            {
                "status": "error",
                "message": "Not found. Available endpoints: GET /health, POST /generate",
            },
        )

    def do_POST(self):
        if self.path != "/generate":
            self._send_json(
                404,
                {
                    "status": "error",
                    "message": "Not found. Available endpoint: POST /generate",
                },
            )
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
            request_data = json.loads(raw_body)
            response = run_full_generation(request_data)
            self._send_json(200, response)
        except json.JSONDecodeError:
            self._send_json(
                400,
                {
                    "status": "error",
                    "message": "Invalid JSON request body.",
                },
            )
        except RuntimeError as exc:
            self._send_json(
                500,
                {
                    "status": "error",
                    "message": str(exc),
                },
            )
        except Exception as exc:
            self._send_json(
                500,
                {
                    "status": "error",
                    "message": f"Unexpected server error: {exc}",
                },
            )

    def log_message(self, format, *args):
        print(f"{self.client_address[0]} - {format % args}")


def main():
    server_address = (HOST, PORT)
    server = ThreadingHTTPServer(server_address, ServerV1Handler)
    print(f"{SERVICE_NAME} started at http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("server stopped")
    finally:
        server.server_close()


if __name__ == "__main__":
    try:
        main()
    except ImportError:
        print("If you choose to use Flask later, install it with: pip install flask", file=sys.stderr)
        sys.exit(1)
