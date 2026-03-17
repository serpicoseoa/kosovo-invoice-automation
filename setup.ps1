# ================================================================
# Kosovo Invoice Automation — One-Click Setup Script
# Run this from the repo root after cloning
# Requires: Docker Desktop, Git, Python 3.x
# ================================================================

param(
    [string]$InvoicesPath = "C:\Users\$env:USERNAME\Dropbox\Test\Invoices",
    [string]$ScriptsPath  = "C:\invoice-automation\scripts",
    [string]$BankPath     = "C:\Users\$env:USERNAME\Dropbox\Test\BankStatements"
)

Write-Host "====== Kosovo Invoice Automation Setup ======" -ForegroundColor Cyan

# 1. Create folder structure
Write-Host "`n[1/6] Creating folder structure..." -ForegroundColor Yellow
$folders = @(
    $InvoicesPath,
    "$InvoicesPath\Completed",
    "$InvoicesPath\Review",
    "$InvoicesPath\Review\OCR_Failed",
    "$InvoicesPath\Review\Duplicates",
    $ScriptsPath,
    "C:\invoice-automation"
)
foreach ($f in $folders) {
    New-Item -ItemType Directory -Force -Path $f | Out-Null
    Write-Host "  Created: $f"
}

# 2. Copy scripts
Write-Host "`n[2/6] Copying Python scripts..." -ForegroundColor Yellow
Copy-Item "$PSScriptRoot\scripts\*.py"           $ScriptsPath -Force
Copy-Item "$PSScriptRoot\scripts\requirements.txt" $ScriptsPath -Force
Write-Host "  Scripts copied to $ScriptsPath"

# 3. Copy Docker setup
Write-Host "`n[3/6] Setting up Docker configuration..." -ForegroundColor Yellow
$n8nSetup = "C:\Users\$env:USERNAME\Desktop\n8n-setup"
New-Item -ItemType Directory -Force -Path $n8nSetup | Out-Null
Copy-Item "$PSScriptRoot\n8n-setup\Dockerfile"        $n8nSetup -Force
Copy-Item "$PSScriptRoot\n8n-setup\docker-compose.yml" $n8nSetup -Force
Copy-Item "$PSScriptRoot\n8n-setup\.env.template"      "$n8nSetup\.env.template" -Force
Write-Host "  Docker files placed in: $n8nSetup"

# 4. Create .env from template
Write-Host "`n[4/6] Creating .env file..." -ForegroundColor Yellow
if (-not (Test-Path "$n8nSetup\.env")) {
    $key = python -c "import secrets; print(secrets.token_hex(32))" 2>$null
    if (-not $key) { $key = [System.Guid]::NewGuid().ToString().Replace('-','') + [System.Guid]::NewGuid().ToString().Replace('-','').Substring(0,8) }
    $envContent = Get-Content "$n8nSetup\.env.template" -Raw
    $envContent = $envContent -replace "GENERATE_A_RANDOM_32_CHAR_HEX_KEY", $key
    $envContent = $envContent -replace "C:/Users/YOUR_USERNAME", "C:/Users/$env:USERNAME"
    Set-Content "$n8nSetup\.env" $envContent
    Write-Host "  .env created at: $n8nSetup\.env"
    Write-Host "  *** IMPORTANT: Edit .env to set your passwords and API keys ***" -ForegroundColor Red
} else {
    Write-Host "  .env already exists — skipping" -ForegroundColor Green
}

# 5. Build Docker image
Write-Host "`n[5/6] Building Docker image (this takes 2-3 minutes)..." -ForegroundColor Yellow
Set-Location $n8nSetup
docker-compose build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker build failed. Check Docker Desktop is running." -ForegroundColor Red
    exit 1
}

# 6. Start n8n
Write-Host "`n[6/6] Starting n8n..." -ForegroundColor Yellow
docker-compose up -d
Start-Sleep -Seconds 20
$health = docker ps --filter "name=n8n-setup-n8n-1" --format "{{.Status}}"
if ($health -like "*healthy*" -or $health -like "*Up*") {
    Write-Host "`n====== SETUP COMPLETE ======" -ForegroundColor Green
    Write-Host "n8n is running at: http://localhost:5678" -ForegroundColor Cyan
    Write-Host "`nNext steps:" -ForegroundColor Yellow
    Write-Host "  1. Open http://localhost:5678 and log in"
    Write-Host "  2. Import workflow: n8n-setup\Kosovo_Invoice_Automation_v2.json"
    Write-Host "  3. Create credential 'Unstract Google Prompt API Key' (HTTP Header Auth)"
    Write-Host "     Header: Authorization | Value: Bearer YOUR_UNSTRACT_API_KEY"
    Write-Host "  4. Open 'Upload to Unstract' node and select the credential"
    Write-Host "  5. Update Unstract URL in 'Upload to Unstract' node if org name differs"
    Write-Host "  6. Activate the workflow"
} else {
    Write-Host "n8n may not be healthy yet. Check: docker ps" -ForegroundColor Yellow
}
