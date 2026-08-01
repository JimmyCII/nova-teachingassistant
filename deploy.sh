#!/bin/bash
set -e

# Nova Voice Console - Cloud Run Deployment Script

echo "Deploying Nova Voice Console to Cloud Run..."

# ==============================================================================
# JUDGING SAFETY GATES ("BLAST RADIUS" CONTAINMENT)
# ==============================================================================
# Because this application is a live Gemini Voice WebSocket, we have implemented
# several safety gates for the Kaggle judging window:
#
# 1. Scaling Caps (Code): The deployment includes --min-instances=0 and 
#    --max-instances=2. This physically prevents scale-out billing spikes if the 
#    URL is leaked.
# 2. Token Auth (Code): The app is exposed to the internet (--allow-unauthenticated),
#    but access to the WebSocket is strictly guarded by the CONSOLE_TOKEN in the URL.
# 3. Disposable API Key (Manual): This is deployed using a disposable 
#    Kaggle_Judging_Key generated in AI Studio, which will be revoked on July 7th.
# 4. Budget Alert (Manual): A $5.00 hard budget alert is set in the GCP Console.
# 5. No PII in repo (Code): Recipient emails are pulled from Secret Manager
#    (KARRIE_EMAIL, ADMIN_EMAIL, SENDER_EMAIL) so no personal addresses are
#    committed. Create them once:
#      printf 'addr@example.com' | gcloud secrets create KARRIE_EMAIL --data-file=-
#    (repeat for ADMIN_EMAIL, SENDER_EMAIL).
# ==============================================================================

# You must set your GCP project id here if not already configured in gcloud
# gcloud config set project [YOUR_PROJECT_ID]

gcloud run deploy nova-voice-console \
    --source . \
    --region us-central1 \
    --allow-unauthenticated \
    --timeout 3600 \
    --memory 512Mi \
    --min-instances 0 \
    --max-instances 2 \
    --set-secrets="GOOGLE_API_KEY=GOOGLE_API_KEY:latest,CONSOLE_TOKEN=CONSOLE_TOKEN:latest,KARRIE_EMAIL=KARRIE_EMAIL:latest,ADMIN_EMAIL=ADMIN_EMAIL:latest,SENDER_EMAIL=SENDER_EMAIL:latest,NOVA_DRIVE_TOKEN_JSON=NOVA_DRIVE_TOKEN_JSON:latest" \
    --set-env-vars="NOVA_LIVE_MODEL=gemini-3.1-flash-live-preview"

echo "Deployment complete!"
