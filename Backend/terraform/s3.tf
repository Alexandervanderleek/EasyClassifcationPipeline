# S3 bucket for model storage
resource "aws_s3_bucket" "models" {
  bucket = "${local.name_prefix}-models-${local.name_suffix}"
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-models"
  })
}

# Enable versioning for models bucket
resource "aws_s3_bucket_versioning" "models_versioning" {
  bucket = aws_s3_bucket.models.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# Configure CORS for models bucket
resource "aws_s3_bucket_cors_configuration" "models_cors" {
  bucket = aws_s3_bucket.models.id
  
  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE", "HEAD"]
    allowed_origins = ["*"] # Restrict to your domains in production
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# Configure lifecycle rules for cost optimization
resource "aws_s3_bucket_lifecycle_configuration" "models_lifecycle" {
  bucket = aws_s3_bucket.models.id
  
  rule {
    id     = "transition-to-ia"
    status = "Enabled"
    
    transition {
      days          = var.s3_lifecycle_transition_days
      storage_class = "STANDARD_IA"
    }
  }
}

# S3 bucket for Elastic Beanstalk deployment
resource "aws_s3_bucket" "eb_deployment" {
  bucket = "${local.name_prefix}-eb-deploy-${local.name_suffix}"
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-eb-deployment"
  })
}

# Elastic Beanstalk app version bucket policy
resource "aws_s3_bucket_policy" "eb_deployment_policy" {
  bucket = aws_s3_bucket.eb_deployment.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "elasticbeanstalk.amazonaws.com"
        }
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion",
          "s3:GetObjectAcl"
        ]
        Resource = "${aws_s3_bucket.eb_deployment.arn}/*"
      }
    ]
  })
}