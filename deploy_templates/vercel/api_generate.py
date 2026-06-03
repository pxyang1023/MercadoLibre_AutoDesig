import json
import os
import urllib.request


def handler(request):
    if request.method != "POST":
        return {
            "statusCode": 405,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"status": "error", "message": "Use POST /generate"}),
        }

    generator_base_url = os.environ.get("GENERATOR_BASE_URL", "").rstrip("/")
    if not generator_base_url:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"status": "error", "message": "GENERATOR_BASE_URL is not configured"}),
        }

    body = request.body or b"{}"
    req = urllib.request.Request(
        f"{generator_base_url}/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=120) as response:
        payload = response.read().decode("utf-8")

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": payload,
    }
