# PlotTwist Infrastructure - DigitalOcean Droplet Deployment
# Modified for DigitalOcean

terraform {
  required_version = ">= 1.0"
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

# Configure DigitalOcean Provider
provider "digitalocean" {
  token = var.do_token
}

# Create SSH Key
resource "digitalocean_ssh_key" "plottwist_key" {
  name       = "plottwist-${var.environment}"
  public_key = var.public_key
}

# Create Droplet
resource "digitalocean_droplet" "plottwist_server" {
  image    = "ubuntu-22-04-x64"
  name     = "plottwist-${var.environment}"
  region   = var.do_region
  size     = var.droplet_size
  ssh_keys = [digitalocean_ssh_key.plottwist_key.id]
  
  # User data script for initial setup
  user_data = file("${path.module}/user_data.sh")
  
  tags = [
    "plottwist",
    var.environment,
    "managed-by-terraform"
  ]
}

# Create Firewall
resource "digitalocean_firewall" "plottwist_firewall" {
  name = "plottwist-${var.environment}-firewall"
  
  droplet_ids = [digitalocean_droplet.plottwist_server.id]
  
  # SSH
  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  # HTTP
  inbound_rule {
    protocol         = "tcp"
    port_range       = "80"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  # HTTPS
  inbound_rule {
    protocol         = "tcp"
    port_range       = "443"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  # Backend API
  inbound_rule {
    protocol         = "tcp"
    port_range       = "8000"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  # Frontend
  inbound_rule {
    protocol         = "tcp"
    port_range       = "3000"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  # PostgreSQL (restrict to droplet only)
  inbound_rule {
    protocol         = "tcp"
    port_range       = "5432"
    source_addresses = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
  }
  
  # Outbound rules
  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  outbound_rule {
    protocol              = "udp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}

# Create Domain (optional)
resource "digitalocean_domain" "plottwist_domain" {
  count = var.domain_name != "" ? 1 : 0
  name  = var.domain_name
}

# Create A record for domain
resource "digitalocean_record" "plottwist_a_record" {
  count  = var.domain_name != "" ? 1 : 0
  domain = digitalocean_domain.plottwist_domain[0].name
  type   = "A"
  name   = "@"
  value  = digitalocean_droplet.plottwist_server.ipv4_address
}

# Create A record for API subdomain
resource "digitalocean_record" "plottwist_api_record" {
  count  = var.domain_name != "" ? 1 : 0
  domain = digitalocean_domain.plottwist_domain[0].name
  type   = "A"
  name   = "api"
  value  = digitalocean_droplet.plottwist_server.ipv4_address
}
