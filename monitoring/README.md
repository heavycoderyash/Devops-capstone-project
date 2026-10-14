# Monitoring

| File | Purpose |
|------|---------|
| `prometheus-values.yaml` | kube-prometheus-stack: scrape ServiceMonitors from all namespaces, MediSlot alert rules |
| `grafana-values.yaml` | Grafana: dashboard sidecar watches all namespaces |
| `../helm/medislot/files/medislot-dashboard.json` | MediSlot dashboard (shipped by the app chart as a ConfigMap; can also be imported manually) |

## How the pieces connect

```text
FastAPI /metrics  <--scrape--  Prometheus  <--query--  Grafana
       ^                          ^                       ^
  Service port "http"      ServiceMonitor            ConfigMap labelled
  (medislot chart)         (medislot chart)          grafana_dashboard=1
```

## Install

`scripts/bootstrap-cluster.sh` does this for you. Manually:

```bash
helm upgrade --install kube-prometheus-stack kube-prometheus-stack \
  --repo https://prometheus-community.github.io/helm-charts --version 92.4.0 \
  -n monitoring --create-namespace \
  -f monitoring/prometheus-values.yaml -f monitoring/grafana-values.yaml \
  --set grafana.adminPassword="$(openssl rand -base64 18)"
```

Then deploy MediSlot with `monitoring.serviceMonitor.enabled=true` and
`monitoring.grafanaDashboard.enabled=true` (already on in `values-prod.yaml`).

## Open the UIs

```bash
# Prometheus -> Status -> Targets: serviceMonitor/medislot/medislot-backend should be UP
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090

# Grafana -> Dashboards -> "MediSlot - Application Overview"   (user: admin)
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3001:80
kubectl get secret -n monitoring kube-prometheus-stack-grafana -o jsonpath='{.data.admin-password}' | base64 -d; echo
```

## Useful PromQL

```promql
sum by (handler) (rate(http_requests_total{namespace="medislot"}[1m]))              # traffic per endpoint
histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket{namespace="medislot"}[5m])))  # p95 latency
sum(rate(http_requests_total{namespace="medislot",status="5xx"}[5m]))               # errors
sum by (specialty) (increase(medislot_appointments_booked_total[1h]))               # business metric
```
