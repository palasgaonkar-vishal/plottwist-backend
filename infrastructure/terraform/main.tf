# PlotTwist Infrastructure - AWS EC2 Deployment
# Task 011: Deployment Infrastructure

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Configure AWS Provider
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "PlotTwist"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Create VPC
resource "aws_vpc" "plottwist_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "plottwist-vpc"
  }
}

# Create Internet Gateway
resource "aws_internet_gateway" "plottwist_igw" {
  vpc_id = aws_vpc.plottwist_vpc.id

  tags = {
    Name = "plottwist-igw"
  }
}

# Create Public Subnet
resource "aws_subnet" "plottwist_public_subnet" {
  vpc_id                  = aws_vpc.plottwist_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name = "plottwist-public-subnet"
  }
}

# Create Route Table for Public Subnet
resource "aws_route_table" "plottwist_public_rt" {
  vpc_id = aws_vpc.plottwist_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.plottwist_igw.id
  }

  tags = {
    Name = "plottwist-public-rt"
  }
}

# Associate Route Table with Public Subnet
resource "aws_route_table_association" "plottwist_public_rta" {
  subnet_id      = aws_subnet.plottwist_public_subnet.id
  route_table_id = aws_route_table.plottwist_public_rt.id
}

# Security Group for EC2 Instance
resource "aws_security_group" "plottwist_sg" {
  name        = "plottwist-security-group"
  description = "Security group for PlotTwist application"
  vpc_id      = aws_vpc.plottwist_vpc.id

  # SSH access
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTP access
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS access
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Backend API access
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Frontend access
  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # PostgreSQL access (internal)
  ingress {
    from_port = 5432
    to_port   = 5432
    protocol  = "tcp"
    self      = true
  }

  # All outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "plottwist-security-group"
  }
}

# Key Pair for EC2 access
resource "aws_key_pair" "plottwist_key" {
  key_name   = "plottwist-key"
  public_key = var.public_key
}

# EC2 Instance
resource "aws_instance" "plottwist_server" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.plottwist_key.key_name
  subnet_id              = aws_subnet.plottwist_public_subnet.id
  vpc_security_group_ids = [aws_security_group.plottwist_sg.id]

  # User data script for initial setup
  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    db_password           = var.db_password
    jwt_secret_key       = var.jwt_secret_key
    frontend_domain      = var.frontend_domain
    backend_domain       = var.backend_domain
  }))

  # Root volume configuration
  root_block_device {
    volume_type = "gp3"
    volume_size = 20
    encrypted   = true

    tags = {
      Name = "plottwist-root-volume"
    }
  }

  tags = {
    Name = "plottwist-server"
  }
}

# Elastic IP for static public IP
resource "aws_eip" "plottwist_eip" {
  instance = aws_instance.plottwist_server.id
  domain   = "vpc"

  tags = {
    Name = "plottwist-eip"
  }

  depends_on = [aws_internet_gateway.plottwist_igw]
} 