#!/usr/bin/env bash
# Installs the cluster add-ons MediSlot depends on:
#   ingress-nginx       - implements the Ingress resource
#   metrics-server      - CPU metrics for the HPA (kind only; EKS gets it as an add-on from Terraform)
#   kube-prometheus-stack - Prometheus Operator, Prometheus, Grafana, Alertmanager
#
# Usage: scripts/bootstrap-cluster.sh eks|kind
set -euo pipefail

PROVIDER="${1:-}"
if [[ "$PROVIDER" != "eks" && "$PROVIDER" != "kind" ]]; then
  echo "usage: $0 eks|kind" >&2
  exit 1
fi
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

INGRESS_NGINX_VERSION=4.15.1
METRICS_SERVER_VERSION=3.14.0
KUBE_PROMETHEUS_STACK_VERSION=92.4.0

echo "==> Namespace"
kubectl apply -f "$ROOT/k8s/namespace.yaml"

if [[ "$PROVIDER" == "eks" ]]; then
  echo "==> gp3 StorageClass (default)"
  kubectl apply -f "$ROOT/k8s/storageclass-gp3.yaml"
  # Demote the legacy gp2 class if it exists so only one default remains.
  kubectl annotate storageclass gp2 storageclass.kubernetes.io/is-default-class=false --overwrite 2>/dev/null || true
fi

echo "==> ingress-nginx"
if [[ "$PROVIDER" == "kind" ]]; then
  INGRESS_ARGS=(
    --set controller.hostPort.enabled=true
    --set controller.service.type=NodePort
    --set-string controller.nodeSelector.ingress-ready=true
    --set "controller.tolerations[0].key=node-role.kubernetes.io/control-plane"
    --set "controller.tolerations[0].operator=Exists"
    --set "controller.tolerations[0].effect=NoSchedule"
  )
else
  INGRESS_ARGS=(
    --set controller.service.type=LoadBalancer
    --set-string "controller.service.annotations.service\.beta\.kubernetes\.io/aws-load-balancer-type=nlb"
    --set-string "controller.service.annotations.service\.beta\.kubernetes\.io/aws-load-balancer-scheme=internet-facing"
  )
fi
helm upgrade --install ingress-nginx ingress-nginx \
  --repo https://kubernetes.github.io/ingress-nginx --version "$INGRESS_NGINX_VERSION" \
  -n ingress-nginx --create-namespace \
  --set controller.metrics.enabled=true \
  "${INGRESS_ARGS[@]}" --wait --timeout 10m

if [[ "$PROVIDER" == "kind" ]]; then
  echo "==> metrics-server"
  helm upgrade --install metrics-server metrics-server \
    --repo https://kubernetes-sigs.github.io/metrics-server/ --version "$METRICS_SERVER_VERSION" \
    -n kube-system \
    --set "args={--kubelet-insecure-tls}" --wait
fi

echo "==> kube-prometheus-stack"
if kubectl get secret -n monitoring kube-prometheus-stack-grafana >/dev/null 2>&1; then
  GRAFANA_PASSWORD="$(kubectl get secret -n monitoring kube-prometheus-stack-grafana -o jsonpath='{.data.admin-password}' | base64 -d)"
else
  GRAFANA_PASSWORD="$(openssl rand -base64 18)"
fi
helm upgrade --install kube-prometheus-stack kube-prometheus-stack \
  --repo https://prometheus-community.github.io/helm-charts --version "$KUBE_PROMETHEUS_STACK_VERSION" \
  -n monitoring --create-namespace \
  -f "$ROOT/monitoring/prometheus-values.yaml" \
  -f "$ROOT/monitoring/grafana-values.yaml" \
  --set grafana.adminPassword="$GRAFANA_PASSWORD" \
  --wait --timeout 15m

echo
echo "Cluster add-ons ready."
echo "Grafana login: admin / (kubectl get secret -n monitoring kube-prometheus-stack-grafana -o jsonpath='{.data.admin-password}' | base64 -d)"
if [[ "$PROVIDER" == "eks" ]]; then
  echo "Ingress address: kubectl get svc -n ingress-nginx ingress-nginx-controller"
fi
