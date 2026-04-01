#!/bin/bash
set -e

echo "========================================="
echo "  DesignBid Deployment Script"
echo "========================================="

# 1. Stop and remove existing containers and apps
echo "[1/8] Stopping existing services..."
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true
docker system prune -af 2>/dev/null || true

# Stop any running uvicorn/node processes
pkill -f uvicorn 2>/dev/null || true
pkill -f node 2>/dev/null || true
pkill -f nginx 2>/dev/null || true

# 2. Remove old app files
echo "[2/8] Removing old application files..."
rm -rf /opt/app 2>/dev/null || true
rm -rf /var/www/* 2>/dev/null || true

# 3. Install dependencies
echo "[3/8] Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq git python3 python3-pip python3-venv nodejs npm nginx postgresql postgresql-contrib curl > /dev/null 2>&1

# Ensure PostgreSQL is running
systemctl enable postgresql
systemctl start postgresql

# 4. Clone from GitHub
echo "[4/8] Cloning DesignBid from GitHub..."
mkdir -p /opt/app
cd /opt/app
git clone https://github.com/digitalkookiehub/DesignBid.git
cd DesignBid

# 5. Setup PostgreSQL database
echo "[5/8] Setting up PostgreSQL database..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS designbid;" 2>/dev/null || true
sudo -u postgres psql -c "DROP USER IF EXISTS designbid;" 2>/dev/null || true
sudo -u postgres psql -c "CREATE USER designbid WITH PASSWORD 'designbid_prod_2024';"
sudo -u postgres psql -c "CREATE DATABASE designbid OWNER designbid;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE designbid TO designbid;"

# 6. Setup Backend
echo "[6/8] Setting up backend..."
cd /opt/app/DesignBid/backend

python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip -q
pip install -r requirements.txt -q

# Create backend .env
cat > .env << 'ENVFILE'
DATABASE_URL=postgresql://designbid:designbid_prod_2024@localhost:5432/designbid
SECRET_KEY=dB-pr0d-s3cr3t-k3y-ch4ng3-th1s-2024-x7k9m2
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
FROM_EMAIL=noreply@designbid.com
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760
APP_URL=http://82.112.231.126
API_URL=http://82.112.231.126:8000
ENVFILE

mkdir -p uploads

# Run migrations
alembic upgrade head
echo "Database migrations complete."

deactivate

# 7. Setup Frontend
echo "[7/8] Building frontend..."
cd /opt/app/DesignBid/frontend

# Create frontend .env
cat > .env << 'ENVFILE'
VITE_API_URL=http://82.112.231.126:8000
ENVFILE

npm install --silent
npm run build

# 8. Setup systemd services and nginx
echo "[8/8] Configuring services..."

# Backend systemd service
cat > /etc/systemd/system/designbid-backend.service << 'SVCFILE'
[Unit]
Description=DesignBid Backend API
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/app/DesignBid/backend
ExecStart=/opt/app/DesignBid/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=5
Environment=PATH=/opt/app/DesignBid/backend/venv/bin:/usr/local/bin:/usr/bin

[Install]
WantedBy=multi-user.target
SVCFILE

# Nginx config
cat > /etc/nginx/sites-available/designbid << 'NGINXCONF'
server {
    listen 80;
    server_name 82.112.231.126;

    # Frontend
    root /opt/app/DesignBid/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000;
    }

    # Docs
    location /docs {
        proxy_pass http://127.0.0.1:8000;
    }
    location /redoc {
        proxy_pass http://127.0.0.1:8000;
    }
    location /openapi.json {
        proxy_pass http://127.0.0.1:8000;
    }

    # Uploaded files
    location /uploads/ {
        alias /opt/app/DesignBid/backend/uploads/;
    }

    client_max_body_size 10M;
}
NGINXCONF

# Enable site
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/designbid /etc/nginx/sites-enabled/designbid

# Start services
systemctl daemon-reload
systemctl enable designbid-backend
systemctl start designbid-backend
systemctl restart nginx

echo ""
echo "========================================="
echo "  DEPLOYMENT COMPLETE!"
echo "========================================="
echo ""
echo "  Frontend: http://82.112.231.126"
echo "  Backend:  http://82.112.231.126:8000"
echo "  API Docs: http://82.112.231.126/docs"
echo ""
echo "  Check status:"
echo "    systemctl status designbid-backend"
echo "    systemctl status nginx"
echo "========================================="
