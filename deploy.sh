#!/bin/bash

# Training Request Management System - Production Deployment Script
# This script automates the deployment process for production environments

set -e  # Exit on any error

# Configuration
PROJECT_NAME="training_system"
PROJECT_DIR="/var/www/training_system"
VENV_DIR="$PROJECT_DIR/venv"
REPO_URL="https://github.com/your-username/training-request-system.git"  # Update with your repo
BRANCH="main"
USER="www-data"
GROUP="www-data"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root (use sudo)"
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install system dependencies
install_system_dependencies() {
    log "Installing system dependencies..."
    
    # Update package list
    apt-get update
    
    # Install required packages
    apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        libpq-dev \
        libmysqlclient-dev \
        nginx \
        supervisor \
        git \
        curl \
        certbot \
        python3-certbot-nginx
    
    log "System dependencies installed successfully"
}

# Setup project directory
setup_project_directory() {
    log "Setting up project directory..."
    
    # Create project directory
    mkdir -p "$PROJECT_DIR"
    mkdir -p "$PROJECT_DIR/logs"
    mkdir -p "/var/log/training_system"
    
    # Set permissions
    chown -R "$USER:$GROUP" "$PROJECT_DIR"
    chown -R "$USER:$GROUP" "/var/log/training_system"
    
    log "Project directory setup complete"
}

# Clone or update repository
setup_repository() {
    log "Setting up repository..."
    
    if [ -d "$PROJECT_DIR/.git" ]; then
        log "Repository exists, pulling latest changes..."
        cd "$PROJECT_DIR"
        sudo -u "$USER" git pull origin "$BRANCH"
    else
        log "Cloning repository..."
        sudo -u "$USER" git clone -b "$BRANCH" "$REPO_URL" "$PROJECT_DIR"
    fi
    
    cd "$PROJECT_DIR"
    log "Repository setup complete"
}

# Setup Python virtual environment
setup_virtualenv() {
    log "Setting up Python virtual environment..."
    
    if [ ! -d "$VENV_DIR" ]; then
        sudo -u "$USER" python3 -m venv "$VENV_DIR"
    fi
    
    # Activate virtual environment and install requirements
    sudo -u "$USER" bash -c "
        source '$VENV_DIR/bin/activate'
        pip install --upgrade pip
        pip install -r requirements-prod.txt
    "
    
    log "Virtual environment setup complete"
}

# Setup database
setup_database() {
    log "Setting up database..."
    
    # Check if .env.production exists
    if [ ! -f "$PROJECT_DIR/.env.production" ]; then
        warn ".env.production file not found. Please create it from .env.production.template"
        warn "Database setup skipped - you'll need to configure it manually"
        return
    fi
    
    # Run Django migrations
    sudo -u "$USER" bash -c "
        cd '$PROJECT_DIR'
        source '$VENV_DIR/bin/activate'
        export DJANGO_SETTINGS_MODULE=training_system.settings_production
        python manage.py migrate
        python manage.py collectstatic --noinput
    "
    
    log "Database setup complete"
}

# Create superuser (interactive)
create_superuser() {
    log "Creating Django superuser..."
    
    sudo -u "$USER" bash -c "
        cd '$PROJECT_DIR'
        source '$VENV_DIR/bin/activate'
        export DJANGO_SETTINGS_MODULE=training_system.settings_production
        python manage.py createsuperuser
    "
}

# Setup Gunicorn
setup_gunicorn() {
    log "Setting up Gunicorn..."
    
    # Create Gunicorn configuration
    cat > "$PROJECT_DIR/gunicorn.conf.py" << EOF
# Gunicorn configuration file
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
user = "$USER"
group = "$GROUP"
tmp_upload_dir = None
errorlog = "/var/log/training_system/gunicorn_error.log"
accesslog = "/var/log/training_system/gunicorn_access.log"
access_log_format = '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
loglevel = "info"
EOF
    
    chown "$USER:$GROUP" "$PROJECT_DIR/gunicorn.conf.py"
    
    log "Gunicorn configuration created"
}

# Setup Supervisor
setup_supervisor() {
    log "Setting up Supervisor..."
    
    # Create Supervisor configuration
    cat > "/etc/supervisor/conf.d/training_system.conf" << EOF
[program:training_system]
command=$VENV_DIR/bin/gunicorn training_system.wsgi:application -c $PROJECT_DIR/gunicorn.conf.py
directory=$PROJECT_DIR
user=$USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/training_system/supervisor.log
environment=DJANGO_SETTINGS_MODULE="training_system.settings_production"
EOF
    
    # Reload Supervisor
    supervisorctl reread
    supervisorctl update
    
    log "Supervisor configuration created"
}

# Setup Nginx
setup_nginx() {
    log "Setting up Nginx..."
    
    # Create Nginx configuration
    cat > "/etc/nginx/sites-available/training_system" << EOF
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;  # Update with your domain
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;  # Update with your domain
    
    # SSL configuration (update paths after running certbot)
    # ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    
    # Static files
    location /static/ {
        alias $PROJECT_DIR/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias $PROJECT_DIR/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check endpoint
    location /health/ {
        access_log off;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
    }
}
EOF
    
    # Enable the site
    ln -sf /etc/nginx/sites-available/training_system /etc/nginx/sites-enabled/
    
    # Remove default site if it exists
    rm -f /etc/nginx/sites-enabled/default
    
    # Test Nginx configuration
    nginx -t
    
    log "Nginx configuration created"
}

# Setup SSL with Let's Encrypt
setup_ssl() {
    log "Setting up SSL certificate..."
    
    warn "Please update the domain name in /etc/nginx/sites-available/training_system"
    warn "Then run: certbot --nginx -d your-domain.com -d www.your-domain.com"
    warn "After SSL setup, uncomment the SSL lines in the Nginx configuration"
}

# Setup log rotation
setup_logrotate() {
    log "Setting up log rotation..."
    
    cat > "/etc/logrotate.d/training_system" << EOF
/var/log/training_system/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 $USER $GROUP
    postrotate
        supervisorctl restart training_system
    endscript
}
EOF
    
    log "Log rotation configured"
}

# Main deployment function
deploy() {
    log "Starting deployment of Training Request Management System..."
    
    install_system_dependencies
    setup_project_directory
    setup_repository
    setup_virtualenv
    setup_database
    setup_gunicorn
    setup_supervisor
    setup_nginx
    setup_logrotate
    
    log "Deployment completed successfully!"
    log "Next steps:"
    log "1. Copy .env.production.template to .env.production and configure it"
    log "2. Update domain names in /etc/nginx/sites-available/training_system"
    log "3. Run: systemctl reload nginx"
    log "4. Setup SSL certificate with: certbot --nginx -d your-domain.com"
    log "5. Create superuser with: sudo -u $USER bash -c 'cd $PROJECT_DIR && source venv/bin/activate && python manage.py createsuperuser'"
    log "6. Start services: supervisorctl start training_system"
}

# Update function for existing deployments
update() {
    log "Updating existing deployment..."
    
    cd "$PROJECT_DIR"
    
    # Pull latest changes
    sudo -u "$USER" git pull origin "$BRANCH"
    
    # Update dependencies
    sudo -u "$USER" bash -c "
        source '$VENV_DIR/bin/activate'
        pip install -r requirements-prod.txt
    "
    
    # Run migrations and collect static files
    sudo -u "$USER" bash -c "
        source '$VENV_DIR/bin/activate'
        export DJANGO_SETTINGS_MODULE=training_system.settings_production
        python manage.py migrate
        python manage.py collectstatic --noinput
    "
    
    # Restart services
    supervisorctl restart training_system
    systemctl reload nginx
    
    log "Update completed successfully!"
}

# Script usage
usage() {
    echo "Usage: $0 {deploy|update|create-superuser}"
    echo "  deploy          - Full deployment setup"
    echo "  update          - Update existing deployment"
    echo "  create-superuser - Create Django superuser"
    exit 1
}

# Main script logic
case "$1" in
    deploy)
        deploy
        ;;
    update)
        update
        ;;
    create-superuser)
        create_superuser
        ;;
    *)
        usage
        ;;
esac