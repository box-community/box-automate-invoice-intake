import os

from dotenv import load_dotenv
from box_sdk_gen import (
    AiItemBase,
    BoxClient,
    CreateAiExtractStructuredMetadataTemplate,
    CreateAiExtractStructuredMetadataTemplateTypeField,
)

load_dotenv()


def extract_invoice_fields(client: BoxClient, file_id: str) -> dict:
    """Call Box AI structured extract with the Invoice metadata template.

    The template tells Box AI which fields to look for and what data types
    to return, so the response shape is predictable across vendor formats.
    """
    template_key = os.getenv("BOX_METADATA_TEMPLATE_KEY")

    result = client.ai.create_ai_extract_structured(
        items=[AiItemBase(id=file_id)],
        metadata_template=CreateAiExtractStructuredMetadataTemplate(
            template_key=template_key,
            type=CreateAiExtractStructuredMetadataTemplateTypeField.METADATA_TEMPLATE,
            scope="enterprise",
        ),
    )

    return result.to_dict()["answer"]
