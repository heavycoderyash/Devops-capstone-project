# ---------------------------------------------------------------------------
# Lets GitHub Actions deploy with short-lived credentials (OIDC) instead of
# long-lived AWS access keys stored as repository secrets.
# Enabled when var.github_repository is set, e.g. "heavycoderyash/Devops-capstone-project".
# ---------------------------------------------------------------------------
resource "aws_iam_openid_connect_provider" "github" {
  count = var.github_repository == "" ? 0 : 1

  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

data "aws_iam_policy_document" "github_trust" {
  count = var.github_repository == "" ? 0 : 1

  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github[0].arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    # Only workflows running on the main branch of this repository may assume the role.
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repository}:ref:refs/heads/main"]
    }
  }
}

resource "aws_iam_role" "github_actions" {
  count = var.github_repository == "" ? 0 : 1

  name               = "${local.name}-github-deploy"
  assume_role_policy = data.aws_iam_policy_document.github_trust[0].json
}

# `aws eks update-kubeconfig` only needs DescribeCluster; Kubernetes
# permissions come from the EKS access entry in main.tf.
resource "aws_iam_role_policy" "github_actions_eks" {
  count = var.github_repository == "" ? 0 : 1

  name = "eks-describe"
  role = aws_iam_role.github_actions[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["eks:DescribeCluster"]
      Resource = module.eks.cluster_arn
    }]
  })
}
