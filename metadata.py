import os

from dotenv import load_dotenv
from box_sdk_gen import (
    BoxAPIError,
    BoxClient,
    CreateFileMetadataByIdScope,
    UpdateFileMetadataByIdRequestBody,
    UpdateFileMetadataByIdRequestBodyOpField,
    UpdateFileMetadataByIdScope,
)

load_dotenv()


def apply_metadata(client: BoxClient, file_id: str, metadata: dict) -> dict:
    """Attach extracted values to the file as a metadata instance.

    Creates the instance on first run. On 409 Conflict (instance already
    exists — common when retesting a file or when Box delivers a duplicate
    webhook), falls back to a JSON-Patch update using op ``add`` so each
    returned field is set whether or not it was present before.

    Once attached, the fields are searchable, filterable, and visible
    in the Box web app Metadata tab.
    """
    template_key = os.getenv("BOX_METADATA_TEMPLATE_KEY")

    try:
        attached = client.file_metadata.create_file_metadata_by_id(
            file_id=file_id,
            scope=CreateFileMetadataByIdScope.ENTERPRISE,
            template_key=template_key,
            request_body=metadata,
        )
    except BoxAPIError as error:
        if error.response_info.status_code != 409:
            raise

        attached = client.file_metadata.update_file_metadata_by_id(
            file_id=file_id,
            scope=UpdateFileMetadataByIdScope.ENTERPRISE,
            template_key=template_key,
            request_body=[
                UpdateFileMetadataByIdRequestBody(
                    op=UpdateFileMetadataByIdRequestBodyOpField.ADD,
                    path=f"/{key}",
                    value=value,
                )
                for key, value in metadata.items()
            ],
        )

    return attached.to_dict()
