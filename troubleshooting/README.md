# Troubleshooting lab

Three deliberately broken manifests for the live failure demo. Each one breaks
a different layer, and each has a different first command that finds it.

| # | Manifest | Symptom | Layer |
|---|----------|---------|-------|
| 1 | `01-broken-image.yaml` | `ImagePullBackOff` | Registry / image tag |
| 2 | `02-broken-service.yaml` | Service exists, requests time out | Service selector / ports |
| 3 | `03-crashloop-bad-database-url.yaml` | `CrashLoopBackOff` | App configuration |

General workflow: **get → describe → events → logs → fix → verify**.

---

## 1. ImagePullBackOff

```bash
kubectl apply -f troubleshooting/01-broken-image.yaml
kubectl get pods -n medislot -l app=medislot-broken-image          # ErrImagePull -> ImagePullBackOff
kubectl describe pod -n medislot -l app=medislot-broken-image      # Events: "...:does-not-exist: not found"
kubectl get events -n medislot --sort-by=.lastTimestamp | tail
```

**Root cause:** the tag `does-not-exist` was never pushed. (Other common causes:
private GHCR package without an `imagePullSecret`, typo in the registry/owner, wrong CPU architecture.)

**Fix:** point at a tag CI actually pushed (the commit SHA):

```bash
kubectl set image deploy/medislot-broken-image -n medislot \
  backend=ghcr.io/heavycoderyash/medislot-backend:<commit-sha>
```

## 2. Service with no endpoints

```bash
kubectl apply -f troubleshooting/02-broken-service.yaml
kubectl get endpointslices -n medislot -l kubernetes.io/service-name=medislot-api-broken   # no endpoints
kubectl get pods -n medislot --show-labels | grep backend
kubectl describe svc medislot-api-broken -n medislot
```

**Root cause (two bugs):**
1. `selector` uses `app.kubernetes.io/name: medislot-api`, but backend Pods are labelled `medislot-backend` → zero endpoints.
2. `targetPort: 8080`, but uvicorn listens on `8000` → even with the right selector, connections are refused.

**Fix:**

```bash
kubectl patch svc medislot-api-broken -n medislot --type merge -p \
  '{"spec":{"selector":{"app.kubernetes.io/name":"medislot-backend"},"ports":[{"port":8000,"targetPort":8000}]}}'
kubectl get endpointslices -n medislot -l kubernetes.io/service-name=medislot-api-broken   # now lists Pod IPs
```

Lesson: a Service finds Pods **only** through labels. No matching labels → no endpoints → no traffic.

## 3. CrashLoopBackOff from bad configuration

```bash
kubectl apply -f troubleshooting/03-crashloop-bad-database-url.yaml
kubectl get pods -n medislot -l app=medislot-broken-config          # Error -> CrashLoopBackOff, RESTARTS climbing
kubectl logs -n medislot -l app=medislot-broken-config --previous   # psycopg OperationalError: cannot connect to host "postgres"
```

**Root cause:** `DATABASE_URL` points at host `postgres`, but the in-cluster
database Service is `medislot-postgres`; the password is wrong too. Alembic fails at startup, so the container exits.

**Fix:** use the chart-managed Secret instead of a hand-written URL:

```bash
kubectl set env deploy/medislot-broken-config -n medislot DATABASE_URL- \
  && kubectl patch deploy medislot-broken-config -n medislot --type json -p \
  '[{"op":"add","path":"/spec/template/spec/containers/0/envFrom","value":[{"secretRef":{"name":"medislot-db"}}]}]'
```

Lesson: `describe` shows *that* a container restarts; `logs --previous` shows *why*.

## Clean up

```bash
kubectl delete -f troubleshooting/ --ignore-not-found
```
