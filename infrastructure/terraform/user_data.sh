#!/bin/bash
# PlotTwist EC2 Instance User Data Script
# Task 011: Deployment Infrastructure

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
    lsb-release

# Install Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start and enable Docker
systemctl start docker
systemctl enable docker

# Add ubuntu user to docker group
usermod -aG docker ubuntu

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install Node.js (for frontend)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
apt-get install -y nodejs

# Install Python and pip (for backend)
apt-get install -y python3 python3-pip python3-venv

# Install PostgreSQL
apt-get install -y postgresql postgresql-contrib

# Configure PostgreSQL
sudo -u postgres psql -c "CREATE USER plottwist WITH PASSWORD '${db_password}';"
sudo -u postgres psql -c "CREATE DATABASE plottwist OWNER plottwist;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE plottwist TO plottwist;"

# Configure PostgreSQL to accept connections
sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/*/main/postgresql.conf
echo "host    all             plottwist       0.0.0.0/0               md5" >> /etc/postgresql/*/main/pg_hba.conf

# Restart PostgreSQL
systemctl restart postgresql
systemctl enable postgresql

# Install Nginx
apt-get install -y nginx

# Install Certbot for SSL
apt-get install -y certbot python3-certbot-nginx

# Create deployment directory
mkdir -p /opt/plottwist
chown ubuntu:ubuntu /opt/plottwist

# Create environment files
cat > /opt/plottwist/.env.production << EOF
# Production Environment Variables
ENVIRONMENT=production
DATABASE_URL=postgresql://plottwist:${db_password}@localhost:5432/plottwist
JWT_SECRET_KEY=${jwt_secret_key}
FRONTEND_URL=https://${frontend_domain}
BACKEND_URL=https://${backend_domain}
ALLOWED_HOSTS=${backend_domain},${frontend_domain}
EOF

# Create systemd service for backend
cat > /etc/systemd/system/plottwist-backend.service << EOF
[Unit]
Description=PlotTwist Backend API
After=network.target postgresql.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/plottwist/plottwist-backend
Environment=PATH=/opt/plottwist/venv/bin
EnvironmentFile=/opt/plottwist/.env.production
ExecStart=/opt/plottwist/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for frontend
cat > /etc/systemd/system/plottwist-frontend.service << EOF
[Unit]
Description=PlotTwist Frontend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/plottwist/plottwist-frontend
ExecStart=/usr/bin/npm start
Environment=NODE_ENV=production
Environment=PORT=3000
Environment=REACT_APP_API_URL=https://${backend_domain}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx for reverse proxy
cat > /etc/nginx/sites-available/plottwist << EOF
# Frontend configuration
server {
    listen 80;
    server_name ${frontend_domain};
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
}

# Backend API configuration
server {
    listen 80;
    server_name ${backend_domain};
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

# Enable Nginx site
ln -sf /etc/nginx/sites-available/plottwist /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and start Nginx
nginx -t
systemctl restart nginx
systemctl enable nginx

# Create deployment script
cat > /opt/plottwist/deploy.sh << 'EOF'
#!/bin/bash
# PlotTwist Deployment Script

set -e

echo "Starting PlotTwist deployment..."

# Navigate to deployment directory
cd /opt/plottwist

# Clone or update repositories
if [ ! -d "plottwist-backend" ]; then
    git clone https://github.com/palasgaonkar-vishal/plottwist-backend.git
else
    cd plottwist-backend && git pull origin main && cd ..
fi

if [ ! -d "plottwist-frontend" ]; then
    git clone https://github.com/palasgaonkar-vishal/plottwist-frontend.git
else
    cd plottwist-frontend && git pull origin main && cd ..
fi

# Set up Python virtual environment for backend
python3 -m venv venv
source venv/bin/activate

# Install backend dependencies
cd plottwist-backend
pip install -r requirements.txt

# Run database migrations
python -m alembic upgrade head

# Seed database if needed
python seed_database.py

cd ..

# Install frontend dependencies
cd plottwist-frontend
npm install
npm run build

cd ..

# Restart services
sudo systemctl daemon-reload
sudo systemctl restart plottwist-backend
sudo systemctl enable plottwist-backend
sudo systemctl restart plottwist-frontend
sudo systemctl enable plottwist-frontend

echo "Deployment completed successfully!"
EOF

chmod +x /opt/plottwist/deploy.sh
chown ubuntu:ubuntu /opt/plottwist/deploy.sh

# Create SSL setup script
cat > /opt/plottwist/setup-ssl.sh << 'EOF'
#!/bin/bash
# SSL Setup Script for PlotTwist

set -e

echo "Setting up SSL certificates..."

# Obtain SSL certificates
certbot --nginx -d ${frontend_domain} -d ${backend_domain} --non-interactive --agree-tos --email admin@${frontend_domain}

# Set up auto-renewal
systemctl enable certbot.timer

echo "SSL setup completed!"
EOF

chmod +x /opt/plottwist/setup-ssl.sh
chown ubuntu:ubuntu /opt/plottwist/setup-ssl.sh

# Create log directories
mkdir -p /var/log/plottwist
chown ubuntu:ubuntu /var/log/plottwist

# Set up log rotation
cat > /etc/logrotate.d/plottwist << EOF
/var/log/plottwist/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 ubuntu ubuntu
}
EOF

echo "EC2 instance setup completed successfully!"
echo "Next steps:"
echo "1. Run: sudo -u ubuntu /opt/plottwist/deploy.sh"
echo "2. Configure DNS to point domains to this instance"
echo "3. Run: sudo -u ubuntu /opt/plottwist/setup-ssl.sh" 