<#
==============================================================================
StrataIQ — Google Cloud Run Production Deployment Script
==============================================================================
Deploys StrataIQ to Google Cloud Run with Google Cloud Firestore, Gemini 2.5,
and Google ADK 2.0.

ZERO-SECRET COMMIT POLICY:
Keys are read dynamically from backend/.env at execution time into process memory.
No keys are written to disk or console logs.
==============================================================================
#>

[CmdletBinding()]
param(
    [string]$Region = "us-central1",
    [string]$ServiceName = "strataiq"
)

$ErrorActionPreference = "Continue"
$env:CLOUDSDK_CORE_VERBOSITY = "warning"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  StrataIQ - Google Cloud Run Production Deployment" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Verify gcloud CLI is installed
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Error "Google Cloud SDK ('gcloud') is not installed or not in PATH. Please install it from https://cloud.google.com/sdk"
    exit 1
}

# 2. Check current GCP Project ID
$CurrentProject = (gcloud config get-value project 2>$null)
if ($CurrentProject) {
    $CurrentProject = $CurrentProject.Trim()
}
if ([string]::IsNullOrWhiteSpace($CurrentProject) -or $CurrentProject -eq "(unset)") {
    $CurrentProject = Read-Host "Enter your Google Cloud Project ID"
    if ([string]::IsNullOrWhiteSpace($CurrentProject)) {
        Write-Error "A valid Google Cloud Project ID is required."
        exit 1
    }
    gcloud config set project $CurrentProject
}
Write-Host "--> Deploying to GCP Project: $CurrentProject" -ForegroundColor Green

# 3. Read secrets safely from backend/.env into memory
$EnvPath = Join-Path $PSScriptRoot "backend\.env"
if (-not (Test-Path $EnvPath)) {
    Write-Error "Could not find $EnvPath. Please ensure backend/.env exists with your API keys."
    exit 1
}

$EnvVars = @{}
Get-Content $EnvPath | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
        $parts = $line.Split("=", 2)
        $key = $parts[0].Trim()
        $val = $parts[1].Trim().Trim('"').Trim("'")
        $EnvVars[$key] = $val
    }
}

$GeminiKey = if ($EnvVars.ContainsKey("GEMINI_API_KEY")) { $EnvVars["GEMINI_API_KEY"] } else { "" }
$TinkerKey = if ($EnvVars.ContainsKey("TINKER_API_KEY")) { $EnvVars["TINKER_API_KEY"] } else { "" }
$BackboardKey = if ($EnvVars.ContainsKey("BACKBOARD_API_KEY")) { $EnvVars["BACKBOARD_API_KEY"] } else { "" }
$TinkerModel = if ($EnvVars.ContainsKey("TINKER_BASE_MODEL")) { $EnvVars["TINKER_BASE_MODEL"] } else { "google/gemma-4-e4b-it" }
$RouterModel = if ($EnvVars.ContainsKey("GOOGLE_GEMMA_ROUTER_MODEL")) { $EnvVars["GOOGLE_GEMMA_ROUTER_MODEL"] } else { "gemma-4-e4b-it" }

if (-not $GeminiKey) {
    Write-Warning "GEMINI_API_KEY is not set in backend/.env. AI agent and voice synthesis will run in deterministic fallback mode."
}

# 4. Enable required Google Cloud APIs
Write-Host "--> Enabling required Google Cloud APIs..." -ForegroundColor Yellow
$RequiredApis = @(
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "firestore.googleapis.com",
    "aiplatform.googleapis.com",
    "texttospeech.googleapis.com",
    "speech.googleapis.com"
)
foreach ($api in $RequiredApis) {
    Write-Host "    - Enabling $api"
    gcloud services enable $api --project $CurrentProject --quiet
}

# Ensure default compute service account has Cloud Build & Storage permissions
$ProjectNumber = (gcloud projects describe $CurrentProject --format="value(projectNumber)" 2>$null)
if ($ProjectNumber) {
    $ProjectNumber = $ProjectNumber.Trim()
    $ComputeSA = "$ProjectNumber-compute@developer.gserviceaccount.com"
    Write-Host "--> Verifying Cloud Build permissions for $ComputeSA..." -ForegroundColor Yellow
    gcloud projects add-iam-policy-binding $CurrentProject --member="serviceAccount:$ComputeSA" --role="roles/storage.admin" --quiet 2>$null | Out-Null
    gcloud projects add-iam-policy-binding $CurrentProject --member="serviceAccount:$ComputeSA" --role="roles/artifactregistry.writer" --quiet 2>$null | Out-Null
    gcloud projects add-iam-policy-binding $CurrentProject --member="serviceAccount:$ComputeSA" --role="roles/cloudbuild.builds.builder" --quiet 2>$null | Out-Null
    gcloud projects add-iam-policy-binding $CurrentProject --member="serviceAccount:$ComputeSA" --role="roles/datastore.user" --quiet 2>$null | Out-Null
}

# 5. Build --set-env-vars payload (keys securely passed from memory)
$EnvVarList = @(
    "GOOGLE_CLOUD_PROJECT=$CurrentProject",
    "GOOGLE_API_KEY=$GeminiKey",
    "GEMINI_API_KEY=$GeminiKey",
    "GEMINI_FLASH_MODEL=$(if ($EnvVars.ContainsKey('GEMINI_FLASH_MODEL')) { $EnvVars['GEMINI_FLASH_MODEL'] } else { 'gemini-3.8-flash' })",
    "GEMINI_PRO_MODEL=$(if ($EnvVars.ContainsKey('GEMINI_PRO_MODEL')) { $EnvVars['GEMINI_PRO_MODEL'] } else { 'gemini-3-flash-preview' })",
    "GEMINI_TTS_MODEL=$(if ($EnvVars.ContainsKey('GEMINI_TTS_MODEL')) { $EnvVars['GEMINI_TTS_MODEL'] } else { 'gemini-3.8-flash-tts' })",
    "GEMINI_EMBEDDING_MODEL=$(if ($EnvVars.ContainsKey('GEMINI_EMBEDDING_MODEL')) { $EnvVars['GEMINI_EMBEDDING_MODEL'] } else { 'gemini-embedding-001' })",
    "TINKER_API_KEY=$TinkerKey",
    "BACKBOARD_API_KEY=$BackboardKey",
    "TINKER_BASE_MODEL=$TinkerModel",
    "GOOGLE_GEMMA_ROUTER_MODEL=$RouterModel"
)
$EnvVarString = ($EnvVarList -join ",")

# 6. Execute Cloud Run source deployment
Write-Host "--> Building and deploying container to Cloud Run (region: $Region)..." -ForegroundColor Yellow
Write-Host "    Using --min-instances 1 to eliminate cold starts for hackathon judges." -ForegroundColor Green

gcloud run deploy $ServiceName `
    --source . `
    --project $CurrentProject `
    --region $Region `
    --platform managed `
    --allow-unauthenticated `
    --min-instances 1 `
    --max-instances 10 `
    --memory 2Gi `
    --cpu 2 `
    --timeout 300 `
    --set-env-vars "$EnvVarString" `
    --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host "  SUCCESS! StrataIQ is live on Google Cloud Run!" -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Green
    $ServiceUrl = (gcloud run services describe $ServiceName --project $CurrentProject --region $Region --format 'value(status.url)' 2>$null)
    if ($ServiceUrl) { $ServiceUrl = $ServiceUrl.Trim() }
    Write-Host "Live Production URL: $ServiceUrl" -ForegroundColor Cyan
    Write-Host "Health Check:        $ServiceUrl/health" -ForegroundColor Cyan
    Write-Host "API Documentation:   $ServiceUrl/docs" -ForegroundColor Cyan
    Write-Host "SDK Forensic Status: $ServiceUrl/api/v1/agent/sdk-status" -ForegroundColor Cyan
} else {
    Write-Error "Deployment failed. Check the Google Cloud Build and Cloud Run logs above."
}
