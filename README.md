# Box invoice intake automation

A minimal, runnable reference service that watches a Box folder for new
invoice PDFs, extracts structured fields with
[Box AI Extract](https://developer.box.com/guides/box-ai/ai-tutorials/extract-metadata-structured),
and writes those values back to each file as Box metadata.

It implements the **webhook > extract > metadata** flow. A Flask backend
receives a `FILE.UPLOADED` webhook (or a simulated curl payload), calls
`POST /2.0/ai/extract_structured` with your Invoice metadata template, and
attaches the result with `POST /2.0/files/:id/metadata/:scope/:template`.

The companion repository to the tutorial is:
**[Automate invoice intake with Box AI Extract](https://developer.box.com/tutorials/invoice-intake)**.

## What it does

| Capability | How |
| --- | --- |
| Detect new invoice uploads | Box webhooks (`FILE.UPLOADED`) or a local curl simulation |
| Extract structured fields | `POST /2.0/ai/extract_structured` with a metadata template |
| Write values back to the file | `POST /2.0/files/:id/metadata/enterprise/:template` |
| Optional ERP handoff | `erp.py` builds a payload you can POST downstream |

## Project layout

```
box-automate-invoice-intake/
├── app.py                 # Flask webhook listener
├── box_client.py          # CCG Service Account auth
├── extract.py             # Box AI structured extract
├── metadata.py            # Attach metadata to the file
├── erp.py                 # Optional ERP payload builder
├── make_sample_invoice.py # Generates sample-invoice.pdf for testing
├── sample-invoice.pdf
├── requirements.txt
├── .env.example
└── .gitignore
```

## Prerequisites

- **Python 3.11+**
- A [free Box developer account](https://account.box.com/signup/developer),
  or a [Box Enterprise account](https://www.box.com/pricing) with **Box AI**
  enabled. Consumer/Individual accounts do not work.
- A **Client Credentials Grant (CCG)** Platform App, **authorized** in the
  Admin Console, with these scopes enabled:
  - **Read and write all files and folders stored in Box**
  - **Manage AI**
  - **Manage webhooks**
- An **Invoice** metadata template in the Admin Console (see Setup below)
- An **Invoices Inbox** folder in Box, with the app's **Service Account**
  invited as an **Editor** collaborator

## Setup

1. **Clone and enter the project**

   ```bash
   git clone https://github.com/box-community/box-automate-invoice-intake.git
   cd box-automate-invoice-intake
   ```

2. **Create a virtual environment and install dependencies**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   ```

3. **Create the Invoice metadata template** (Admin Console > **Metadata** >
   **Invoices** tab > **New**). Name it `Invoice` and add these fields:

   | Field name | Type | Description |
   | --- | --- | --- |
   | Vendor Name | Text | Vendor or supplier name |
   | Invoice Number | Text | Unique invoice identifier |
   | Invoice Date | Date | Date the invoice was issued |
   | Due Date | Date | Payment due date |
   | Total Amount | Number | Total due, including taxes and fees |
   | Currency | Text | Three-letter currency code (USD, EUR, GBP) |

   Copy the **template key** shown under Template Name — you need it for `.env`.

4. **Create the Invoices Inbox folder** in Box and note its folder ID from the
   URL (`https://app.box.com/folder/123456789` > `123456789`).

   **Critical:** invite the app's Service Account as an **Editor** on that
   folder. Find the Service Account email in Developer Console > your app >
   **General Settings** > **Service Account ID** (looks like
   `AutomationUser_xxxxx_xxxxxx@boxdevedition.com`). Without this collaboration,
   API calls return `404 Not Found`.

5. **Configure credentials**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and fill in:

   - `BOX_CLIENT_ID`, `BOX_CLIENT_SECRET`, `BOX_ENTERPRISE_ID` from the
     Developer Console
   - `BOX_METADATA_TEMPLATE_KEY` from step 3
   - `INVOICES_FOLDER_ID` from step 4

   > **Never commit `.env`.** It is already in `.gitignore`.

## Run

```bash
python app.py
```

The server starts on `http://127.0.0.1:5000` (with auto-reload enabled).

> Do not use `debug=True` in production.

## Try it

You can exercise the whole pipeline locally without a public URL or a real
webhook. You need **two terminals**: one running the Flask server, one sending
a simulated payload.

1. **Upload `sample-invoice.pdf`** to your Invoices Inbox folder in Box
   (regenerate any time with `python make_sample_invoice.py`). Note the
   **file ID** from the file URL (`https://app.box.com/file/123456789` >
   `123456789`). Use the file ID, not the folder ID.

2. **Start the server** (terminal 1):

   ```bash
   source .venv/bin/activate
   python app.py
   ```

3. **Simulate a webhook** (terminal 2 — replace `<FILE_ID>`):

   ```bash
   curl -X POST http://127.0.0.1:5000/webhook \
     -H "Content-Type: application/json" \
     -d '{
       "trigger": "FILE.UPLOADED",
       "source": {
         "id": "<FILE_ID>",
         "name": "sample-invoice.pdf"
       }
     }'
   ```

4. **Check the result.** Terminal 1 should print extracted fields and confirm
   metadata was applied. Open the file in Box > **Metadata** tab to verify.

### Register a real webhook (production)

For automatic processing when files arrive, expose the app over HTTPS (for
example with a tunnel) and register a webhook on the inbox folder:

```bash
curl -X POST https://api.box.com/2.0/webhooks \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "target": {
      "id": "<FOLDER_ID>",
      "type": "folder"
    },
    "address": "<webhook_url>/webhook",
    "triggers": ["FILE.UPLOADED"]
  }'
```

In production, [verify webhook signatures](https://developer.box.com/guides/webhooks/v2/signatures-v2)
before processing.

## How it works

1. A PDF lands in the Invoices Inbox (or you POST a simulated webhook).
2. `extract.py` calls Box AI with your Invoice metadata template so the
   response shape is consistent across vendor formats.
3. `metadata.py` writes those values onto the file as an enterprise metadata
   instance - searchable and visible in the Box UI.
4. Optionally, uncomment the `push_to_erp(...)` call in `app.py` to hand off
   structured totals to an ERP.

## Security notes

- Keep the client secret, enterprise ID, and access tokens server-side.
- Grant the Service Account only the folder access it needs (Editor on the
  inbox is enough for this sample).
- Verify webhook signatures in production.
- Make the handler idempotent for duplicate webhook deliveries (check whether
  metadata already exists before extracting again).

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `unauthorized_client` | Authorize the app in the Admin Console (Developer Console > Authorization > Review and Submit). |
| `invalid_client` | Check `BOX_CLIENT_ID` / `BOX_CLIENT_SECRET` / `BOX_ENTERPRISE_ID` in `.env`. |
| `404 Not Found` | Invite the Service Account as **Editor** on the Invoices Inbox folder (and on the file's parent if different). |
| `metadata_template must have both scope and template_key` | Set `BOX_METADATA_TEMPLATE_KEY` in `.env` to the key from the Admin Console. |
| `ModuleNotFoundError` | Activate the venv: `source .venv/bin/activate`. |
| Extraction fails / AI errors | Confirm the **Manage AI** scope is enabled and the app was re-authorized after enabling it. Box AI must be available on the account. |

## License

[MIT](./LICENSE)
