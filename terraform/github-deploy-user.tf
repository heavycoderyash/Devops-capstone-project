# ---------------------------------------------------------------------------
# Fallback CI identity when OIDC is unavailable (var.github_oidc_enabled = false).
# The user can only call eks:DescribeCluster in AWS; its Kubernetes permissions
# come from the EKS access entry in main.tf. Create its access key once with
#   aws iam create-access-key --user-name <github_deploy_user output>
# and store it as GitHub secrets - the key never enters Terraform state or Git.
# ---------------------------------------------------------------------------
locals {
  github_oidc = var.github_repository != "" && var.github_oidc_enabled
  github_user = var.github_repository != "" && !var.github_oidc_enabled

  github_deploy_principal_arn = local.github_oidc ? aws_iam_role.github_actions[0].arn : (
    local.github_user ? aws_iam_user.github_actions[0].arn : null
  )
}

resource "aws_iam_user" "github_actions" {
  count = local.github_user ? 1 : 0

  name = "${local.name}-github-deploy"
}

resource "aws_iam_user_policy" "github_actions_eks" {
  count = local.github_user ? 1 : 0

  name = "eks-describe"
  user = aws_iam_user.github_actions[0].name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["eks:DescribeCluster"]
      Resource = module.eks.cluster_arn
    }]
  })
}
