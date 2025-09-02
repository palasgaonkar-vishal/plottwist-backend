# PlotTwist Deployment Infrastructure
**Task 011: Deployment Infrastructure**

This directory contains all the infrastructure components needed to deploy PlotTwist to AWS EC2 with production-ready configurations.

## 📁 Directory Structure

```
infrastructure/
├── terraform/              # Infrastructure as Code
│   ├── main.tf             # Main Terraform configuration
│   ├── variables.tf        # Input variables
│   ├── outputs.tf          # Output values
│   └── user_data.sh        # EC2 initialization script
├── docker/                 # Container configurations
│   └── production.yml      # Production Docker Compose
├── monitoring/             # Health checks and monitoring
│   └── health-check.sh     # Production health check script
└── README.md              # This file
```

**Note**: CI/CD pipelines are managed through GitHub Actions workflows in the respective repository `.github/workflows/` directories:
- Backend CI/CD: `plottwist-backend/.github/workflows/ci-cd.yml`
- Frontend CI/CD: `plottwist-frontend/.github/workflows/ci-cd.yml`

## 🚀 Quick Start

### 1. Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform >= 1.0 installed
- SSH key pair for EC2 access
- Domain names configured (optional but recommended)

### 2. Deploy Infrastructure

```bash
# Navigate to terraform directory
cd terraform/

# Initialize Terraform
terraform init

# Review the deployment plan
terraform plan -var="public_key=$(cat ~/.ssh/id_rsa.pub)" \
               -var="db_password=your_secure_password" \
               -var="jwt_secret_key=your_jwt_secret"

# Deploy infrastructure
terraform apply
```

### 3. Configure GitHub Actions

Set up the following secrets in both repositories:

#### Required Secrets:
- `EC2_HOST`: EC2 instance public IP
- `EC2_USERNAME`: ubuntu
- `EC2_SSH_KEY`: Private SSH key content
- `BACKEND_URL`: https://api.yourdom ain.com
- `FRONTEND_URL`: https://yourdomain.com
- `REACT_APP_API_URL`: Backend URL for frontend

#### Optional Secrets:
- `DOCKER_USERNAME`: Docker Hub username
- `DOCKER_PASSWORD`: Docker Hub password
- `SLACK_WEBHOOK`: Slack notification webhook
- `SNYK_TOKEN`: Snyk security scanning token

## 🏗️ Infrastructure Components

### AWS Resources

| Resource | Type | Purpose |
|----------|------|---------|
| EC2 Instance | t3.micro | Application server |
| VPC | Custom | Network isolation |
| Security Group | Custom | Traffic control |
| Elastic IP | Static | Consistent addressing |
| Key Pair | RSA | SSH access |

### Services Configuration

#### Backend (Port 8000)
- **Runtime**: Python 3.10 with uvicorn
- **Database**: PostgreSQL 14
- **Process Manager**: systemd
- **Environment**: Production with secure configurations

#### Frontend (Port 3000)
- **Runtime**: Node.js 18
- **Build**: React production build
- **Process Manager**: systemd
- **Proxy**: Nginx reverse proxy

#### Database
- **Engine**: PostgreSQL 14
- **User**: plottwist
- **Database**: plottwist
- **Backup**: Automated via cron

#### Web Server
- **Proxy**: Nginx
- **SSL**: Let's Encrypt certificates
- **Security**: Security headers and HTTPS redirect

## 🔧 Environment Configuration

### Production Environment Variables

```bash
# Database
DATABASE_URL=postgresql://plottwist:password@localhost:5432/plottwist

# Authentication
JWT_SECRET_KEY=your-secure-jwt-secret

# Application URLs
FRONTEND_URL=https://yourdomain.com
BACKEND_URL=https://api.yourdomain.com

# Security
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com
ENVIRONMENT=production
```

### Domain Configuration

1. Point your domains to the Elastic IP:
   ```
   yourdomain.com       A    <ELASTIC_IP>
   api.yourdomain.com   A    <ELASTIC_IP>
   ```

2. SSL certificates are automatically obtained via Let's Encrypt

## 🔄 CI/CD Pipeline

The CI/CD pipelines are configured and managed in the respective repository workflows:

### Backend Pipeline
- **Location**: `plottwist-backend/.github/workflows/ci-cd.yml`
- **Features**: Testing, security scanning, linting, coverage reporting
- **Triggers**: Push to main/develop branches, pull requests

### Frontend Pipeline  
- **Location**: `plottwist-frontend/.github/workflows/ci-cd.yml`
- **Features**: Testing, linting, building, security auditing
- **Triggers**: Push to main/develop branches, pull requests

### Pipeline Integration with Infrastructure
Both pipelines can be extended to include automatic deployment to the infrastructure created by these Terraform scripts. The infrastructure provides the target environment for deployment.

## 📊 Monitoring & Health Checks

### Automated Health Checks
- Database connectivity
- API endpoint availability
- Frontend application status
- System resource usage
- SSL certificate expiry
- Response time monitoring

### Usage
```bash
# Run health check
sudo /opt/plottwist/health-check.sh

# View logs
tail -f /var/log/plottwist/health-check.log
```

## 🔒 Security Features

### Infrastructure Security
- VPC with private subnets
- Security groups with minimal required ports
- Encrypted EBS volumes
- SSH key-based authentication

### Application Security
- HTTPS-only with automatic redirect
- Security headers via Nginx
- JWT-based authentication
- Environment variable encryption

### Monitoring
- Automated vulnerability scanning
- Dependency security checks
- SSL certificate monitoring
- Resource usage alerts

## 🚀 Deployment Commands

### Manual Deployment
```bash
# SSH to instance
ssh -i ~/.ssh/plottwist-key ubuntu@<ELASTIC_IP>

# Deploy latest changes
sudo -u ubuntu /opt/plottwist/deploy.sh

# Setup SSL (first time only)
sudo -u ubuntu /opt/plottwist/setup-ssl.sh

# Check services
sudo systemctl status plottwist-backend
sudo systemctl status plottwist-frontend
sudo systemctl status nginx
```

### Service Management
```bash
# Restart services
sudo systemctl restart plottwist-backend
sudo systemctl restart plottwist-frontend
sudo systemctl restart nginx

# View logs
sudo journalctl -u plottwist-backend -f
sudo journalctl -u plottwist-frontend -f
sudo tail -f /var/log/nginx/access.log
```

## 🐳 Docker Alternative

For containerized deployment:

```bash
# Use Docker Compose
cd infrastructure/docker/
cp production.yml docker-compose.yml

# Set environment variables
cp .env.example .env
# Edit .env with your configurations

# Deploy
docker-compose up -d

# Monitor
docker-compose logs -f
```

## 📈 Scaling Considerations

### Horizontal Scaling
- Load balancer (ALB) for multiple instances
- Auto Scaling Groups for dynamic scaling
- RDS for managed database
- CloudFront for CDN

### Performance Optimization
- Redis for caching
- Database connection pooling
- Static asset optimization
- Image compression and optimization

## 🔧 Troubleshooting

### Common Issues

1. **Service not starting**
   ```bash
   sudo journalctl -u plottwist-backend -n 50
   sudo systemctl reset-failed plottwist-backend
   ```

2. **Database connection issues**
   ```bash
   sudo systemctl status postgresql
   sudo -u postgres psql -c "\l"
   ```

3. **SSL certificate issues**
   ```bash
   sudo certbot certificates
   sudo certbot renew --dry-run
   ```

4. **High resource usage**
   ```bash
   htop
   df -h
   free -h
   ```

### Log Locations
- Application logs: `/var/log/plottwist/`
- Nginx logs: `/var/log/nginx/`
- System logs: `/var/log/syslog`

## 📞 Support

For deployment issues:
1. Check the health check script output
2. Review application logs
3. Verify GitHub Actions pipeline status
4. Consult the troubleshooting section

## 🎯 Production Checklist

- [ ] Infrastructure deployed via Terraform
- [ ] GitHub Actions configured and working
- [ ] SSL certificates installed and auto-renewing
- [ ] Health checks passing
- [ ] Monitoring configured
- [ ] Backup strategy implemented
- [ ] Security scan completed
- [ ] Performance testing done
- [ ] Documentation updated

---

**Task 011 Implementation Complete** ✅
- AWS EC2 infrastructure with Terraform
- Production PostgreSQL setup
- Let's Encrypt SSL certificates
- Complete CI/CD pipelines
- Health monitoring and logging
- Security configurations
- Documentation and deployment guides 