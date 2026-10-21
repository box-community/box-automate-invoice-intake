"""Live end-to-end test against a real Box enterprise.

Runs the tutorial flow as a reader would: upload sample-invoice.pdf, post a
simulated FILE.UPLOADED webhook to the Flask app, then read back the metadata
instance. Posts the webhook twice so the 409 update path in metadata.py runs too.

Works in a throwaway subfolder of INVOICES_FOLDER_ID and deletes it at the end.
Reads the same variables as .env.example, from the environment or a local .env.
"""

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from box_sdk_gen import (  # noqa: E402
    CreateFolderParent,
    GetFileMetadataByIdScope,
    UploadFileAttributes,
    UploadFileAttributesParentField,
)

from app import app  # noqa: E402
from box_client import get_box_client  # noqa: E402

REQUIRED_ENV = [
    "BOX_CLIENT_ID",
    "BOX_CLIENT_SECRET",
    "BOX_ENTERPRISE_ID",
    "BOX_METADATA_TEMPLATE_KEY",
    "INVOICES_FOLDER_ID",
]


def post_webhook(test_client, file_id: str) -> None:
    response = test_client.post(
        "/webhook",
        json={
            "trigger": "FILE.UPLOADED",
            "source": {"id": file_id, "name": "sample-invoice.pdf"},
        },
    )
    expected = {"status": "processed", "file_id": file_id}
    assert response.status_code == 200, f"/webhook returned {response.status_code}"
    assert response.get_json() == expected, f"/webhook returned {response.get_json()}"


def main() -> None:
    missing = [name for name in REQUIRED_ENV if not os.getenv(name)]
    if missing:
        sys.exit(f"Missing environment variables: {', '.join(missing)}")

    client = get_box_client()
    run_id = os.getenv("GITHUB_RUN_ID") or f"local-{int(time.time())}"
    folder = client.folders.create_folder(
        f"ci-run-{run_id}",
        CreateFolderParent(id=os.getenv("INVOICES_FOLDER_ID")),
    )

    try:
        with open("sample-invoice.pdf", "rb") as pdf:
            uploaded = client.uploads.upload_file(
                UploadFileAttributes(
                    name="sample-invoice.pdf",
                    parent=UploadFileAttributesParentField(id=folder.id),
                ),
                pdf,
            )
        file_id = uploaded.entries[0].id
        print(f"Uploaded sample-invoice.pdf as file {file_id}")

        test_client = app.test_client()
        post_webhook(test_client, file_id)
        post_webhook(test_client, file_id)

        metadata = client.file_metadata.get_file_metadata_by_id(
            file_id,
            GetFileMetadataByIdScope.ENTERPRISE,
            os.getenv("BOX_METADATA_TEMPLATE_KEY"),
        )
        fields = metadata.extra_data or {}
        print(f"Metadata on file: {fields}")

        assert "INV-001" in str(fields.get("invoiceNumber", "")), "invoiceNumber mismatch"
        assert float(fields.get("totalAmount", 0)) == 1250, "totalAmount mismatch"

        print("Live test passed")
    finally:
        client.folders.delete_folder_by_id(folder.id, recursive=True)
        print(f"Deleted test folder {folder.id}")


if __name__ == "__main__":
    main()
