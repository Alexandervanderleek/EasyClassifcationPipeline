# Use default VPC for simplicity in the POC stage
data "aws_vpc" "default" {
  default = true
}

# Get availability zones in the region
data "aws_availability_zones" "available" {
  state = "available"
}

# Use default subnets
resource "aws_default_subnet" "default" {
  count = 2  # Create in first two AZs
  
  availability_zone = data.aws_availability_zones.available.names[count.index]
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-subnet-${count.index}"
  })
}

# Security group for Elastic Beanstalk
resource "aws_security_group" "eb" {
  name        = "${local.name_prefix}-eb-sg"
  description = "Security group for Elastic Beanstalk environment"
  vpc_id      = data.aws_vpc.default.id
  
  # Allow HTTP traffic
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  # Allow HTTPS traffic
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-eb-sg"
  })
}