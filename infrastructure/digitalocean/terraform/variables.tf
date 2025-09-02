# PlotTwist DigitalOcean Infrastructure Variables

variable "do_token" {
  description = "DigitalOcean API token"
  type        = string
  sensitive   = true
}

variable "do_region" {
  description = "DigitalOcean region for deployment"
  type        = string
  default     = "nyc1"
}

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  default     = "production"
}

variable "droplet_size" {
  description = "DigitalOcean droplet size"
  type        = string
  default     = "s-1vcpu-1gb"  # $6/month
}

variable "public_key" {
  description = "Public key for SSH access"
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

variable "domain_name" {
  description = "Domain name for the application (optional)"
  type        = string
  default     = ""
}

variable "docker_username" {
  description = "Docker Hub username for image registry"
  type        = string
  default     = ""
}

variable "docker_password" {
  description = "Docker Hub password for image registry"
  type        = string
  sensitive   = true
  default     = ""
}
