provider "aws" {
  region = var.aws_region
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
  
  # Optional: Configure remote state storage
  backend "s3" {
    bucket = "classifier-pipeline-state-bucket"
    key    = "classifier-api/terraform.tfstate"
    region = "eu-west-1"
  }
}

# Random suffix for unique resource naming
resource "random_id" "suffix" {
  byte_length = 4
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
  name_suffix = random_id.suffix.hex
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}