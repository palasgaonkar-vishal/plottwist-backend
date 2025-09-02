#!/bin/bash
# PlotTwist DigitalOcean Deployment Script

set -e

echo "🌊 PlotTwist DigitalOcean Deployment"
echo "===================================="

# Check if terraform.tfvars exists
if [ ! -f "terraform/terraform.tfvars" ]; then
    echo "❌ terraform.tfvars not found!"
    echo "📝 Please create terraform.tfvars with your configuration:"
    echo ""
    cat << 'TFVARS'
do_token = "your_digitalocean_api_token_here"
do_region = "nyc1"
environment = "production"
droplet_size = "s-1vcpu-1gb"
public_key = "$(cat ~/.ssh/id_rsa.pub)"
db_password = "YourSecurePassword123!"
jwt_secret_key = "YourJWTSecretKey123!"
domain_name = "yourdomain.com"
TFVARS
    echo ""
    echo "💡 Save this as terraform/terraform.tfvars and run the script again."
    exit 1
fi

# Deploy infrastructure
echo "🏗️  Deploying infrastructure with Terraform..."
cd terraform
terraform init
terraform plan
terraform apply -auto-approve

# Get droplet IP
DROPLET_IP=$(terraform output -raw droplet_ip)
echo "✅ Droplet created with IP: $DROPLET_IP"

# Display next steps
echo ""
echo "🎉 Infrastructure deployed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. SSH into your droplet:"
echo "   ssh root@$DROPLET_IP"
echo ""
echo "2. Clone your repositories:"
echo "   cd /opt/plottwist"
echo "   git clone https://github.com/your-username/plottwist-backend.git"
echo "   git clone https://github.com/your-username/plottwist-frontend.git"
echo ""
echo "3. Configure environment:"
echo "   cp .env.template .env"
echo "   nano .env  # Edit with your values"
echo ""
echo "4. Deploy application:"
echo "   ./deploy.sh"
echo ""
echo "🌐 Your application will be available at:"
echo "   Frontend: http://$DROPLET_IP:3000"
echo "   Backend:  http://$DROPLET_IP:8000"
echo "   API Docs: http://$DROPLET_IP:8000/docs"
echo ""
echo "💡 For domain setup, point your domain to $DROPLET_IP"
