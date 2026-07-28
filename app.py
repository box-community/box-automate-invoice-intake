import json

from dotenv import load_dotenv
from flask import Flask, request, jsonify

from box_client import get_box_client
from extract import extract_invoice_fields
from metadata import apply_metadata

load_dotenv()
app = Flask(__name__)


@app.route("/")
def index():
    """Friendly landing page with usage hints."""
    return jsonify(
        {
            "service": "Box invoice intake automation",
            "endpoints": {
                "POST /webhook": (
                    "Receive FILE.UPLOADED webhook payloads, extract "
                    "invoice fields with Box AI, and write metadata"
                ),
                "GET /health": "Liveness check",
            },
            "local_test": (
                "curl -X POST http://127.0.0.1:5000/webhook "
                '-H "Content-Type: application/json" '
                "-d '{\"trigger\":\"FILE.UPLOADED\","
                '"source":{"id":"<FILE_ID>","name":"sample-invoice.pdf"}}'
                "'"
            ),
        }
    )


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/webhook", methods=["POST"])
def handle_webhook():
    """Handle Box FILE.UPLOADED webhooks for the Invoices Inbox folder.

    In production, verify webhook signatures before processing. See:
    https://developer.box.com/guides/webhooks/v2/signatures-v2
    """
    payload = request.get_json()

    if not payload or payload.get("trigger") != "FILE.UPLOADED":
        return jsonify({"status": "ignored"}), 200

    file_id = payload["source"]["id"]
    file_name = payload["source"]["name"]

    if not file_name.lower().endswith(".pdf"):
        return jsonify({"status": "skipped, not a PDF"}), 200

    client = get_box_client()

    extracted = extract_invoice_fields(client, file_id)
    print(f"Extracted from {file_name}: {json.dumps(extracted, indent=2)}")

    apply_metadata(client, file_id, extracted)
    print(f"Metadata applied to file {file_id}")

    # Optional: push structured totals to an ERP.
    # from erp import push_to_erp
    # push_to_erp(extracted, file_id)

    return jsonify({"status": "processed", "file_id": file_id}), 200


if __name__ == "__main__":
    app.run(port=5000, debug=True)
