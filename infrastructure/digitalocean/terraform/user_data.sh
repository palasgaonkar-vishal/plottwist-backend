#!/bin/bash
# PlotTwist DigitalOcean Droplet User Data Script

set -e

# Update system
apt-get update
apt-get upgrade -y

# Install essential packages
apt-get install -y \
    curl \
    wget \
    git \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    nginx \
    certbot \
    python3-certbot-nginx

# Install Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start and enable Docker
systemctl start docker
systemctl enable docker

# Add root user to docker group
usermod -aG docker root

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create application directory
mkdir -p /opt/plottwist
cd /opt/plottwist

# Create environment file template
cat > .env.template << 'ENVEOF'
# Database Configuration
DB_PASSWORD=your_secure_password_here
POSTGRES_USER=plottwist
POSTGRES_DB=plottwist

# JWT Configuration
JWT_SECRET_KEY=your_jwt_secret_key_here

# Application URLs
FRONTEND_DOMAIN=yourdomain.com
BACKEND_DOMAIN=api.yourdomain.com

# Docker Registry (optional)
DOCKER_USERNAME=your_dockerhub_username
DOCKER_PASSWORD=your_dockerhub_password
ENVEOF

# Create deployment script
cat > deploy.sh << 'DEPLOYEOF'
#!/bin/bash
set -e

echo "🚀 Starting PlotTwist deployment..."

# Check if repositories exist
if [ ! -d "plottwist-backend" ]; then
    echo "❌ Backend repository not found. Please clone it first."
    exit 1
fi

if [ ! -d "plottwist-frontend" ]; then
    echo "❌ Frontend repository not found. Please clone it first."
    exit 1
fi

# Copy environment file
if [ ! -f ".env" ]; then
    echo "📝 Creating environment file from template..."
    cp .env.template .env
    echo "⚠️  Please edit .env file with your actual values before running deployment!"
    exit 1
fi

# Build and deploy
echo "🐳 Building and deploying with Docker Compose..."
docker-compose -f docker-compose.fullstack.yml down || true
docker-compose -f docker-compose.fullstack.yml build --no-cache
docker-compose -f docker-compose.fullstack.yml up -d

echo "✅ Deployment completed!"
echo "🌐 Frontend: http://$(curl -s ifconfig.me):3000"
echo "🔧 Backend: http://$(curl -s ifconfig.me):8000"
echo "📚 API Docs: http://$(curl -s ifconfig.me):8000/docs"
DEPLOYEOF

chmod +x deploy.sh

# Create health check script
cat > health-check.sh << 'HEALTHEOF'
#!/bin/bash
echo "🔍 PlotTwist Health Check"
echo "========================="

# Check Docker
echo "🐳 Docker Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🌐 Service Health:"

# Check backend
if curl -f -s http://localhost:8000/api/v1/health > /dev/null; then
    echo "✅ Backend API: Healthy"
else
    echo "❌ Backend API: Unhealthy"
fi

# Check frontend
if curl -f -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend: Healthy"
else
    echo "❌ Frontend: Unhealthy"
fi

# Check database
if docker exec plottwist-postgres pg_isready -U plottwist -d plottwist > /dev/null 2>&1; then
    echo "✅ Database: Healthy"
else
    echo "❌ Database: Unhealthy"
fi

echo ""
echo "📊 System Resources:"
echo "Memory Usage:"
free -h
echo ""
echo "Disk Usage:"
df -h /
HEALTHEOF

chmod +x health-check.sh

# Create systemd service for auto-start
cat > /etc/systemd/system/plottwist.service << 'SERVICEEOF'
[Unit]
Description=PlotTwist Application
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/plottwist
ExecStart=/usr/local/bin/docker-compose -f docker-compose.fullstack.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.fullstack.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
SERVICEEOF

systemctl daemon-reload
systemctl enable plottwist.service

# Configure Nginx for reverse proxy (optional)
cat > /etc/nginx/sites-available/plottwist << 'NGINXEOF'
server {
    listen 80;
    server_name _;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API Documentation
    location /docs {
        proxy_pass http://localhost:8000/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINXEOF

ln -sf /etc/nginx/sites-available/plottwist /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo "🎉 PlotTwist droplet setup completed!"
echo "📝 Next steps:"
echo "1. SSH into the droplet: ssh root@<droplet-ip>"
echo "2. Clone your repositories in /opt/plottwist/"
echo "3. Edit .env file with your configuration"
echo "4. Run ./deploy.sh to deploy the application"
