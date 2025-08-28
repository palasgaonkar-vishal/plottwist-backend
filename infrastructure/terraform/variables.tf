# PlotTwist Infrastructure Variables
# Task 011: Deployment Infrastructure

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  default     = "production"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "public_key" {
  description = "Public key for EC2 SSH access"
  type        = string
}

variable "db_password" {
  description = "PostgreSQL database password"
  type        = string
  sensitive   = true
}

variable "jwt_secret_key" {
  description = "JWT secret key for authentication"
  type        = string
  sensitive   = true
}

variable "frontend_domain" {
  description = "Frontend domain name"
  type        = string
  default     = "plottwist.example.com"
}

variable "backend_domain" {
  description = "Backend API domain name"
  type        = string
  default     = "api.plottwist.example.com"
} 