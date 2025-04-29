variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "classifier-api"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage (GB)"
  type        = number
  default     = 5
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "classifier"
}

variable "db_username" {
  description = "PostgreSQL database username"
  type        = string
  default     = "postgres"
}

variable "db_password" {
  description = "PostgreSQL database password"
  type        = string
  sensitive   = true
}

variable "eb_instance_type" {
  description = "Elastic Beanstalk EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "eb_min_instances" {
  description = "Minimum number of instances in the Elastic Beanstalk environment"
  type        = number
  default     = 1
}

variable "eb_max_instances" {
  description = "Maximum number of instances in the Elastic Beanstalk environment"
  type        = number
  default     = 2
}

variable "api_key" {
  description = "API key for authentication"
  type        = string
  sensitive   = true
}

variable "s3_lifecycle_transition_days" {
  description = "Number of days before transitioning objects to Infrequent Access storage"
  type        = number
  default     = 30
}