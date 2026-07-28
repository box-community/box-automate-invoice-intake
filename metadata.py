import os

from dotenv import load_dotenv
from box_sdk_gen import BoxClient, CreateFileMetadataByIdScope

load_dotenv()


def apply_metadata(client: BoxClient, file_id: str, metadata: dict) -> dict:
    """Attach extracted values to the file as a metadata instance.

    Once attached, the fields are searchable, filterable, and visible
    in the Box web app Metadata tab.
    """
    template_key = os.getenv("BOX_METADATA_TEMPLATE_KEY")

    attached = client.file_metadata.create_file_metadata_by_id(
        file_id=file_id,
        scope=CreateFileMetadataByIdScope.ENTERPRISE,
        template_key=template_key,
        request_body=metadata,
    )

    return attached.to_dict()
