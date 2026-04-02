#!/bin/bash
set -e

echo "========================================="
echo "  DesignBid Docker Deployment"
echo "========================================="

# 1. Clean up ALL previous deployments
echo "[1/5] Cleaning up previous deployments..."
systemctl stop designbid-backend 2>/dev/null || true
systemctl disable designbid-backend 2>/dev/null || true
rm -f /etc/systemd/system/designbid-backend.service
systemctl daemon-reload 2>/dev/null || true
pkill -f uvicorn 2>/dev/null || true
pkill -f node 2>/dev/null || true
systemctl stop nginx 2>/dev/null || true
systemctl disable nginx 2>/dev/null || true
docker compose -f /opt/app/DesignBid/docker-compose.yml down 2>/dev/null || true
docker compose -f /opt/app/DesignerBid/docker-compose.yml down 2>/dev/null || true
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true
docker system prune -af 2>/dev/null || true
docker volume prune -f 2>/dev/null || true
rm -rf /opt/app 2>/dev/null || true
rm -rf /var/www/* 2>/dev/null || true
rm -f /etc/nginx/sites-enabled/designbid 2>/dev/null || true
rm -f /etc/nginx/sites-available/designbid 2>/dev/null || true

# 2. Install Docker if not present
echo "[2/5] Setting up Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
else
    systemctl start docker
fi

if ! docker compose version &> /dev/null; then
    apt-get update -qq
    apt-get install -y -qq docker-compose-plugin > /dev/null 2>&1
fi

# 3. Clone from GitHub
echo "[3/5] Cloning from GitHub..."
mkdir -p /opt/app
cd /opt/app
git clone https://github.com/digitalkookiehub/DesignerBid.git
cd DesignerBid

# 4. Build and start
echo "[4/5] Building and starting containers..."
docker compose up -d --build

# 5. Wait and verify
echo "[5/5] Waiting for services to start..."
sleep 15
docker compose ps

echo ""
echo "========================================="
echo "  DEPLOYMENT COMPLETE!"
echo "========================================="
echo ""
echo "  Frontend: http://optionscreener.online"
echo "  API Docs: http://optionscreener.online/docs"
echo ""
echo "  Useful commands:"
echo "    cd /opt/app/DesignerBid"
echo "    docker compose logs -f"
echo "    docker compose ps"
echo "    docker compose restart"
echo "========================================="
