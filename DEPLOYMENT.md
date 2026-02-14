# Deployment Guide

## Production Deployment Steps

### 1. Server Setup

#### System Requirements
- Ubuntu 20.04+ LTS
- 4GB RAM minimum
- 20GB disk space
- Open ports: 80, 443

#### Install Dependencies
```bash
sudo apt-get update
sudo apt-get install -y \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    postgresql \
    postgresql-contrib \
    redis-server \
    nginx \
    certbot \
    python3-certbot-nginx \
    curl \
    wget
```

### 2. Database Setup

#### PostgreSQL Configuration
```bash
sudo -u postgres psql

CREATE USER restaurant WITH PASSWORD 'secure_password';
CREATE DATABASE restaurant_db OWNER restaurant;

# Enable required extensions
\c restaurant_db
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

\q
```

#### Backup Configuration
```bash
# Create backup script
sudo mkdir -p /backups/postgres
sudo crontab -e

# Add daily backup (3 AM every day)
0 3 * * * pg_dump -U restaurants restaurant_db | gzip > /backups/postgres/backup_$(date +\%Y\%m\%d).sql.gz
```

### 3. Application Setup

#### Clone and Setup
```bash
cd /opt
sudo git clone https://your-repo/restaurant-backend.git
cd restaurant-backend
sudo chown -R $USER:$USER /opt/restaurant-backend

# Setup Python environment
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools
pip install -r requirements.txt
```

#### Environment Configuration
```bash
# Copy and configure .env
cp .env.example .env
nano .env

# Critical settings for production:
DEBUG=False
ENVIRONMENT=production
SECRET_KEY=generate-long-random-string-here
DATABASE_URL=postgresql://restaurant:password@localhost/restaurant_db
ALLOWED_ORIGINS=["https://your-domain.com", "https://www.your-domain.com"]
```

#### Database Migrations
```bash
# Run migrations
alembic upgrade head

# Create initial data
python manage.py create-data
```

### 4. Systemd Service Files

#### Create app service
```bash
sudo nano /etc/systemd/system/restaurant-app.service
```

Add:
```ini
[Unit]
Description=Restaurant Backend Application
After=network.target postgresql.service redis-server.service
Wants=postgresql.service redis-server.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/restaurant-backend
Environment="PATH=/opt/restaurant-backend/venv/bin"
EnvironmentFile=/opt/restaurant-backend/.env
ExecStart=/opt/restaurant-backend/venv/bin/uvicorn app.main:app \
    --host 127.0.0.1 --port 8000 --workers 4 --loop uvloop
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Create Celery service
```bash
sudo nano /etc/systemd/system/restaurant-celery.service
```

Add:
```ini
[Unit]
Description=Restaurant Celery Worker
After=network.target redis-server.service
Wants=redis-server.service

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/opt/restaurant-backend
Environment="PATH=/opt/restaurant-backend/venv/bin"
EnvironmentFile=/opt/restaurant-backend/.env
ExecStart=/opt/restaurant-backend/venv/bin/celery -A app.workers.celery_app worker \
    --loglevel=info --logfile=/var/log/restaurant/celery.log --detach

[Install]
WantedBy=multi-user.target
```

#### Enable Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable restaurant-app restaurant-celery
sudo systemctl start restaurant-app restaurant-celery
sudo systemctl status restaurant-app restaurant-celery
```

### 5. Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/restaurant
```

Add:
```nginx
upstream restaurant_app {
    server 127.0.0.1:8000;
}

# Rate limiting zones
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;
limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=10r/m;

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy strict-origin-when-cross-origin always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    client_max_body_size 10M;

    # Health check
    location /health {
        access_log off;
        proxy_pass http://restaurant_app;
    }

    # Static files
    location /uploads/ {
        alias /opt/restaurant-backend/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Rate limiting
    location /api/auth/ {
        limit_req zone=auth_limit burst=20 nodelay;
        proxy_pass http://restaurant_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        limit_req zone=api_limit burst=100 nodelay;
        proxy_pass http://restaurant_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Root
    location / {
        proxy_pass http://restaurant_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/restaurant /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. SSL Certificate

```bash
sudo certbot certonly --nginx -d your-domain.com -d www.your-domain.com
# Auto-renewal should be enabled by default

# Verify renewal
sudo certbot renew --dry-run
```

### 7. Monitoring & Logging

#### Log Directory
```bash
sudo mkdir -p /var/log/restaurant
sudo chown www-data:www-data /var/log/restaurant
```

#### Application Logs
```bash
sudo journalctl -u restaurant-app -f
sudo journalctl -u restaurant-celery -f
tail -f /var/log/restaurant/celery.log
```

#### Health Monitoring
```bash
# Check app health
curl https://your-domain.com/health

# Monitor system resources
top
free -h
df -h
```

### 8. Database Maintenance

#### Vacuum and Analyze
```bash
# Add to crontab (daily at 2 AM)
0 2 * * * psql -U restaurant restaurant_db -c "VACUUM ANALYZE;"
```

#### Backup Verification
```bash
# Test restore from backup
pg_restore -U restaurant -d test_db /backups/postgres/backup_20240115.sql.gz
```

### 9. Performance Optimization

#### PostgreSQL Tuning
```ini
# /etc/postgresql/14/main/postgresql.conf
shared_buffers = 256MB              # 25% of RAM
effective_cache_size = 1GB          # 2-3% of RAM
maintenance_work_mem = 64MB
work_mem = 16MB
```

#### Redis Configuration
```bash
# /etc/redis/redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
appendonly yes
```

#### Application Settings
```python
# .env
SQLALCHEMY_POOL_SIZE=20
SQLALCHEMY_MAX_OVERFLOW=40
REDIS_CACHE_TTL=3600
```

### 10. Monitoring & Alerts

#### Recommended Services
- **Error Tracking**: Sentry (https://sentry.io)
- **Uptime Monitoring**: UptimeRobot, Pingdom
- **APM**: NewRelic, DataDog
- **Log Aggregation**: ELK Stack, LogRocket

#### Basic Health Check Script
```bash
#!/bin/bash
# /usr/local/bin/check-restaurant-health.sh

ENDPOINT="https://your-domain.com/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $ENDPOINT)

if [ $RESPONSE -ne 200 ]; then
    # Send alert
    echo "Restaurant app is down!" | mail -s "Alert" admin@example.com
    systemctl restart restaurant-app
fi
```

### 11. Backup & Recovery

#### Automated Backups
```bash
#!/bin/bash
# /usr/local/bin/backup-restaurant.sh

BACKUP_DIR="/backups/restaurant"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
pg_dump -U restaurant restaurant_db | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Application files backup
tar -czf $BACKUP_DIR/app_$DATE.tar.gz /opt/restaurant-backend --exclude=venv --exclude=__pycache__

# Keep only last 30 days
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

#### Restore Procedure
```bash
# Restore database
gunzip -c backups/db_20240115_030000.sql.gz | psql -U restaurant restaurant_db

# Restore application
tar -xzf backups/app_20240115_030000.tar.gz -C /opt/

# Restart services
sudo systemctl restart restaurant-app
```

## Docker Production Deployment

### Using Docker Compose
```bash
# Production compose file
docker-compose -f docker-compose.yml up -d

# View logs
docker-compose logs -f app

# Scale services
docker-compose up -d --scale celery=3
```

### Kubernetes (Advanced)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: restaurant-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: restaurant-app
  template:
    metadata:
      labels:
        app: restaurant-app
    spec:
      containers:
      - name: app
        image: restaurant-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: redis_url
```

## Troubleshooting

### App Won't Start
```bash
sudo systemctl status restaurant-app
sudo journalctl -u restaurant-app -n 50

# Check logs
tail -f /var/log/restaurant/app.log
```

### Database Connection Issues
```bash
# Test connection
psql -U restaurant -h localhost -d restaurant_db

# Check if PostgreSQL is running
sudo systemctl status postgresql
```

### High Memory Usage
```bash
# Check processes
ps aux | grep python

# Reduce worker count in .env
WORKERS_COUNT=2  # decrease from 4
```

## Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Set database password to secure value
- [ ] Enable SSL/TLS with Let's Encrypt
- [ ] Configure CORS for production domains
- [ ] Set proper file permissions
- [ ] Disable debug mode
- [ ] Configure firewall rules
- [ ] Setup monitoring and logging
- [ ] Enable automated backups
- [ ] Create admin account with strong password
- [ ] Configure rate limiting
- [ ] Setup CDN for static files
- [ ] Enable database backups
- [ ] Configure error tracking
