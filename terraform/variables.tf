variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "ap-southeast-2"
}

variable "project" {
  description = "Name prefix for every resource"
  type        = string
  default     = "medislot"
}

variable "environment" {
  description = "Environment tag (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.20.0.0/16"
}

variable "az_count" {
  description = "Number of availability zones (one public + one private subnet in each)"
  type        = number
  default     = 2

  validation {
    condition     = var.az_count >= 2
    error_message = "EKS requires subnets in at least two availability zones."
  }
}

variable "kubernetes_version" {
  description = "EKS Kubernetes version. Keep it in standard support to avoid extended-support charges."
  type        = string
  default     = "1.36"
}

variable "node_instance_types" {
  description = "EC2 instance types for the managed node group"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_min_size" {
  type    = number
  default = 2
}

variable "node_desired_size" {
  type    = number
  default = 2
}

variable "node_max_size" {
  type    = number
  default = 4
}

variable "github_repository" {
  description = "owner/repo allowed to deploy via GitHub Actions OIDC. Empty string disables the CI deploy role."
  type        = string
  default     = ""
}
