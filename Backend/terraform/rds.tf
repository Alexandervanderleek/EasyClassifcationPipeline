# RDS security group
resource "aws_security_group" "rds" {
  name        = "${local.name_prefix}-rds-sg"
  description = "Security group for RDS PostgreSQL database"
  
  # Allow inbound traffic from Elastic Beanstalk security group
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.eb.id]
  }
  
  # Optionally allow inbound from other sources like bastion hosts
  # (uncomment and configure as needed)
  # ingress {
  #   from_port   = 5432
  #   to_port     = 5432
  #   protocol    = "tcp"
  #   cidr_blocks = ["your-admin-ip/32"]
  # }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-rds-sg"
  })
}

# RDS subnet group
resource "aws_db_subnet_group" "default" {
  name       = "${local.name_prefix}-rds-subnet-group"
  subnet_ids = aws_default_subnet.default[*].id
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-rds-subnet-group"
  })
}

# RDS PostgreSQL instance
resource "aws_db_instance" "postgres" {
  identifier             = "${local.name_prefix}-db"
  engine                 = "postgres"
  engine_version         = "14.6"
  instance_class         = var.db_instance_class
  allocated_storage      = var.db_allocated_storage
  storage_type           = "gp2"
  
  db_name                = var.db_name
  username               = var.db_username
  password               = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.default.name
  
  # Backups and maintenance
  backup_retention_period = 7
  backup_window           = "03:00-04:00"  # UTC
  maintenance_window      = "Mon:04:00-Mon:05:00"  # UTC
  
  # Skip final snapshot for dev/test environments
  # Set to true for production
  skip_final_snapshot     = var.environment != "prod"
  final_snapshot_identifier = var.environment == "prod" ? "${local.name_prefix}-final-${formatdate("YYYYMMDDhhmmss", timestamp())}" : null
  
  # Enable deletion protection in production
  deletion_protection     = var.environment == "prod"
  
  # Performance Insights (optional, for better monitoring)
  performance_insights_enabled = var.environment == "prod"
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-postgres"
  })
}