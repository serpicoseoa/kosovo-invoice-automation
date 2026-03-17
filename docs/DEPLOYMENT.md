# Deployment Guide — Step by Step

## Prerequisites
Install these on the new machine before anything else:

| Software | Version | Download |
|----------|---------|----------|
| Docker Desktop | Latest | https://www.docker.com/products/docker-desktop/ |
| Git | Latest | https://git-scm.com/download/win |
| Python | 3.10+ | https://www.python.org/downloads/ |
| Dropbox (optional) | Latest | https://www.dropbox.com/install |

## Step 1 — Clone & Setup

```powershell
git clone https://github.com/YOUR_GITHUB_USERNAME/kosovo-invoice-automation.git
cd kosovo-invoice-automation
powershell -ExecutionPolicy Bypass -File setup.ps1
```

The setup script will ask for paths — press Enter to accept defaults or type your own.

## Step 2 — Configure .env

Edit `C:\Users\YOUR_USERNAME\Desktop\n8n-setup\.env`:
```
N8N_ENCRYPTION_KEY=<generated automatically>
N8N_BASIC_AUTH_PASSWORD=<SET THIS>
INVOICES_PATH=C:/Users/YOUR_USERNAME/Dropbox/Test/Invoices
SCRIPTS_PATH=C:/invoice-automation/scripts
UNSTRACT_API_KEY=<get from Unstract>
```

## Step 3 — Deploy Unstract (if not already running)

Unstract runs separately. Follow their official docs:
https://docs.unstract.com/

After Unstract is running, find the network name:
```powershell
docker network ls | Select-String unstract
```
Update `docker-compose.yml` if the network name differs from `unstract-network`.

## Step 4 — Start n8n

```powershell
cd C:\Users\YOUR_USERNAME\Desktop\n8n-setup
docker-compose up -d
```

Wait ~30 seconds, then open: http://localhost:5678

## Step 5 — Import & Configure Workflow

1. Log into n8n (admin / your password)
2. Click **+** → **New workflow** → **⋮** → **Import from file**
3. Select: `n8n-setup/Kosovo_Invoice_Automation_v2.json`
4. **Settings → Credentials → New → HTTP Header Auth**:
   - Name: `Unstract Google Prompt API Key`
   - Header Name: `Authorization`
   - Header Value: `Bearer YOUR_UNSTRACT_API_KEY`
5. Open **"Upload to Unstract"** node → assign the credential
6. Open **"Poll & Parse Unstract Result"** node → update `UNSTRACT_KEY` value
7. Update the Unstract URL if your org slug is different from `mock_org`
8. Toggle workflow **Active** ✅

## Step 6 — Test

1. Copy a test invoice PDF to your invoices folder
2. Wait 30 seconds (or click **Execute workflow** manually)
3. Check the invoice moves to `Completed/` and LB.xlsx has a new row

## Updating on the Same Machine

When you pull new changes from GitHub:
```powershell
cd kosovo-invoice-automation
git pull
# If Dockerfile changed:
cd C:\Users\YOUR_USERNAME\Desktop\n8n-setup
docker-compose build
docker-compose up -d
# If scripts changed — they auto-sync via volume mount, no restart needed
```
