# IAM role for Elastic Beanstalk service
resource "aws_iam_role" "eb_service_role" {
  name = "${local.name_prefix}-eb-service-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "elasticbeanstalk.amazonaws.com"
        }
      }
    ]
  })
  
  tags = local.common_tags
}

# Attach AWS managed policies to EB service role
resource "aws_iam_role_policy_attachment" "eb_service_role_policy" {
  role       = aws_iam_role.eb_service_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSElasticBeanstalkService"
}

# IAM role for EC2 instances in the Elastic Beanstalk environment
resource "aws_iam_role" "eb_instance_role" {
  name = "${local.name_prefix}-eb-instance-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
  
  tags = local.common_tags
}

# Attach AWS managed policies to EB instance role
resource "aws_iam_role_policy_attachment" "eb_instance_web_tier" {
  role       = aws_iam_role.eb_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/AWSElasticBeanstalkWebTier"
}

# Custom policy for S3 access to models bucket
resource "aws_iam_policy" "s3_models_access" {
  name        = "${local.name_prefix}-s3-models-access"
  description = "Policy for accessing models S3 bucket"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion",
          "s3:ListBucket",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          aws_s3_bucket.models.arn,
          "${aws_s3_bucket.models.arn}/*"
        ]
      }
    ]
  })
}

# Attach S3 models access policy to instance role
resource "aws_iam_role_policy_attachment" "eb_instance_s3_models" {
  role       = aws_iam_role.eb_instance_role.name
  policy_arn = aws_iam_policy.s3_models_access.arn
}

# Create instance profile for EC2 instances
resource "aws_iam_instance_profile" "eb_instance_profile" {
  name = "${local.name_prefix}-eb-instance-profile"
  role = aws_iam_role.eb_instance_role.name
}