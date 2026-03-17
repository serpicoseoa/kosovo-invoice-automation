# Configuration Guide — What to Update on a New Machine

## 1. Paths (MUST update)

Edit `n8n-setup/.env` after running setup.ps1:

| Variable | Description | Example |
|----------|-------------|---------|
| `INVOICES_PATH` | Where invoices arrive | `C:/Users/john/Dropbox/Test/Invoices` |
| `SCRIPTS_PATH` | Python scripts location | `C:/invoice-automation/scripts` |
| `BANK_STATEMENTS_PATH` | Bank statements folder | `C:/Users/john/Dropbox/Test/BankStatements` |

## 2. Credentials (MUST update)

### n8n Login
```
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=your_strong_password
```

### n8n Encryption Key
Generate a new unique key for each installation:
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

## 3. Unstract Setup (MUST configure)

### 3a. Start Unstract
Unstract must be running separately. It is NOT included in this repo's docker-compose.
- Unstract repo: https://github.com/Zipstack/unstract
- After starting, access at: http://frontend.unstract.localhost

### 3b. Get your Unstract API Key
1. Open Unstract → API Deployments
2. Find "Google Prompt API" deployment
3. Click ⋮ → Edit → copy the API key shown

### 3c. Network requirement
n8n must be on the same Docker network as Unstract.
The docker-compose.yml attaches n8n to `unstract-network` (external).
If your Unstract uses a different network name, update line in docker-compose.yml:
```yaml
unstract-network:
  external: true
  name: YOUR_UNSTRACT_NETWORK_NAME   # ← update this
```

### 3d. Find your network name
```powershell
docker network ls | Select-String unstract
```

## 4. n8n Workflow Configuration (MUST update after import)

After importing `Kosovo_Invoice_Automation_v2.json`:

### Step 1: Create Unstract Credential
- Settings → Credentials → New → HTTP Header Auth
- Name: `Unstract Google Prompt API Key`
- Header Name: `Authorization`
- Header Value: `Bearer YOUR_UNSTRACT_API_KEY`

### Step 2: Update Upload to Unstract node
- Open workflow → click "Upload to Unstract" node
- URL: `http://unstract-backend:8000/deployment/api/YOUR_ORG/YOUR_API_NAME/`
- The default is `mock_org/google_prompt` — change if your org slug differs

### Step 3: Update Poll & Parse Unstract Result node
- Find line: `const UNSTRACT_KEY = 'YOUR_KEY_HERE';`
- Replace with your actual Unstract API key

### Step 4: Activate
- Assign the credential to "Upload to Unstract" node
- Toggle workflow Active ✅

## 5. LB.xlsx — Kosovo VAT Purchase Book

The automation writes to `LB.xlsx` in your invoices folder.
This file MUST exist before running the workflow.
Column structure (rows 1-3 are headers, data starts row 4):
- Column B: Date (Data)
- Column C: Invoice Number (Numri i faturës)
- Column D: Supplier Name (Emri i shitësit)
- Column E: Fiscal Number
- Column F: VAT Number
- Columns G-AD: ATK field codes [31] through [68]
- Column S: Formula =K*0.18 (18% VAT total)
- Column AB: Formula =T*0.08 (8% VAT total)
- Column AC: Formula =S+AB (total deductible VAT)
