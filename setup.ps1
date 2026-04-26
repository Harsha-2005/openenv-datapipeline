# ============================================================
# OpenEnv Data Pipeline — Smart Setup Script (Windows)
# ============================================================
# Usage:
#   .\setup.ps1           — Full smart setup (only installs if needed)
#   .\setup.ps1 -Force    — Force reinstall all dependencies
#   .\setup.ps1 -Run      — Setup + start the server
# ============================================================

param(
    [switch]$Force,
    [switch]$Run
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$VenvDir     = Join-Path $ProjectRoot ".venv"
$HashFile    = Join-Path $ProjectRoot ".deps_hash"
$ReqFile     = Join-Path $ProjectRoot "requirements.txt"
$PythonExe   = Join-Path $VenvDir "Scripts\python.exe"
$PipExe      = Join-Path $VenvDir "Scripts\pip.exe"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   OpenEnv Data Pipeline — Smart Setup           ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Create virtual environment if missing ──────────
if (-not (Test-Path $PythonExe)) {
    Write-Host "📦  Creating virtual environment (.venv)..." -ForegroundColor Yellow
    python -m venv $VenvDir
    Write-Host "✅  Virtual environment created." -ForegroundColor Green
} else {
    Write-Host "✅  Virtual environment already exists." -ForegroundColor Green
}

# ── Step 2: Compute hash of requirements.txt ──────────────
$CurrentHash = (Get-FileHash $ReqFile -Algorithm MD5).Hash
$StoredHash  = ""
if (Test-Path $HashFile) {
    $StoredHash = (Get-Content $HashFile).Trim()
}

# ── Step 3: Install deps only if requirements changed ─────
if ($Force -or ($CurrentHash -ne $StoredHash)) {
    if ($Force) {
        Write-Host "🔄  Force reinstall requested..." -ForegroundColor Yellow
    } else {
        Write-Host "🔄  requirements.txt changed — installing new dependencies..." -ForegroundColor Yellow
    }

    # Use pre-built wheels where possible, skip pydantic strict pin
    & $PipExe install --upgrade pip --quiet
    & $PipExe install `
        "pydantic>=2.10.0" `
        "fastapi>=0.115.0" `
        "uvicorn[standard]>=0.30.6" `
        "pandas>=2.1.0" `
        "httpx>=0.27.2" `
        "openai>=1.51.0" `
        "pyyaml>=6.0.2" `
        "python-dotenv>=1.0.0" `
        "pytest>=8.0.0" `
        "pytest-asyncio>=0.23.0" `
        "websockets>=12.0" `
        "jinja2>=3.1.0"

    if ($LASTEXITCODE -eq 0) {
        # Save hash so next run skips install
        $CurrentHash | Set-Content $HashFile
        Write-Host "✅  Dependencies installed and hash saved." -ForegroundColor Green
    } else {
        Write-Host "❌  Dependency install failed!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "⚡  Dependencies up-to-date (requirements.txt unchanged). Skipping install." -ForegroundColor Green
}

# ── Step 4: Check for .env file ───────────────────────────
$EnvFile = Join-Path $ProjectRoot ".env"
if (-not (Test-Path $EnvFile)) {
    Write-Host ""
    Write-Host "⚠️   No .env file found. Creating a template..." -ForegroundColor Yellow
    @"
# OpenEnv Data Pipeline — Environment Variables
# Copy this file and fill in your values.

# HuggingFace token (required for model inference)
HF_TOKEN=your_huggingface_token_here

# OpenAI API key (optional — for GPT-based agents)
OPENAI_API_KEY=your_openai_key_here

# Server port (default: 7860)
PORT=7860
"@ | Set-Content $EnvFile
    Write-Host "📝  .env template created. Fill in your credentials before running." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Setup complete! To start the server run:      ║" -ForegroundColor Cyan
Write-Host "║                                                  ║" -ForegroundColor Cyan
Write-Host "║   .\.venv\Scripts\python.exe -m uvicorn          ║" -ForegroundColor Cyan
Write-Host "║       app:app --host 0.0.0.0 --port 7860        ║" -ForegroundColor Cyan
Write-Host "║                                                  ║" -ForegroundColor Cyan
Write-Host "║   Or run:  .\setup.ps1 -Run                     ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── Step 5: Optionally start the server ───────────────────
if ($Run) {
    Write-Host "🚀  Starting server on http://localhost:7860 ..." -ForegroundColor Green
    Write-Host "    Dashboard → http://localhost:7860/dashboard" -ForegroundColor Cyan
    Write-Host "    API Docs  → http://localhost:7860/docs" -ForegroundColor Cyan
    Write-Host ""
    & $PythonExe -m uvicorn app:app --host 0.0.0.0 --port 7860 --reload
}
