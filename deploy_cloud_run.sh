#!/usr/bin/env bash
# ==============================================================================
# StrataIQ — Google Cloud Run Production Deployment Script (Bash)
# ==============================================================================
# Deploys StrataIQ to Google Cloud Run with Google Cloud Firestore, Gemini 2.5,
# and Google ADK 2.0.
#
# ZERO-SECRET COMMIT POLICY:
# Keys are read dynamically from backend/.env at execution time into process memory.
# No keys are written to disk or console logs.
# ==============================================================================

set -euo pipefail

REGION="${1:-us-central1}"
SERVICE_NAME="${2:-strataiq}"

echo "=========================================================="
echo "  StrataIQ - Google Cloud Run Production Deployment"
echo "=========================================================="

# 1. Verify gcloud CLI is installed
if ! command -v gcloud &> /dev/null; then
    echo "ERROR: 'gcloud' is not installed or not in PATH. Please install Google Cloud SDK."
    exit 1
fi

# 2. Check current GCP Project ID
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || true)
if [ -z "$CURRENT_PROJECT" ] || [ "$CURRENT_PROJECT" = "(unset)" ]; then
    read -rp "Enter your Google Cloud Project ID: " CURRENT_PROJECT
    if [ -z "$CURRENT_PROJECT" ]; then
        echo "ERROR: A valid Google Cloud Project ID is required."
        exit 1
    fi
    gcloud config set project "$CURRENT_PROJECT"
fi
echo "--> Deploying to GCP Project: $CURRENT_PROJECT"

# 3. Read secrets safely from backend/.env into memory
ENV_PATH="$(dirname "$0")/backend/.env"
if [ ! -f "$ENV_PATH" ]; then
    echo "ERROR: Could not find $ENV_PATH. Please ensure backend/.env exists with your API keys."
    exit 1
fi

GEMINI_API_KEY=$(grep -E '^GEMINI_API_KEY=' "$ENV_PATH" | cut -d '=' -f2- | tr -d '"' | tr -d "'" || true)
GEMINI_FLASH_MODEL=$(grep -E '^GEMINI_FLASH_MODEL=' "$ENV_PATH" | cut -d '=' -f2- | tr -d '"' | tr -d "'" || true)
GEMINI_PRO_MODEL=$(grep -E '^GEMINI_PRO_MODEL=' "$ENV_PATH" | cut -d '=' -f2- | tr -d '"' | tr -d "'" || true)
GEMINI_TTS_MODEL=$(grep -E '^GEMINI_TTS_MODEL=' "$ENV_PATH" | cut -d '=' -f2- | tr -d '"' | tr -d "'" || true)
GEMINI_EMBEDDING_MODEL=$(grep -E '^GEMINI_EMBEDDING_MODEL=' "$ENV_PATH" | cut -d '=' -f2- | tr -d '"' | tr -d "'" || true)
TINKER_API_KEY=$(grep -E '^TINKER_API_KEY=' "$ENV_PATH" | cut -d '=' -f2- | tr -d '"' | tr -d "'" || true)
BACKBOARD_API_KEY=$(grep -E '^BACKBOARD_API_KEY=' "$ENV_PATH" | cut -d '=' -f2- | tr -d '"' | tr -d "'" || true)
TINKER_BASE_MODEL=$(grep -E '^TINKER_BASE_MODEL=' "$ENV_PATH" | cut -d '=' -f2- | tr -d '"' | tr -d "'" || true)
GOOGLE_GEMMA_ROUTER_MODEL=$(grep -E '^GOOGLE_GEMMA_ROUTER_MODEL=' "$ENV_PATH" | cut -d '=' -f2- | tr -d '"' | tr -d "'" || true)

[ -z "$GEMINI_FLASH_MODEL" ] && GEMINI_FLASH_MODEL="gemini-3.8-flash"
[ -z "$GEMINI_PRO_MODEL" ] && GEMINI_PRO_MODEL="gemini-3-flash-preview"
[ -z "$GEMINI_TTS_MODEL" ] && GEMINI_TTS_MODEL="gemini-3.8-flash-tts"
[ -z "$GEMINI_EMBEDDING_MODEL" ] && GEMINI_EMBEDDING_MODEL="gemini-embedding-001"
[ -z "$TINKER_BASE_MODEL" ] && TINKER_BASE_MODEL="google/gemma-4-e4b-it"
[ -z "$GOOGLE_GEMMA_ROUTER_MODEL" ] && GOOGLE_GEMMA_ROUTER_MODEL="gemma-4-e4b-it"

# 4. Enable required Google Cloud APIs
echo "--> Enabling required Google Cloud APIs..."
APIS=(
    "run.googleapis.com"
    "cloudbuild.googleapis.com"
    "artifactregistry.googleapis.com"
    "firestore.googleapis.com"
    "aiplatform.googleapis.com"
    "texttospeech.googleapis.com"
    "speech.googleapis.com"
)
for api in "${APIS[@]}"; do
    echo "    - Enabling $api"
    gcloud services enable "$api" --project "$CURRENT_PROJECT" --quiet
done

PROJECT_NUMBER=$(gcloud projects describe "$CURRENT_PROJECT" --format="value(projectNumber)" 2>/dev/null || true)
if [ -n "$PROJECT_NUMBER" ]; then
    COMPUTE_SA="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"
    echo "--> Verifying Cloud Build & Firestore permissions for $COMPUTE_SA..."
    gcloud projects add-iam-policy-binding "$CURRENT_PROJECT" --member="serviceAccount:$COMPUTE_SA" --role="roles/storage.admin" --quiet 2>/dev/null || true
    gcloud projects add-iam-policy-binding "$CURRENT_PROJECT" --member="serviceAccount:$COMPUTE_SA" --role="roles/artifactregistry.writer" --quiet 2>/dev/null || true
    gcloud projects add-iam-policy-binding "$CURRENT_PROJECT" --member="serviceAccount:$COMPUTE_SA" --role="roles/cloudbuild.builds.builder" --quiet 2>/dev/null || true
    gcloud projects add-iam-policy-binding "$CURRENT_PROJECT" --member="serviceAccount:$COMPUTE_SA" --role="roles/datastore.user" --quiet 2>/dev/null || true
fi

# 5. Build --set-env-vars payload
ENV_VARS="GOOGLE_CLOUD_PROJECT=$CURRENT_PROJECT,GOOGLE_API_KEY=$GEMINI_API_KEY,GEMINI_API_KEY=$GEMINI_API_KEY,GEMINI_FLASH_MODEL=$GEMINI_FLASH_MODEL,GEMINI_PRO_MODEL=$GEMINI_PRO_MODEL,GEMINI_TTS_MODEL=$GEMINI_TTS_MODEL,GEMINI_EMBEDDING_MODEL=$GEMINI_EMBEDDING_MODEL,TINKER_API_KEY=$TINKER_API_KEY,BACKBOARD_API_KEY=$BACKBOARD_API_KEY,TINKER_BASE_MODEL=$TINKER_BASE_MODEL,GOOGLE_GEMMA_ROUTER_MODEL=$GOOGLE_GEMMA_ROUTER_MODEL"

# 6. Execute Cloud Run source deployment
echo "--> Building and deploying container to Cloud Run (region: $REGION)..."
echo "    Using --min-instances 1 to eliminate cold starts for hackathon judges."

gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --project "$CURRENT_PROJECT" \
    --region "$REGION" \
    --platform managed \
    --allow-unauthenticated \
    --min-instances 1 \
    --max-instances 10 \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --set-env-vars "$ENV_VARS" \
    --quiet

SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --project "$CURRENT_PROJECT" --region "$REGION" --format 'value(status.url)' 2>/dev/null || true)

echo ""
echo "=========================================================="
echo "  SUCCESS! StrataIQ is live on Google Cloud Run!"
echo "=========================================================="
echo "Live Production URL: $SERVICE_URL"
echo "Health Check:        $SERVICE_URL/health"
echo "API Documentation:   $SERVICE_URL/docs"
echo "SDK Forensic Status: $SERVICE_URL/api/v1/agent/sdk-status"
