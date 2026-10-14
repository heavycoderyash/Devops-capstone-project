# MediSlot — Clinic Appointment Booking

MediSlot is a small clinic scheduling app. Front-desk staff manage the clinic's doctors, book patient
appointments, and move each visit through its lifecycle
(**Scheduled → Checked in → Completed**, or **Cancelled**). The backend refuses double-bookings: a
doctor can never have two active appointments that overlap in time.

The app is the vehicle for the DevOps capstone. It goes from a laptop to a monitored, autoscaling
Kubernetes deployment on AWS:

```text
 Developer ── git push ──▶ GitHub
                              │
                     GitHub Actions (.github/workflows/ci-cd.yml)
                              ├─ pytest (22 tests) + Alembic check on real PostgreSQL
                              ├─ frontend unit tests + Vite build
                              ├─ helm lint + terraform validate
                              ├─ docker build (backend, frontend)
                              ├─ Trivy scan ── fails on fixable HIGH/CRITICAL CVEs
                              ├─ push to GHCR  (tag = commit SHA)
                              └─ helm upgrade --install ──┐
                                                          ▼
   Terraform ─▶ AWS: VPC (2 public + 2 private subnets, NAT) + EKS 1.36 (managed node group)
                                                          │
                     ┌────────────── ingress-nginx (NLB) ─┴───────────────┐
                     │  /            → frontend Service → React + Nginx   │ 2+ pods
                     │  /api         → backend Service  → FastAPI         │ 2–8 pods (HPA)
                     │                                     │              │
                     │                          PostgreSQL StatefulSet    │ EBS gp3 volume
                     └────────────────────────────────────────────────────┘
                     Prometheus ◀─ ServiceMonitor ─ /metrics      Grafana dashboard
```

| Layer | Technology |
|-------|------------|
| Frontend | React 19 + Vite 8, plain CSS (responsive), served by unprivileged Nginx |
| Backend | FastAPI, SQLAlchemy 2, Pydantic 2, Alembic, Prometheus instrumentation |
| Database | PostgreSQL 18 |
| Tests | pytest (SQLite in-memory test DB), Node test runner |
| Containers | Multi-stage Dockerfiles, non-root users, Docker Compose |
| CI/CD | GitHub Actions, Trivy, GitHub Container Registry |
| Infrastructure | Terraform (AWS VPC + EKS modules), EBS CSI via EKS Pod Identity, CI deploy identity (OIDC role or least-privilege user) |
| Platform | Kubernetes, Helm 4, ingress-nginx, HPA + metrics-server, PodDisruptionBudgets |
| Observability | kube-prometheus-stack (Prometheus, Grafana, Alertmanager) |

---

## Repository layout

```text
backend/            FastAPI app (app/), Alembic migrations (alembic/versions/), pytest suite (tests/)
frontend/           React app (src/), Nginx config template, multi-stage Dockerfile
docker-compose.yml  Full local stack: postgres + backend + frontend
.github/workflows/  CI/CD pipeline
terraform/          AWS VPC + EKS + IAM (EBS CSI role, GitHub Actions deploy identity)
k8s/                Namespace, gp3 StorageClass, kind cluster config
helm/medislot/      Helm chart (Deployments, Services, StatefulSet, Ingress, HPA, ServiceMonitor, dashboard)
monitoring/         kube-prometheus-stack values (Prometheus + Grafana)
scripts/            Cluster bootstrap, local kind rehearsal, load testing
troubleshooting/    Deliberately broken manifests + walkthrough
docs/               Trivy scan write-up, screenshots, original course guide
```

---

## 1. Run it locally (Docker Compose)

```bash
docker compose up --build
```

| URL | What |
|-----|------|
| http://localhost:3000 | MediSlot UI |
| http://localhost:8000/docs | Swagger UI (try every endpoint) |
| http://localhost:8000/health | Liveness: `{"status":"UP"}` |
| http://localhost:8000/ready | Readiness: checks the database (`503` if it is down) |
| http://localhost:8000/metrics | Prometheus metrics |

The backend runs `alembic upgrade head` on start, and migration `0002` seeds four doctors, so the app
is usable straight away. `docker compose down -v` stops everything and wipes the database.

Look at the data directly:

```bash
docker compose exec postgres psql -U medislot -c "select id, patient_name, status, scheduled_at from appointments;"
```

### Without Docker

```bash
# backend (needs a PostgreSQL; see backend/.env.example)
cd backend && python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export DATABASE_URL=postgresql+psycopg://medislot:medislot@localhost:5432/medislot
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# frontend (Vite proxies /api to :8000)
cd frontend && npm ci && npm run dev    # http://localhost:5173
```

---

## 2. API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health`, `/ready`, `/metrics` | Probes and metrics |
| GET | `/api/doctors?specialty=` | List doctors |
| GET | `/api/doctors/{id}` | Get one doctor |
| POST | `/api/doctors` | Add a doctor (`409` if the email exists) |
| PUT | `/api/doctors/{id}` | Update a doctor |
| DELETE | `/api/doctors/{id}` | Remove a doctor (`409` if they have appointments) |
| GET | `/api/appointments?status=&doctor_id=&day=YYYY-MM-DD` | List / filter appointments |
| GET | `/api/appointments/{id}` | Get one appointment |
| GET | `/api/appointments/stats` | Dashboard counters |
| POST | `/api/appointments` | Book (`404` unknown doctor, `409` overlapping slot) |
| PUT | `/api/appointments/{id}` | Reschedule or change status (overlaps re-checked) |
| DELETE | `/api/appointments/{id}` | Delete |

Custom business metrics on `/metrics`: `medislot_appointments_booked_total{specialty}`,
`medislot_appointment_status_changes_total{status}` and `medislot_booking_conflicts_total`.

---

## 3. Tests

```bash
cd backend && pytest -v      # 22 tests: ops endpoints, doctors CRUD, booking rules, stats, metrics
cd frontend && npm test      # 6 unit tests for formatting / lifecycle helpers
```

`tests/conftest.py` gives every test a fresh **in-memory SQLite** database through FastAPI dependency
overrides, so tests never touch the real PostgreSQL. CI additionally runs the Alembic migrations up,
down, and up again against a real PostgreSQL service container, then runs `alembic check` to catch
model changes that have no migration.

---

## 4. CI/CD pipeline

`.github/workflows/ci-cd.yml` runs on every push and pull request to `main`:

1. **backend-test**, **frontend-build** and **iac-lint** run in parallel. Any failure stops the pipeline,
   so a broken commit never produces an image.
2. **build-scan-push** (matrix: backend, frontend) builds each image tagged with the **full commit
   SHA**, scans it with **Trivy**, uploads the SARIF report to the GitHub *Security* tab, and **fails on
   any fixable HIGH/CRITICAL vulnerability**. Images are pushed to GHCR only on `main`, never from PRs.
3. **deploy** authenticates to AWS (OIDC role, or a least-privilege deploy user where OIDC is blocked), runs
   `helm upgrade --install --rollback-on-failure`, then smoke-tests the API through the Ingress.

Every running pod therefore traces back to an exact commit:
`ghcr.io/heavycoderyash/medislot-backend:<sha>`.

> **Supply-chain note:** `aquasecurity/trivy-action` is pinned to a commit SHA (v0.35.0). In March 2026
> its version tags were force-pushed to credential-stealing code (CVE-2026-33634). Only the immutable
> SHA reference is safe.

### One-time GitHub setup

| Where | Name | Value |
|-------|------|-------|
| Settings → Secrets and variables → Actions → **Variables** | `EKS_CLUSTER_NAME` | `terraform output -raw cluster_name` |
| | `AWS_REGION` | `ap-southeast-2` |
| … → **Secrets** | `POSTGRES_PASSWORD` | a strong random string (`openssl rand -hex 16`) |
| | `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | key of the deploy user (see below) |
| Your profile → Packages → `medislot-backend` / `medislot-frontend` → Package settings | Visibility | **Public** (so EKS can pull without a pull secret) |

**AWS login for the pipeline.** Two modes, chosen with `github_oidc_enabled` in `terraform.tfvars`:

- `true` (preferred): GitHub assumes an IAM role through OIDC, and no AWS keys are stored anywhere. Set
  the `AWS_DEPLOY_ROLE_ARN` variable from `terraform output -raw github_actions_role_arn`.
- `false` (this project's account): the AWS Organization's SCP denies `iam:CreateOpenIDConnectProvider`,
  so Terraform creates an IAM user that can only call `eks:DescribeCluster`. Create its key with
  `aws iam create-access-key --user-name $(terraform output -raw github_deploy_user)` and store it as the
  two secrets above. The key never enters Git or Terraform state.

The deploy job is skipped until `EKS_CLUSTER_NAME` is set, so the pipeline stays green before the
infrastructure exists.

---

## 5. AWS infrastructure (Terraform)

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars     # set github_repository; no credentials go here
aws configure                                    # or `aws login` / SSO
terraform init
terraform plan -out tfplan
terraform apply tfplan                           # ~15 min
$(terraform output -raw configure_kubectl)       # aws eks update-kubeconfig ...
```

This creates a VPC (`10.20.0.0/16`) across two AZs, with two public subnets (tagged for internet-facing
load balancers), two private subnets for worker nodes, and one NAT gateway. It also creates an EKS 1.36
cluster with a managed node group (2× `c7i-flex.large`, autoscaling 2–4) and the add-ons `vpc-cni`, `coredns`,
`kube-proxy`, `eks-pod-identity-agent`, `aws-ebs-csi-driver` (IAM through Pod Identity) and
`metrics-server`. Finally, it creates an IAM role GitHub Actions can assume only from the `main` branch
of this repository (or, where OIDC is blocked, a deploy user limited to `eks:DescribeCluster`). See [terraform/README.md](terraform/README.md).

> **Instance type:** `c7i-flex.large` (2 vCPU, 4 GiB) because AWS *Free plan* accounts can only launch
> free-tier-eligible types; `t3.medium` is rejected there.
>
> **Cost:** EKS control plane + NAT gateway + 2 nodes + the ingress load balancer ≈ US$0.40/hour
> (billed against Free plan credits, if you have them). Run `terraform destroy` after the
> evaluation, after first running `helm uninstall` (see section 9).

---

## 6. Deploy to Kubernetes

```bash
scripts/bootstrap-cluster.sh eks     # namespace, gp3 StorageClass, ingress-nginx (NLB), kube-prometheus-stack

helm upgrade --install medislot ./helm/medislot -n medislot \
  -f helm/medislot/values-prod.yaml \
  --set backend.image.tag=<commit-sha> --set frontend.image.tag=<commit-sha> \
  --set postgres.password="$(openssl rand -hex 16)"
```

After the first manual install, every push to `main` redeploys automatically.

```bash
kubectl get pods,svc,ingress,hpa -n medislot
helm list -n medislot
kubectl get svc ingress-nginx-controller -n ingress-nginx   # EXTERNAL-IP = app URL
```

What the chart deploys:

- **backend** Deployment (2+ replicas): startup, readiness (`/ready`) and liveness (`/health`) probes,
  CPU/memory requests, `DATABASE_URL` taken from a Secret.
- **frontend** Deployment (2 replicas): Nginx on port 8080, non-root.
- **ClusterIP Services** for the backend, frontend and PostgreSQL.
- **PostgreSQL StatefulSet** with a persistent volume.
- **Migration Job**, a Helm hook that runs Alembic once per release so replicas never race each other.
- **Ingress**: `/api` → backend, `/` → frontend.
- **HPA**: backend scales 2 → 8 pods at 60% CPU.
- **PodDisruptionBudgets** that keep at least one pod of each Deployment up during node drains.
- **ServiceMonitor** and **Grafana dashboard** ConfigMap.

All pods pass the Kubernetes **restricted** Pod Security Standard: non-root, no privilege escalation,
all capabilities dropped, seccomp `RuntimeDefault`. The namespace enforces it.

### Rehearse locally first (kind)

```bash
scripts/local-k8s-up.sh                              # kind cluster + add-ons + build + helm install
echo "127.0.0.1 medislot.local" | sudo tee -a /etc/hosts
open http://medislot.local
kind delete cluster --name medislot                  # when done
```

---

## 7. Autoscaling and monitoring

```bash
kubectl apply -f scripts/load-generator.yaml        # in-cluster load
kubectl get hpa -n medislot -w                      # REPLICAS climbs 2 → 3 → 4 …
kubectl delete -f scripts/load-generator.yaml       # scales back down after ~2 min
# or from your laptop through the Ingress:
URL=http://<ingress-address> REQUESTS=20000 CONCURRENCY=50 scripts/load-test.sh
```

```bash
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090   # Status → Targets
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3001:80        # Dashboards → MediSlot
```

The **MediSlot - Application Overview** dashboard loads automatically. It shows request rate, 5xx error
ratio, p95 latency, live backend pod count, per-endpoint traffic and latency, CPU per pod (what the HPA
reacts to), and appointments booked per specialty. Alert rules for "backend down", "error rate > 5%" and
"p95 > 1s" ship in [monitoring/prometheus-values.yaml](monitoring/prometheus-values.yaml). See
[monitoring/README.md](monitoring/README.md).

---

## 8. Troubleshooting lab

[troubleshooting/README.md](troubleshooting/README.md) has three deliberately broken manifests:
`ImagePullBackOff`, a Service with no endpoints (wrong selector *and* wrong targetPort), and a
`CrashLoopBackOff` caused by a bad `DATABASE_URL`. Each one comes with the commands that find the
cause and the fix.

---

## 9. Teardown (avoid AWS charges)

```bash
helm uninstall medislot -n medislot
helm uninstall kube-prometheus-stack -n monitoring
helm uninstall ingress-nginx -n ingress-nginx       # deletes the NLB
kubectl delete pvc --all -n medislot                # deletes the EBS volume
cd terraform && terraform destroy
```

Uninstall the ingress controller and the PVCs **before** `terraform destroy`. The NLB and EBS volume are
created by Kubernetes, not Terraform, so they would otherwise block the VPC deletion.

---

## Security practices

- No credentials in Git: the DB password is passed at deploy time (`--set` / GitHub secret), CI's AWS
  access is OIDC or a deploy user that can only describe the cluster, and `.env`, `terraform.tfvars` and state files are git-ignored.
- Containers run as non-root (backend uid 10001, Nginx uid 101, Postgres uid 70) with all Linux
  capabilities dropped.
- Images are scanned before they are pushed. `pip` is removed from the runtime image, which removes its
  vendored libraries from the attack surface.
- The CI token has least privilege: `packages: write` only in the build job, `id-token: write` only in
  the deploy job.

See [docs/SUBMISSION.md](docs/SUBMISSION.md) for what the Trivy scan covered and what its result means.
Screenshots of every stage are in [docs/screenshots/](docs/screenshots/).
