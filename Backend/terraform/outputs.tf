output "app_url" {
  description = "URL of the Elastic Beanstalk environment"
  value       = aws_elastic_beanstalk_environment.env.endpoint_url
}

output "db_endpoint" {
  description = "RDS database endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "s3_models_bucket" {
  description = "S3 bucket for storing models"
  value       = aws_s3_bucket.models.bucket
}

output "db_connection_string" {
  description = "Database connection string (without password)"
  value       = "postgresql://${var.db_username}:****@${aws_db_instance.postgres.endpoint}/${var.db_name}"
  sensitive   = true
}