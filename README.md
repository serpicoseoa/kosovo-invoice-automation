# Kosovo Invoice Automation v2.0

Automated end-to-end invoice processing pipeline for Kosovo VAT compliance.
Processes PDF/JPEG invoices → Unstract AI extraction → Kosovo ATK Purchase Book (LB.xlsx) → Archived.

## Stack
| Component | Technology |
|-----------|-----------|
| Orchestration | n8n 2.x (latest, self-hosted) |
| Container | Docker + custom image (n8n + Python 3.12) |
| Document AI | Unstract API + Llama-3.1-8B (Google Prompt deployment) |
| Excel Engine | Python 3.12 + openpyxl |
| File Storage | Dropbox (bind-mounted into Docker) |

## Repo Structure
```
kosovo-invoice-automation/
├── README.md                          ← This file
├── setup.ps1                          ← One-click Windows setup script
├── scripts/
│   ├── excel_writer_lb.py             ← Writes to LB.xlsx (Kosovo ATK format, 30 cols)
│   ├── archive_lb_invoice.py          ← Renames & moves completed invoices
│   ├── checksum_manager.py            ← SHA-256 duplicate detection
│   ├── validation.py                  ← Invoice field validation
│   ├── ocr_fallback.py                ← OCR fallback for blurry documents
│   ├── poll_unstract.py               ← Unstract async polling utility
│   └── requirements.txt               ← Python dependencies
├── n8n-setup/
│   ├── Dockerfile                     ← Custom image: n8n latest + Python 3.12 + openpyxl
│   ├── docker-compose.yml             ← n8n service with volume mounts
│   ├── .env.template                  ← Environment variables template (copy to .env)
│   └── Kosovo_Invoice_Automation_v2.json ← n8n workflow (import this)
└── docs/
    ├── DEPLOYMENT.md                  ← Detailed deployment guide
    ├── CONFIGURATION.md               ← What to update on a new machine
    └── TROUBLESHOOTING.md             ← Common issues and fixes
```

## Quick Start (New Machine)

### Prerequisites
- Windows 10/11
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [Git](https://git-scm.com/download/win) installed
- Python 3.x installed (for setup script)
- Unstract instance running (see DEPLOYMENT.md)

### Install
```powershell
# 1. Clone the repo
git clone https://github.com/YOUR_GITHUB_USERNAME/kosovo-invoice-automation.git
cd kosovo-invoice-automation

# 2. Run setup (creates folders, copies files, builds Docker, starts n8n)
powershell -ExecutionPolicy Bypass -File setup.ps1

# 3. Follow the on-screen instructions to configure n8n
```

### What the setup script does
1. Creates folder structure (Invoices, Completed, Review, etc.)
2. Copies Python scripts to `C:\invoice-automation\scripts\`
3. Builds custom Docker image (n8n + Python)
4. Starts n8n at http://localhost:5678
5. Gives you next steps for workflow import

## Workflow Flow
```
[Every 30s] → List PDFs/JPGs in /data/invoices/
→ Read file (fs.readFileSync)
→ Upload to Unstract (multipart POST)
→ Poll until COMPLETED (every 10s, max 10 min)
→ Parse: invoice_data + amounts + vat_classification
→ Validate Albanian fields (Data, Numri faturës, Emri shitësit)
→ IF valid:
    → Write to LB.xlsx (ATK 30-column format, columns B-AD)
    → Archive to /Completed/{Supplier} - {Date} - {InvNum}.pdf
    → Success
→ IF invalid:
    → Move to /Review/{filename}-FAILED-{timestamp}
```
