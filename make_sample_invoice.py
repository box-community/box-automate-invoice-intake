"""Generate a small, valid sample invoice PDF for testing extraction.

Pure standard library - no dependencies. Run:

    python make_sample_invoice.py

This writes sample-invoice.pdf in the current directory. Upload that file
to your Invoices Inbox folder in Box, then POST a simulated webhook to
/webhook with the resulting file ID.
"""

OUTPUT = "sample-invoice.pdf"

LINES = [
    "INVOICE",
    "",
    "Vendor: ACME Corp",
    "Invoice Number: INV-001",
    "Invoice Date: 2025-03-15",
    "Due Date: 2025-04-15",
    "",
    "Bill To: Contoso Manufacturing",
    "123 Industrial Way",
    "Austin, TX 78701",
    "",
    "Description                    Qty    Amount",
    "--------------------------------------------",
    "Widget assembly kits            10   $800.00",
    "Rush shipping                    1   $150.00",
    "Sales tax                            $300.00",
    "--------------------------------------------",
    "Total Amount:                      $1250.00",
    "Currency: USD",
    "",
    "This is a sample invoice for the Box invoice",
    "intake automation tutorial. It is not a real bill.",
]


def _content_stream() -> bytes:
    parts = ["BT", "/F1 12 Tf", "72 720 Td", "16 TL"]
    for line in LINES:
        # Escape PDF string special characters.
        safe = line.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")
        parts.append(f"({safe}) Tj")
        parts.append("T*")
    parts.append("ET")
    return ("\n".join(parts)).encode("latin-1")


def build_pdf() -> bytes:
    content = _content_stream()

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n"
        + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"

    xref_pos = len(pdf)
    count = len(objects) + 1
    pdf += f"xref\n0 {count}\n".encode()
    pdf += b"0000000000 65535 f \n"
    for off in offsets:
        pdf += f"{off:010d} 00000 n \n".encode()

    pdf += (
        b"trailer\n<< /Size " + str(count).encode() + b" /Root 1 0 R >>\n"
        b"startxref\n" + str(xref_pos).encode() + b"\n%%EOF\n"
    )
    return bytes(pdf)


if __name__ == "__main__":
    with open(OUTPUT, "wb") as f:
        f.write(build_pdf())
    print(f"Wrote {OUTPUT}")
