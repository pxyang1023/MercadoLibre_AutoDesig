import json
import os
import sys
from html import escape
from urllib.parse import urlparse
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


def build_home_html():
    preview_manifest_path = PROJECT_ROOT / "output" / DEFAULT_PRODUCT_ID / "cloud_preview" / "preview_manifest.json"
    preview_link = '<a class="button" href="/preview_manifest">Preview Manifest</a>' if preview_manifest_path.exists() else '<span class="button disabled">Preview Manifest not generated yet</span>'
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MercadoLibre AutoDesign Cloud Test Panel</title>
  <style>
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: #f3f6f8;
      color: #0f172a;
    }}
    main {{
      max-width: 880px;
      margin: 0 auto;
      padding: 44px 22px;
    }}
    .panel {{
      background: #fff;
      border: 1px solid #e2e8f0;
      border-radius: 18px;
      box-shadow: 0 18px 40px rgba(15, 23, 42, .08);
      padding: 28px;
    }}
    h1 {{
      margin: 0 0 12px;
      color: #075985;
      font-size: 34px;
    }}
    p, li {{
      color: #334155;
      line-height: 1.7;
    }}
    .buttons {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin: 22px 0;
    }}
    .button {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 42px;
      padding: 10px 16px;
      border-radius: 10px;
      background: #00a6b4;
      color: #fff;
      font-weight: 700;
      text-decoration: none;
    }}
    .button.disabled {{
      background: #94a3b8;
      color: #f8fafc;
    }}
    code {{
      background: #f1f5f9;
      padding: 2px 6px;
      border-radius: 6px;
    }}
  </style>
</head>
<body>
  <main>
    <section class="panel">
      <h1>MercadoLibre AutoDesign Cloud Test Panel</h1>
      <p>Service is running: <strong>{escape(SERVICE_NAME)}</strong></p>
      <p>Use this page to test the cloud deployment in a browser. No Postman or curl required.</p>
      <div class="buttons">
        <a class="button" href="/health">Health Check</a>
        <a class="button" href="/generate-test">Generate NB001</a>
        {preview_link}
      </div>
      <h2>Available endpoints</h2>
      <ul>
        <li><code>GET /</code> Browser test panel.</li>
        <li><code>GET /health</code> Health check JSON.</li>
        <li><code>GET /generate-test</code> Browser-only test endpoint for NB001.</li>
        <li><code>GET /preview_manifest</code> Returns preview manifest JSON if generated.</li>
        <li><code>POST /generate</code> Official API endpoint for n8n and automation.</li>
      </ul>
      <p><strong>Note:</strong> <code>/generate</code> is the formal POST API. <code>/generate-test</code> is only for browser testing.</p>
    </section>
  </main>
</body>
</html>"""


def build_generate_test_html(result):
    json_block = escape(json.dumps(result, ensure_ascii=False, indent=2))
    images = "\n".join(f"<li>{escape(name)}</li>" for name in result.get("images", []))
    preview_index = PROJECT_ROOT / result.get("preview_index", "")
    preview_note = (
        f"<p>Cloud preview index exists in container/local path: <code>{escape(str(preview_index))}</code></p>"
        if preview_index.exists()
        else "<p>Cloud preview index was not found yet.</p>"
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Generate NB001 Result</title>
  <style>
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: #f3f6f8;
      color: #0f172a;
    }}
    main {{
      max-width: 960px;
      margin: 0 auto;
      padding: 36px 22px;
    }}
    section {{
      background: #fff;
      border: 1px solid #e2e8f0;
      border-radius: 18px;
      box-shadow: 0 18px 40px rgba(15, 23, 42, .08);
      padding: 26px;
    }}
    h1 {{ color: #075985; margin-top: 0; }}
    dl {{
      display: grid;
      grid-template-columns: 180px 1fr;
      gap: 10px 16px;
    }}
    dt {{ color: #64748b; }}
    dd {{ margin: 0; overflow-wrap: anywhere; }}
    pre {{
      white-space: pre-wrap;
      background: #0f172a;
      color: #e2e8f0;
      border-radius: 12px;
      padding: 16px;
      overflow: auto;
    }}
    a {{
      color: #007f8a;
      font-weight: 700;
    }}
  </style>
</head>
<body>
  <main>
    <section>
      <h1>Generate NB001 Result</h1>
      <p><a href="/">Back to test panel</a></p>
      <dl>
        <dt>status</dt><dd>{escape(result.get("status", ""))}</dd>
        <dt>product_id</dt><dd>{escape(result.get("product_id", ""))}</dd>
        <dt>final_folder</dt><dd>{escape(result.get("final_folder", ""))}</dd>
        <dt>preview_folder</dt><dd>{escape(result.get("preview_folder", ""))}</dd>
        <dt>zip_file</dt><dd>{escape(result.get("zip_file", ""))}</dd>
      </dl>
      {preview_note}
      <h2>Images</h2>
      <ul>{images}</ul>
      <h2>Raw JSON</h2>
      <pre>{json_block}</pre>
    </section>
  </main>
</body>
</html>"""


class ServerV1Handler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, payload):
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, status_code, html):
        body = html.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            self._send_html(200, build_home_html())
            return

        if path == "/health":
            self._send_json(
                200,
                {
                    "status": "ok",
                    "service": SERVICE_NAME,
                },
            )
            return

        if path == "/generate-test":
            try:
                result = run_full_generation(
                    {
                        "product_id": DEFAULT_PRODUCT_ID,
                        "csv": DEFAULT_CSV,
                        "plan": DEFAULT_PLAN,
                    }
                )
                self._send_html(200, build_generate_test_html(result))
            except RuntimeError as exc:
                self._send_html(500, f"<h1>Generate test failed</h1><p>{escape(str(exc))}</p><p><a href='/'>Back</a></p>")
            except Exception as exc:
                self._send_html(500, f"<h1>Unexpected error</h1><p>{escape(str(exc))}</p><p><a href='/'>Back</a></p>")
            return

        if path == "/preview_manifest":
            manifest_path = PROJECT_ROOT / "output" / DEFAULT_PRODUCT_ID / "cloud_preview" / "preview_manifest.json"
            if not manifest_path.exists():
                self._send_json(
                    404,
                    {
                        "status": "error",
                        "message": f"preview_manifest.json not found: {to_project_relative(manifest_path)}. Run /generate-test or POST /generate first.",
                    },
                )
                return
            try:
                with manifest_path.open("r", encoding="utf-8") as file:
                    self._send_json(200, json.load(file))
            except json.JSONDecodeError:
                self._send_json(
                    500,
                    {
                        "status": "error",
                        "message": f"preview_manifest.json exists but is invalid JSON: {to_project_relative(manifest_path)}",
                    },
                )
            return

        self._send_json(
            404,
            {
                "status": "error",
                "message": "Not found. Available endpoints: GET /, GET /health, GET /generate-test, GET /preview_manifest, POST /generate",
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
