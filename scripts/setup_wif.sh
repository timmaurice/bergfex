#!/bin/bash
set -e

# Konfiguration
PROJECT_ID="bergfex-481612"
SERVICE_ACCOUNT_NAME="github-actions"
POOL_NAME="github-actions-pool"
PROVIDER_NAME="github-provider"
REPO="Alexander-Heinz/bergfex-scraper"
LOCATION="global"

SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "🚀 Starting Workload Identity Federation Setup for $PROJECT_ID..."

# Get project number
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")

# 1. Service Account erstellen
if ! gcloud iam service-accounts describe "$SERVICE_ACCOUNT_EMAIL" --project="$PROJECT_ID" &>/dev/null; then
    echo "Creating Service Account..."
    gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
        --display-name="GitHub Actions Deployer" \
        --project="$PROJECT_ID"
else
    echo "✓ Service Account exists."
fi

# 2. IAM Rollen zuweisen
echo "Assigning IAM roles..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/editor" \
    --condition=None --quiet || true

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/iam.serviceAccountUser" \
    --condition=None --quiet || true

# 3. Workload Identity Pool erstellen
if ! gcloud iam workload-identity-pools describe "$POOL_NAME" --project="$PROJECT_ID" --location="$LOCATION" &>/dev/null; then
    echo "Creating Identity Pool..."
    gcloud iam workload-identity-pools create "$POOL_NAME" \
        --project="$PROJECT_ID" \
        --location="$LOCATION" \
        --display-name="GitHub Actions Pool"
else
    echo "✓ Identity Pool exists."
fi

# 4. Workload Identity Provider erstellen (mit attribute-condition!)
if ! gcloud iam workload-identity-pools providers describe "$PROVIDER_NAME" \
    --project="$PROJECT_ID" \
    --location="$LOCATION" \
    --workload-identity-pool="$POOL_NAME" &>/dev/null; then
    echo "Creating Identity Provider..."
    gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_NAME" \
        --project="$PROJECT_ID" \
        --location="$LOCATION" \
        --workload-identity-pool="$POOL_NAME" \
        --display-name="GitHub Provider" \
        --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
        --attribute-condition="assertion.repository=='${REPO}'" \
        --issuer-uri="https://token.actions.githubusercontent.com"
else
    echo "✓ Identity Provider exists."
fi

# 5. Service Account Binding
echo "Binding Service Account to GitHub Repo..."
MEMBER="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/${LOCATION}/workloadIdentityPools/${POOL_NAME}/attribute.repository/${REPO}"

gcloud iam service-accounts add-iam-policy-binding "$SERVICE_ACCOUNT_EMAIL" \
    --project="$PROJECT_ID" \
    --role="roles/iam.workloadIdentityUser" \
    --member="$MEMBER" --quiet || true

echo ""
echo "✅ Setup Complete!"
echo "---------------------------------------------------"
echo "GitHub Repository Secrets (Settings → Secrets):"
echo ""
echo "GCP_PROJECT_ID:"
echo "  $PROJECT_ID"
echo ""
echo "GCP_SERVICE_ACCOUNT:"
echo "  $SERVICE_ACCOUNT_EMAIL"
echo ""
echo "GCP_WORKLOAD_IDENTITY_PROVIDER:"
echo "  projects/${PROJECT_NUMBER}/locations/${LOCATION}/workloadIdentityPools/${POOL_NAME}/providers/${PROVIDER_NAME}"
echo "---------------------------------------------------"
