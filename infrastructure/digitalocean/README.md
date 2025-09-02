# PlotTwist DigitalOcean Deployment Guide

This guide shows how to deploy PlotTwist to DigitalOcean using Docker and Terraform.

## 🚀 Quick Start

### Prerequisites

1. **DigitalOcean Account** with API token
2. **Terraform** >= 1.0 installed
3. **SSH Key Pair** for droplet access
4. **Domain names** (optional but recommended)

### 1. Get DigitalOcean API Token

1. Go to [DigitalOcean API Tokens](https://cloud.digitalocean.com/account/api/tokens)
2. Click "Generate New Token"
3. Give it a name (e.g., "PlotTwist Deployment")
4. Select "Full Access" or "Read and Write"
5. Copy the token (you'll need it for Terraform)

### 2. Deploy Infrastructure

```bash
# Navigate to terraform directory
cd infrastructure/digitalocean/terraform/

# Initialize Terraform
terraform init

# Create terraform.tfvars file
cat > terraform.tfvars << 'TFVARS'
do_token = "your_digitalocean_api_token_here"
do_region = "nyc1"  # or your preferred region
environment = "production"
droplet_size = "s-1vcpu-1gb"  # $6/month
public_key = "$(cat ~/.ssh/id_rsa.pub)"
db_password = "YourSecurePassword123!"
jwt_secret_key = "YourJWTSecretKey123!"
domain_name = "yourdomain.com"  # Optional
docker_username = "your_dockerhub_username"  # Optional
docker_password = "your_dockerhub_password"  # Optional
TFVARS

# Review the plan
terraform plan

# Deploy
terraform apply
```

### 3. Deploy Application

```bash
# SSH into your droplet
ssh root@<droplet-ip>

# Navigate to application directory
cd /opt/plottwist

# Clone your repositories
git clone https://github.com/your-username/plottwist-backend.git
git clone https://github.com/your-username/plottwist-frontend.git

# Configure environment
cp .env.template .env
nano .env  # Edit with your values

# Deploy
./deploy.sh
```

## 💰 Cost Comparison

| Resource | AWS (t3.micro) | DigitalOcean (s-1vcpu-1gb) |
|----------|----------------|----------------------------|
| Instance | $0.0104/hour | $6/month |
| Storage | $0.10/GB/month | Included |
| Data Transfer | $0.09/GB | 1TB included |
| **Monthly Cost** | ~$7.50 | $6.00 |

## 🔧 Configuration Options

### Droplet Sizes

| Size | vCPUs | RAM | SSD | Price/Month |
|------|-------|-----|-----|-------------|
| s-1vcpu-1gb | 1 | 1GB | 25GB | $6 |
| s-1vcpu-2gb | 1 | 2GB | 50GB | $12 |
| s-2vcpu-2gb | 2 | 2GB | 60GB | $18 |
| s-2vcpu-4gb | 2 | 4GB | 80GB | $24 |

### Regions

- `nyc1` - New York 1
- `nyc3` - New York 3
- `sfo3` - San Francisco 3
- `sgp1` - Singapore 1
- `lon1` - London 1
- `fra1` - Frankfurt 1
- `ams3` - Amsterdam 3

## 🌐 Domain Configuration

### With Domain

1. **Point your domain to the droplet:**
   - `yourdomain.com` → `<droplet-ip>`
   - `api.yourdomain.com` → `<droplet-ip>`

2. **Enable SSL:**
   ```bash
   # On the droplet
   certbot --nginx -d yourdomain.com -d api.yourdomain.com
   ```

### Without Domain

Access your application directly via IP:
- Frontend: `http://<droplet-ip>:3000`
- Backend: `http://<droplet-ip>:8000`
- API Docs: `http://<droplet-ip>:8000/docs`

## 🔍 Monitoring

### Health Check

```bash
# On the droplet
./health-check.sh
```

### Logs

```bash
# View all logs
docker-compose -f docker-compose.fullstack.yml logs

# View specific service logs
docker-compose -f docker-compose.fullstack.yml logs backend
docker-compose -f docker-compose.fullstack.yml logs frontend
docker-compose -f docker-compose.fullstack.yml logs postgres
```

### System Resources

```bash
# Check resource usage
docker stats

# Check disk usage
df -h

# Check memory usage
free -h
```

## 🔄 CI/CD Integration

### GitHub Actions

Add these secrets to your repository:

```
DO_HOST: <droplet-ip>
DO_USERNAME: root
DO_SSH_KEY: <private-ssh-key-content>
BACKEND_URL: http://<droplet-ip>:8000
FRONTEND_URL: http://<droplet-ip>:3000
REACT_APP_API_URL: http://<droplet-ip>:8000/api/v1
```

### Deployment Workflow

```yaml
name: Deploy to DigitalOcean
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to DigitalOcean
        uses: appleboy/ssh-action@v0.1.5
        with:
          host: ${{ secrets.DO_HOST }}
          username: ${{ secrets.DO_USERNAME }}
          key: ${{ secrets.DO_SSH_KEY }}
          script: |
            cd /opt/plottwist
            git pull origin main
            ./deploy.sh
```

## 🛠️ Troubleshooting

### Common Issues

1. **SSH Connection Failed:**
   ```bash
   # Check firewall rules
   # Verify SSH key is correct
   chmod 600 ~/.ssh/plottwist-key
   ```

2. **Docker Build Failed:**
   ```bash
   # Check Docker daemon
   systemctl status docker
   
   # Check disk space
   df -h
   ```

3. **Services Not Starting:**
   ```bash
   # Check logs
   docker-compose -f docker-compose.fullstack.yml logs
   
   # Check environment variables
   cat .env
   ```

4. **Database Connection Issues:**
   ```bash
   # Check PostgreSQL
   docker exec plottwist-postgres pg_isready -U plottwist
   
   # Check network
   docker network ls
   ```

## 🔒 Security Best Practices

1. **Change default passwords**
2. **Use strong JWT secrets**
3. **Enable firewall rules**
4. **Use SSL/TLS certificates**
5. **Regular security updates**
6. **Monitor access logs**
7. **Backup database regularly**

## 📊 Backup Strategy

### Database Backup

```bash
# Create backup script
cat > backup.sh << 'BACKUPEOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec plottwist-postgres pg_dump -U plottwist plottwist > backup_$DATE.sql
gzip backup_$DATE.sql
BACKUPEOF

chmod +x backup.sh

# Schedule daily backups
echo "0 2 * * * /opt/plottwist/backup.sh" | crontab -
```

### Application Backup

```bash
# Backup application data
tar -czf plottwist_backup_$(date +%Y%m%d).tar.gz \
  /opt/plottwist/plottwist-backend \
  /opt/plottwist/plottwist-frontend \
  /opt/plottwist/.env
```

## �� Scaling

### Vertical Scaling

Upgrade droplet size:
```bash
# In Terraform, change droplet_size variable
droplet_size = "s-2vcpu-4gb"  # Upgrade to 2 vCPUs, 4GB RAM

# Apply changes
terraform apply
```

### Horizontal Scaling

For multiple droplets, consider:
- Load balancer
- Database clustering
- Container orchestration (Kubernetes)

## 📞 Support

- [DigitalOcean Documentation](https://docs.digitalocean.com/)
- [Docker Documentation](https://docs.docker.com/)
- [Terraform Documentation](https://www.terraform.io/docs/)
