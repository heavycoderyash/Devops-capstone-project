terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # Optional remote state. Create the bucket once, then uncomment and run
  # `terraform init -migrate-state`. Local state is fine for a single student.
  # backend "s3" {
  #   bucket       = "medislot-tfstate-<your-account-id>"
  #   key          = "medislot/terraform.tfstate"
  #   region       = "ap-southeast-2"
  #   use_lockfile = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.tags
  }
}
