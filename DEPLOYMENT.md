# Training Request Management System - Production Deployment Guide

This guide covers deploying the Training Request Management System to production environments using various deployment methods.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Deployment Methods](#deployment-methods)
   - [Traditional Server Deployment](#traditional-server-deployment)
   - [Docker Deployment](#docker-deployment)
   - [Cloud Platform Deployment](#cloud-platform-deployment)
4. [Post-Deployment Configuration](#post-deployment-configuration)
5. [Monitoring and Maintenance](#monitoring-and-maintenance)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Ubuntu 20.04+ or CentOS 8+ (recommended)
- **Python**: 3.11+
- **Database**: PostgreSQL 13+ or MySQL 8.0+
- **Web Server**: Nginx 1.18+
- **Memory**: Minimum 2GB RAM (4GB+ recommended)
- **Storage**: Minimum 10GB free space
- **SSL Certificate**: Let's Encrypt or commercial certificate

### Domain and DNS

- Domain name pointing to your server
- DNS A record configured
- Optional: CDN setup (CloudFlare, AWS CloudFront)

## Environment Configuration

### 1. Create Environment File

Copy the environment template and configure it:

```bash
cp .env.production.template .env.production
```

### 2. Required Environment Variables

Edit `.env.production` with your specific values:

```bash
# Core Django settings
SECRET_KEY=your-super-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DEBUG=False

# Database (PostgreSQL example)
DATABASE_ENGINE=postgresql
DATABASE_NAME=training_system_prod
DATABASE_USER=training_user
DATABASE_PASSWORD=secure_password_here
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Security
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Microsoft Teams
TEAMS_WEBHOOK_URL=https://your-org.webhook.office.com/webhookb2/your-webhook-url
BASE_URL=https://yourdomain.com
```

## Deployment Methods

### Traditional Server Deployment

#### 1. Automated Deployment Script

The easiest way to deploy is using the provided deployment script:

```bash
# Make the script executable
chmod +x deploy.sh

# Run full deployment
sudo ./deploy.sh deploy

# For updates
sudo ./deploy.sh update
```

#### 2. Manual Deployment Steps

If you prefer manual deployment:

```bash
# 1. Install system dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx postgresql postgresql-contrib supervisor

# 2. Create project directory
sudo mkdir -p /var/www/training_system
sudo chown $USER:$USER /var/www/training_system

# 3. Clone repository
git clone https://github.com/your-repo/training-system.git /var/www/training_system
cd /var/www/training_system

# 4. Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-prod.txt

# 5. Configure environment
cp .env.production.template .env.production
# Edit .env.production with your values

# 6. Setup database
sudo -u postgres createdb training_system_prod
sudo -u postgres createuser training_user
sudo -u postgres psql -c "ALTER USER training_user PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE training_system_prod TO training_user;"

# 7. Run Django setup
export DJANGO_SETTINGS_MODULE=training_system.settings_production
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser

# 8. Setup services (see service configuration files)
```

### Docker Deployment

#### 1. Using Docker Compose

```bash
# 1. Configure environment
cp .env.production.template .env.production
# Edit .env.production

# 2. Build and start services
docker-compose -f docker-compose.prod.yml up -d

# 3. Run initial setup
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# 4. Setup SSL certificates (if using Let's Encrypt)
docker run --rm -v ./nginx/ssl:/etc/letsencrypt certbot/certbot certonly --webroot -w /var/www/certbot -d yourdomain.com
```

#### 2. Docker with External Database

If using an external database service:

```bash
# Modify docker-compose.prod.yml to remove the db service
# Update .env.production with external database credentials
docker-compose -f docker-compose.prod.yml up -d web nginx redis
```

### Cloud Platform Deployment

#### AWS Deployment

1. **EC2 Instance**: Use the traditional deployment method on an EC2 instance
2. **Elastic Beanstalk**: Deploy using the provided `Dockerfile`
3. **ECS/Fargate**: Use the Docker images with ECS task definitions
4. **RDS**: Use managed PostgreSQL for the database
5. **S3**: Configure for static/media file storage

#### Google Cloud Platform

1. **Compute Engine**: Traditional deployment on VM instances
2. **Cloud Run**: Deploy containerized application
3. **Cloud SQL**: Managed PostgreSQL database
4. **Cloud Storage**: For static/media files

#### Azure Deployment

1. **App Service**: Deploy using Docker container
2. **Azure Database**: Managed PostgreSQL
3. **Blob Storage**: For static/media files

## Post-Deployment Configuration

### 1. SSL Certificate Setup

#### Using Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (already configured in deployment script)
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 2. Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Or iptables
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```

### 3. Backup Configuration

```bash
# Database backup script
cat > /usr/local/bin/backup_training_system.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/training_system"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Database backup
pg_dump training_system_prod > $BACKUP_DIR/db_backup_$DATE.sql

# Media files backup
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz /var/www/training_system/media/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
EOF

chmod +x /usr/local/bin/backup_training_system.sh

# Add to crontab
echo "0 2 * * * /usr/local/bin/backup_training_system.sh" | sudo crontab -
```

## Monitoring and Maintenance

### 1. Log Monitoring

```bash
# View application logs
tail -f /var/log/training_system/django.log
tail -f /var/log/training_system/gunicorn_error.log

# View Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# System logs
journalctl -u training_system -f
```

### 2. Performance Monitoring

#### Using Docker with Prometheus/Grafana

```bash
# Start monitoring stack
docker-compose -f docker-compose.prod.yml --profile monitoring up -d

# Access Grafana at http://your-server:3000
# Default login: admin/admin
```

### 3. Health Checks

```bash
# Application health
curl -f http://localhost:8000/health/

# Database connection
python manage.py dbshell

# Static files
curl -I https://yourdomain.com/static/css/style.css
```

### 4. Updates and Maintenance

```bash
# Update application
sudo ./deploy.sh update

# Or manually
cd /var/www/training_system
git pull origin main
source venv/bin/activate
pip install -r requirements-prod.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo supervisorctl restart training_system
```

## Troubleshooting

### Common Issues

#### 1. Static Files Not Loading

```bash
# Check static files collection
python manage.py collectstatic --noinput

# Check Nginx configuration
sudo nginx -t
sudo systemctl reload nginx

# Check file permissions
sudo chown -R www-data:www-data /var/www/training_system/staticfiles/
```

#### 2. Database Connection Issues

```bash
# Test database connection
python manage.py dbshell

# Check PostgreSQL status
sudo systemctl status postgresql

# Check database credentials in .env.production
```

#### 3. SSL Certificate Issues

```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Check Nginx SSL configuration
sudo nginx -t
```

#### 4. Application Not Starting

```bash
# Check Gunicorn logs
tail -f /var/log/training_system/gunicorn_error.log

# Check Supervisor status
sudo supervisorctl status training_system

# Restart services
sudo supervisorctl restart training_system
sudo systemctl reload nginx
```

### Performance Optimization

#### 1. Database Optimization

```sql
-- Create indexes for frequently queried fields
CREATE INDEX idx_training_request_status ON training_requests_trainingrequest(status);
CREATE INDEX idx_training_request_requester ON training_requests_trainingrequest(requester_id);
CREATE INDEX idx_training_request_created ON training_requests_trainingrequest(created_at);
```

#### 2. Caching Configuration

```python
# Add to settings_production.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

#### 3. Static File Optimization

```bash
# Enable Nginx gzip compression (already configured)
# Use CDN for static files
# Optimize images before upload
```

## Security Checklist

- [ ] SSL certificate installed and configured
- [ ] Firewall configured (only necessary ports open)
- [ ] Database access restricted
- [ ] Strong passwords and secret keys
- [ ] Regular security updates
- [ ] Log monitoring configured
- [ ] Backup system in place
- [ ] Rate limiting configured
- [ ] Security headers configured
- [ ] File upload restrictions in place

## Support

For deployment issues:

1. Check the logs first
2. Review this documentation
3. Check Django and Nginx documentation
4. Create an issue in the project repository

Remember to never commit sensitive information like passwords or secret keys to version control!