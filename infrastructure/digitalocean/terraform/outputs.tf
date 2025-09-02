# PlotTwist DigitalOcean Infrastructure Outputs

output "droplet_id" {
  description = "ID of the DigitalOcean droplet"
  value       = digitalocean_droplet.plottwist_server.id
}

output "droplet_ip" {
  description = "Public IP address of the droplet"
  value       = digitalocean_droplet.plottwist_server.ipv4_address
}

output "ssh_command" {
  description = "SSH command to connect to the droplet"
  value       = "ssh -i ~/.ssh/plottwist-key root@${digitalocean_droplet.plottwist_server.ipv4_address}"
}

output "frontend_url" {
  description = "Frontend application URL"
  value       = "http://${digitalocean_droplet.plottwist_server.ipv4_address}:3000"
}

output "backend_url" {
  description = "Backend API URL"
  value       = "http://${digitalocean_droplet.plottwist_server.ipv4_address}:8000"
}

output "domain_frontend_url" {
  description = "Domain-based frontend URL"
  value       = var.domain_name != "" ? "https://${var.domain_name}" : "http://${digitalocean_droplet.plottwist_server.ipv4_address}:3000"
}

output "domain_backend_url" {
  description = "Domain-based backend URL"
  value       = var.domain_name != "" ? "https://api.${var.domain_name}" : "http://${digitalocean_droplet.plottwist_server.ipv4_address}:8000"
}

output "deployment_commands" {
  description = "Commands to deploy the application"
  value = <<-EOT
    # SSH into the droplet
    ${self.ssh_command}
    
    # Clone repositories
    git clone https://github.com/your-username/plottwist-backend.git
    git clone https://github.com/your-username/plottwist-frontend.git
    
    # Deploy with Docker Compose
    cd plottwist-backend
    docker-compose -f docker-compose.prod.yml up -d
  EOT
}
