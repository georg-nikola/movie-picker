#!/bin/bash
# Creates Kubernetes secrets for movie-picker-api and postgresql.
# Run this once before deploying. Values are NOT stored in git.
#
# Usage:
#   ./scripts/create-k8s-secrets.sh
#
# Required env vars (or will prompt):
#   DB_PASSWORD       - PostgreSQL password for moviepicker user
#   JWT_SECRET        - Random string for signing JWTs (use: openssl rand -hex 32)
#   SMTP_USER         - Gmail address
#   SMTP_PASSWORD     - Gmail App Password (16 chars, no spaces)
#   SMTP_FROM         - Sender address (usually same as SMTP_USER)

set -e

CONTEXT="admin@home-talos-k8s-cluster"
NAMESPACE="default"

read_secret() {
  local var="$1"
  local prompt="$2"
  if [ -z "${!var}" ]; then
    read -rsp "$prompt: " value
    echo
    eval "$var='$value'"
  fi
}

read_secret DB_PASSWORD       "PostgreSQL password for moviepicker user"
read_secret JWT_SECRET        "JWT secret (or press enter to generate)"
read_secret SMTP_USER         "Gmail SMTP user (email address)"
read_secret SMTP_PASSWORD     "Gmail App Password"
read_secret SMTP_FROM         "Sender email (leave empty to use SMTP_USER)"

if [ -z "$JWT_SECRET" ]; then
  JWT_SECRET=$(openssl rand -hex 32)
  echo "Generated JWT_SECRET: $JWT_SECRET"
fi

if [ -z "$SMTP_FROM" ]; then
  SMTP_FROM="$SMTP_USER"
fi

DB_URL="postgresql+asyncpg://moviepicker:${DB_PASSWORD}@postgresql.${NAMESPACE}.svc.cluster.local:5432/moviepicker"

echo ""
echo "Creating secret: postgresql-credentials"
kubectl --context "$CONTEXT" -n "$NAMESPACE" create secret generic postgresql-credentials \
  --from-literal=password="$DB_PASSWORD" \
  --from-literal=postgres-password="$DB_PASSWORD" \
  --dry-run=client -o yaml | kubectl --context "$CONTEXT" apply -f -

echo "Creating secret: movie-picker-api-secrets"
kubectl --context "$CONTEXT" -n "$NAMESPACE" create secret generic movie-picker-api-secrets \
  --from-literal=DATABASE_URL="$DB_URL" \
  --from-literal=JWT_SECRET="$JWT_SECRET" \
  --from-literal=SMTP_HOST="smtp.gmail.com" \
  --from-literal=SMTP_PORT="587" \
  --from-literal=SMTP_USER="$SMTP_USER" \
  --from-literal=SMTP_PASSWORD="$SMTP_PASSWORD" \
  --from-literal=SMTP_FROM="$SMTP_FROM" \
  --dry-run=client -o yaml | kubectl --context "$CONTEXT" apply -f -

echo ""
echo "Secrets created successfully."
echo "Next steps:"
echo "  1. Apply ArgoCD apps: kubectl --context $CONTEXT apply -f talos-configs repo argocd manifests"
echo "  2. Or deploy directly:"
echo "     helm upgrade --install postgresql helm/postgresql --kube-context $CONTEXT -n $NAMESPACE"
echo "     helm upgrade --install movie-picker-api helm/movie-picker-api --kube-context $CONTEXT -n $NAMESPACE"
