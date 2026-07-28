def push_to_erp(extracted: dict, file_id: str) -> dict:
    """Build (and optionally send) an ERP payload from extracted fields.

    Replace the commented requests.post with your ERP's API endpoint when
    you are ready to push downstream.
    """
    erp_payload = {
        "vendor": extracted.get("vendorName"),
        "invoice_number": extracted.get("invoiceNumber"),
        "total": extracted.get("totalAmount"),
        "currency": extracted.get("currency"),
        "due_date": extracted.get("dueDate"),
        "source_file_id": file_id,
    }
    # Replace with your ERP's API endpoint
    # requests.post("https://erp.example.com/api/invoices", json=erp_payload)
    print(f"ERP payload ready: {erp_payload}")
    return erp_payload
