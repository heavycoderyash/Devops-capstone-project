# Terraform: AWS VPC + EKS

Provisions everything MediSlot needs in AWS. Kubernetes manages workloads; Terraform creates the network
and the cluster underneath them.

```text
AWS (ap-southeast-2)
 └── VPC 10.20.0.0/16 (2 AZs)
      ├── public subnets  10.20.101.0/24, 10.20.102.0/24   ← NLB for ingress-nginx, NAT gateway
      ├── private subnets 10.20.1.0/24,   10.20.2.0/24     ← worker nodes
      └── EKS cluster medislot-dev (Kubernetes 1.36)
           ├── managed node group: 2× c7i-flex.large (min 2, max 4), AL2023
           ├── add-ons: vpc-cni, coredns, kube-proxy, eks-pod-identity-agent,
           │            aws-ebs-csi-driver (IAM role via Pod Identity), metrics-server
           └── access entry for the GitHub Actions OIDC role (if github_repository is set)
```

| File | Contents |
|------|----------|
| `versions.tf` | Terraform/provider versions, AWS provider with default tags, optional S3 backend |
| `variables.tf` | Inputs with defaults (region, sizes, Kubernetes version, GitHub repo) |
| `main.tf` | VPC module, EKS module, EBS CSI IAM role + Pod Identity association |
| `github-oidc.tf` | OIDC provider + IAM role GitHub Actions assumes to deploy (no stored AWS keys) |
| `outputs.tf` | Cluster name/endpoint, VPC/subnet IDs, kubeconfig command, deploy role ARN |
| `terraform.tfvars.example` | Copy to `terraform.tfvars` (git-ignored) |

## Usage

```bash
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform fmt -check && terraform validate
terraform plan -out tfplan
terraform apply tfplan
$(terraform output -raw configure_kubectl)
kubectl get nodes
```

AWS credentials come from your environment (`aws configure`, `aws login`, SSO or `AWS_PROFILE`), never
from `.tf` or `.tfvars` files.

## Destroy

First delete what Kubernetes created in AWS (the load balancer and EBS volumes), otherwise the VPC
cannot be deleted:

```bash
helm uninstall medislot -n medislot
helm uninstall ingress-nginx -n ingress-nginx
kubectl delete pvc --all -n medislot
terraform destroy
```

> Cost: EKS control plane (~$0.10/h) + NAT gateway (~$0.056/h + data) + 2× c7i-flex.large (~$0.09/h) in ap-southeast-2.
> Destroy as soon as you have your screenshots.
