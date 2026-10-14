# Capstone submission guide

Everything in the repo is done. What remains needs **your** AWS account, GitHub account and screen:
run the steps below in order and save each screenshot into `docs/screenshots/` with the file name shown.

## Rubric → where it lives

| Module | Evidence in repo |
|--------|------------------|
| M1 App | `backend/app/`, `backend/alembic/versions/0001_*.py` + `0002_*.py`, `frontend/src/`, `docker-compose.yml` |
| M2 Tests | `backend/tests/` (22 tests, 3 files), `backend/tests/conftest.py`, `backend/pytest.ini` |
| M3 Git | `.gitignore` (covers `.env`, `__pycache__`, `node_modules`, `.venv`) |
| M4 Docker | `backend/Dockerfile` (non-root uid 10001), `frontend/Dockerfile` (Node → unprivileged Nginx) |
| M5 CI/CD | `.github/workflows/ci-cd.yml` (push to main, pytest gate, frontend build, both images, GHCR, SHA tags) |
| M6 Trivy | `build-scan-push` job: SARIF upload + gate with `exit-code: 1` on HIGH/CRITICAL |
| M7 Terraform | `terraform/*.tf`, `terraform/terraform.tfvars.example` |
| M8 K8s/Helm | `k8s/namespace.yaml`, `helm/medislot/` (Chart, values, templates, Ingress, HPA) |
| M9 Observability | `/metrics`, `monitoring/prometheus-values.yaml`, `monitoring/grafana-values.yaml`, dashboard JSON |
| M10 Docs | `README.md`, this file, `troubleshooting/README.md` |

---

## Step 1 — Local app (M1, M2, M4)

```bash
cd backend && python3.12 -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt
pytest -v                                         # 📸 m2-pytest.png
cd .. && docker compose up --build                # 📸 m4-compose-up.png
```

Open http://localhost:3000, book two appointments, check one in → 📸 `m1-app-dashboard.png`.
Narrow the window to phone width → 📸 `m1-app-mobile.png` (shows the responsive layout).
`curl -s localhost:8000/metrics | head -40` → 📸 `m9-metrics-endpoint.png`

## Step 2 — GitHub (M3, M5, M6)

```bash
git push -u origin main
```

- Actions tab → the green run → 📸 `m5-pipeline-green.png` (copy the run URL into the submission form)
- Open a `Build + scan` job → expand **Trivy gate** → 📸 `m6-trivy-output.png`
- Profile → Packages → `medislot-backend` → 📸 `m5-ghcr-sha-tags.png`; then set **both** packages to *Public*
- `git log --oneline` → 📸 `m3-commit-history.png`

## Step 3 — AWS (M7)

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan -out tfplan                        # 📸 m7-terraform-plan.png
terraform apply tfplan
$(terraform output -raw configure_kubectl)
terraform output                                  # copy cluster_name + github_actions_role_arn
```

AWS Console (region **ap-southeast-2**): VPC → Your VPCs → `medislot-dev-vpc` 📸 `m7-aws-vpc.png`;
EKS → Clusters → `medislot-dev` → Compute tab 📸 `m7-aws-eks.png`.

Add GitHub repo **variables** `EKS_CLUSTER_NAME`, `AWS_REGION`, `AWS_DEPLOY_ROLE_ARN` and **secret**
`POSTGRES_PASSWORD` (Settings → Secrets and variables → Actions).

## Step 4 — Kubernetes (M8, M9)

```bash
scripts/bootstrap-cluster.sh eks
SHA=$(git rev-parse HEAD)
helm upgrade --install medislot ./helm/medislot -n medislot -f helm/medislot/values-prod.yaml \
  --set backend.image.tag=$SHA --set frontend.image.tag=$SHA \
  --set postgres.password='<same value as the POSTGRES_PASSWORD secret>'

kubectl get pods -n medislot          # 📸 m8-pods-running.png
kubectl get svc -n medislot           # 📸 m8-services.png
helm list -n medislot                 # 📸 m8-helm-list.png
kubectl get ingress -n medislot
kubectl get svc ingress-nginx-controller -n ingress-nginx    # EXTERNAL-IP hostname
```

Open `http://<EXTERNAL-IP hostname>/` → 📸 `m8-app-via-ingress.png`
(the NLB DNS name can take 2–3 minutes to resolve).

```bash
kubectl apply -f scripts/load-generator.yaml
kubectl get hpa -n medislot -w        # 📸 m8-hpa-scaling.png once REPLICAS > 2
kubectl delete -f scripts/load-generator.yaml
```

Prometheus → `kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090` →
http://localhost:9090/targets, filter "medislot" → 📸 `m9-prometheus-targets-up.png`

Grafana → `kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3001:80` →
http://localhost:3001 (admin / password from `monitoring/README.md`) → Dashboards → *MediSlot -
Application Overview* (run the load generator first so panels have data) → 📸 `m9-grafana-dashboard.png`

## Step 5 — Teardown (M7)

Follow README section 9, then `terraform destroy` → 📸 `m7-terraform-destroy.png`.

---

## M6 written explanation (adapt to your actual run)

> Trivy scanned both container images built by the pipeline: the operating-system packages of the
> Debian-based Python image and the Alpine-based Nginx image, plus every Python package installed in the
> backend image. The pipeline fails if it finds a HIGH or CRITICAL vulnerability that already has a fix
> available. While building the project, the first scan of the backend image failed on 4 HIGH CVEs
> (e.g. CVE-2025-47273, a path-traversal bug in setuptools, and two urllib3 CVEs). All of them came from
> libraries vendored inside `pip`, not from the application's own code, so I removed `pip` from the final
> runtime image (it is not needed once dependencies are installed). The scan has been clean since. A clean
> result means no *known, fixable* HIGH/CRITICAL CVEs at scan time. It is not a guarantee of security,
> which is why the pipeline also uses non-root containers, least-privilege tokens and OIDC instead of
> stored keys.

---

## Live demo script (M10, ~10 minutes)

1. **App** — open the Ingress URL and book an appointment. Try to double-book the same doctor and slot →
   "Doctor already has an appointment in this time slot" (HTTP 409).
2. **API** — `/docs` on a port-forward to the backend: run GET /api/appointments/stats.
3. **Database** — `kubectl exec -n medislot medislot-postgres-0 -- psql -U medislot -c "select * from appointments"`
4. **Change + commit** — e.g. edit the sidebar callout text in `frontend/src/components/Sidebar.jsx`:
   `git commit -am "Update front-desk tip on sidebar" && git push`
5. **Pipeline** — Actions tab: tests → build → Trivy → push → deploy (about 6–8 minutes).
6. **Registry** — the new SHA tag appears in GHCR.
7. **Rollout** — `kubectl get pods -n medislot -w` shows new pods replacing old ones with zero downtime
   (`maxUnavailable: 0`); refresh the browser to see the change.
   `kubectl get deploy medislot-frontend -n medislot -o jsonpath='{..image}'` shows the commit SHA.
8. **Terraform** — walk through `terraform/main.tf` (VPC module → EKS module → add-ons → Pod Identity).
9. **Helm** — `helm history medislot -n medislot`; optionally `helm rollback medislot <rev> -n medislot`.
10. **HPA** — apply the load generator and watch replicas climb, alongside the Grafana *Backend pods* panel.
11. **Failure** — `kubectl apply -f troubleshooting/02-broken-service.yaml` and diagnose it live
    (see `troubleshooting/README.md`).
