output "region" {
  value = var.aws_region
}

output "vpc_id" {
  value = module.vpc.vpc_id
}

output "public_subnets" {
  value = module.vpc.public_subnets
}

output "private_subnets" {
  value = module.vpc.private_subnets
}

output "cluster_name" {
  value = module.eks.cluster_name
}

output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "cluster_version" {
  value = module.eks.cluster_version
}

output "configure_kubectl" {
  description = "Run this to point kubectl at the new cluster"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}

output "github_actions_role_arn" {
  description = "OIDC mode: store as the AWS_DEPLOY_ROLE_ARN repository variable in GitHub"
  value       = local.github_oidc ? aws_iam_role.github_actions[0].arn : null
}

output "github_deploy_user" {
  description = "Access-key mode: create a key for this user and store it as GitHub secrets"
  value       = local.github_user ? aws_iam_user.github_actions[0].name : null
}
