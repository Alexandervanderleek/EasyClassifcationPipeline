# Elastic Beanstalk application
resource "aws_elastic_beanstalk_application" "app" {
  name        = "${local.name_prefix}-app"
  description = "Classifier API Application"
  
  tags = local.common_tags
}

# Elastic Beanstalk environment
resource "aws_elastic_beanstalk_environment" "env" {
  name                = "${local.name_prefix}-env"
  application         = aws_elastic_beanstalk_application.app.name
  solution_stack_name = "64bit Amazon Linux 2 v3.5.0 running Python 3.8"
  
  # Link to the instance profile
  setting {
    namespace = "aws:autoscaling:launchconfiguration"
    name      = "IamInstanceProfile"
    value     = aws_iam_instance_profile.eb_instance_profile.name
  }
  
  # Instance settings
  setting {
    namespace = "aws:ec2:instances"
    name      = "InstanceTypes"
    value     = var.eb_instance_type
  }
  
  # Auto scaling settings
  setting {
    namespace = "aws:autoscaling:asg"
    name      = "MinSize"
    value     = var.eb_min_instances
  }
  
  setting {
    namespace = "aws:autoscaling:asg"
    name      = "MaxSize"
    value     = var.eb_max_instances
  }
  
  # Load balancer settings
  setting {
    namespace = "aws:elasticbeanstalk:environment"
    name      = "LoadBalancerType"
    value     = "application"
  }
  
  # VPC and security group settings
  setting {
    namespace = "aws:ec2:vpc"
    name      = "VPCId"
    value     = data.aws_vpc.default.id
  }
  
  setting {
    namespace = "aws:ec2:vpc"
    name      = "Subnets"
    value     = join(",", aws_default_subnet.default[*].id)
  }
  
  setting {
    namespace = "aws:autoscaling:launchconfiguration"
    name      = "SecurityGroups"
    value     = aws_security_group.eb.id
  }
  
  # Environment variables
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "FLASK_ENV"
    value     = var.environment
  }
  
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "API_KEY"
    value     = var.api_key
  }
  
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "S3_BUCKET_NAME"
    value     = aws_s3_bucket.models.id
  }
  
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "DATABASE_URL"
    value     = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.endpoint}/${var.db_name}"
  }
  
  # CloudWatch Logs
  setting {
    namespace = "aws:elasticbeanstalk:cloudwatch:logs"
    name      = "StreamLogs"
    value     = "true"
  }
  
  setting {
    namespace = "aws:elasticbeanstalk:cloudwatch:logs"
    name      = "DeleteOnTerminate"
    value     = "false"
  }
  
  setting {
    namespace = "aws:elasticbeanstalk:cloudwatch:logs"
    name      = "RetentionInDays"
    value     = "14"
  }
  
  # Rolling updates
  setting {
    namespace = "aws:elasticbeanstalk:command"
    name      = "DeploymentPolicy"
    value     = "Rolling"
  }
  
  setting {
    namespace = "aws:elasticbeanstalk:command"
    name      = "BatchSizeType"
    value     = "Percentage"
  }
  
  setting {
    namespace = "aws:elasticbeanstalk:command"
    name      = "BatchSize"
    value     = "25"
  }
  
  # Health checks
  setting {
    namespace = "aws:elasticbeanstalk:environment:process:default"
    name      = "HealthCheckPath"
    value     = "/api/health"
  }
  
  tags = local.common_tags
  
  # Ensure database is created first
  depends_on = [aws_db_instance.postgres]
}