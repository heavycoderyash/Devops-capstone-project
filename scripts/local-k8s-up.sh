#!/usr/bin/env bash
# One-shot local Kubernetes rehearsal on kind:
# cluster -> add-ons -> build & load images -> helm install -> http://medislot.local
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLUSTER=medislot

if ! kind get clusters | grep -qx "$CLUSTER"; then
  kind create cluster --config "$ROOT/k8s/local/kind-cluster.yaml"
fi
kubectl config use-context "kind-$CLUSTER"

"$ROOT/scripts/bootstrap-cluster.sh" kind

echo "==> Building images"
docker build -t medislot-backend:local "$ROOT/backend"
docker build -t medislot-frontend:local "$ROOT/frontend"
kind load docker-image medislot-backend:local medislot-frontend:local --name "$CLUSTER"

echo "==> Deploying MediSlot"
# Reuse the existing DB password on re-runs so the Postgres volume stays readable.
DB_PASSWORD="$(kubectl get secret -n medislot medislot-db -o jsonpath='{.data.POSTGRES_PASSWORD}' 2>/dev/null | base64 -d || true)"
DB_PASSWORD="${DB_PASSWORD:-$(openssl rand -hex 16)}"
helm upgrade --install medislot "$ROOT/helm/medislot" -n medislot \
  -f "$ROOT/helm/medislot/values-dev.yaml" \
  --set postgres.password="$DB_PASSWORD" \
  --set monitoring.serviceMonitor.enabled=true \
  --set monitoring.grafanaDashboard.enabled=true \
  --wait --timeout 10m

kubectl get pods,svc,ingress,hpa -n medislot
grep -q "medislot.local" /etc/hosts || echo "Add this to /etc/hosts:  127.0.0.1 medislot.local"
echo "Open http://medislot.local"
