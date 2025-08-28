# PlotTwist Infrastructure Outputs
# Task 011: Deployment Infrastructure

output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.plottwist_server.id
}

output "instance_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_eip.plottwist_eip.public_ip
}

output "instance_public_dns" {
  description = "Public DNS name of the EC2 instance"
  value       = aws_instance.plottwist_server.public_dns
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i ~/.ssh/plottwist-key ubuntu@${aws_eip.plottwist_eip.public_ip}"
}

output "frontend_url" {
  description = "Frontend application URL"
  value       = "http://${aws_eip.plottwist_eip.public_ip}:3000"
}

output "backend_url" {
  description = "Backend API URL"
  value       = "http://${aws_eip.plottwist_eip.public_ip}:8000"
}

output "ssl_frontend_url" {
  description = "SSL Frontend URL (when SSL is configured)"
  value       = "https://${var.frontend_domain}"
}

output "ssl_backend_url" {
  description = "SSL Backend API URL (when SSL is configured)"
  value       = "https://${var.backend_domain}"
} 