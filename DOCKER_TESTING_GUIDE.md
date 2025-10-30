# 🐳 Docker Testing Guide - Chef's Training Kitchen

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- At least 4GB RAM available for Docker
- Ports 8000, 5432, 6379 available on your machine

### 1. One-Command Setup
```bash
./docker-setup.sh start
```

This will:
- ✅ Check Docker installation
- ✅ Create development environment file
- ✅ Build Docker images
- ✅ Start all services (web, database, Redis)
- ✅ Run database migrations
- ✅ Create admin user and sample data
- ✅ Display access information

### 2. Access the Application
- **Web App**: http://localhost:8000
- **Admin Login**: `admin` / `admin123`
- **Health Check**: http://localhost:8000/health/

## 🛠️ Available Commands

### Basic Operations
```bash
# Start all services
./docker-setup.sh start

# Start with admin tools (Adminer, Redis Commander)
./docker-setup.sh start-with-admin

# Stop services
./docker-setup.sh stop

# Restart services
./docker-setup.sh restart

# View logs
./docker-setup.sh logs

# Check service status
./docker-setup.sh status

# Clean up everything
./docker-setup.sh cleanup
```

### Development Tools
```bash
# Open bash shell in web container
./docker-setup.sh shell

# Open Django shell
./docker-setup.sh django-shell

# Manual Docker Compose commands
docker-compose -f docker-compose.dev.yml ps
docker-compose -f docker-compose.dev.yml logs web
docker-compose -f docker-compose.dev.yml exec web python manage.py migrate
```

## 🧪 Testing Scenarios

### 1. Fresh Installation Test
```bash
# Clean slate test
./docker-setup.sh cleanup
./docker-setup.sh start

# Verify:
# - Application loads at http://localhost:8000
# - Admin login works (admin/admin123)
# - Sample data is present
# - All restaurant theme elements are visible
```

### 2. Database Persistence Test
```bash
# Create some data
# 1. Login as admin
# 2. Create a new training request
# 3. Stop and restart services

./docker-setup.sh stop
./docker-setup.sh start

# Verify:
# - Your data is still there
# - Database persisted correctly
```

### 3. Service Health Test
```bash
# Check all services are healthy
./docker-setup.sh status

# Expected output:
# ✅ Database is healthy
# ✅ Redis is healthy  
# ✅ Web application is healthy
```

### 4. Restaurant Theme Test
Visit http://localhost:8000 and verify:
- ✅ "Chef's Training Kitchen" branding
- ✅ Restaurant color scheme (reds, golds, greens)
- ✅ Kitchen terminology ("Recipe Orders", "Chef Approved", etc.)
- ✅ Restaurant icons (utensils, chef hat, etc.)
- ✅ Time-based greetings work
- ✅ All badges and buttons have restaurant styling

### 5. User Role Test
Test different user roles:

**Admin User** (`admin` / `admin123`):
- ✅ Can access all areas
- ✅ Can manage users
- ✅ Can approve/deny requests
- ✅ Restaurant management menu visible

**Leadership User** (`chef_leader` / `password123`):
- ✅ Can access Head Chef dashboard
- ✅ Can approve/deny requests
- ✅ Can view kitchen staff
- ✅ Cannot access admin functions

**Team Member** (`sous_chef` / `password123`):
- ✅ Can create recipe orders
- ✅ Can view own orders
- ✅ Cannot access leadership functions

### 6. Functionality Test Checklist

#### Core Features:
- [ ] User registration and login
- [ ] Create new recipe training order
- [ ] View recipe order list
- [ ] Recipe order approval workflow
- [ ] Dashboard statistics display
- [ ] User management (admin only)
- [ ] Role-based access control

#### Restaurant Theme Features:
- [ ] Navigation hover effects (yellow underlines)
- [ ] Dashboard card animations
- [ ] Status badges with restaurant terminology
- [ ] Time-based kitchen greetings
- [ ] Consistent spacing and padding
- [ ] Mobile responsive design

#### Data Integrity:
- [ ] Database migrations run successfully
- [ ] Sample data loads correctly
- [ ] User sessions persist
- [ ] File uploads work (if applicable)

## 🔧 Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check what's using the ports
lsof -i :8000
lsof -i :5432
lsof -i :6379

# Kill processes if needed
sudo kill -9 <PID>
```

#### Docker Issues
```bash
# Restart Docker Desktop
# Or reset Docker to factory defaults

# Clear Docker cache
docker system prune -a
docker volume prune
```

#### Database Connection Issues
```bash
# Check database logs
docker-compose -f docker-compose.dev.yml logs db

# Reset database
docker-compose -f docker-compose.dev.yml down -v
./docker-setup.sh start
```

#### Web Application Not Starting
```bash
# Check web container logs
docker-compose -f docker-compose.dev.yml logs web

# Common fixes:
# 1. Ensure all dependencies are installed
# 2. Check for Python syntax errors
# 3. Verify database connection
```

### Debug Mode

Enable verbose logging:
```bash
# Edit .env.development
DEBUG=True
DJANGO_LOG_LEVEL=DEBUG

# Restart services
./docker-setup.sh restart
```

## 📊 Performance Testing

### Load Testing (Optional)
```bash
# Install Apache Bench
brew install httpie  # or apt-get install apache2-utils

# Basic load test
ab -n 100 -c 10 http://localhost:8000/

# Test specific endpoints
ab -n 50 -c 5 http://localhost:8000/users/
ab -n 50 -c 5 http://localhost:8000/requests/
```

### Memory Usage
```bash
# Check Docker resource usage
docker stats

# Expected usage:
# - Web container: ~200-400MB
# - Database: ~50-100MB  
# - Redis: ~10-20MB
```

## 🚀 Production Readiness Test

### Environment Variables
```bash
# Test with production-like settings
cp .env.production.template .env.test
# Edit .env.test with test values

# Start with test environment
docker-compose -f docker-compose.prod.yml --env-file .env.test up -d
```

### Security Test
```bash
# Check for exposed secrets
grep -r "password\|secret\|key" . --exclude-dir=venv --exclude-dir=.git

# Verify .gitignore is working
git status --ignored
```

### SSL/HTTPS Test (Production)
```bash
# Test SSL configuration (when deployed)
curl -I https://yourdomain.com
openssl s_client -connect yourdomain.com:443
```

## 📋 Deployment Verification Checklist

Before deploying to production, verify:

### ✅ Docker Setup
- [ ] All containers start successfully
- [ ] Health checks pass
- [ ] Services communicate properly
- [ ] Data persists across restarts
- [ ] Logs are accessible and meaningful

### ✅ Application Features  
- [ ] All user roles work correctly
- [ ] Restaurant theme displays properly
- [ ] Database operations work
- [ ] File uploads/downloads work
- [ ] Email notifications work (if configured)

### ✅ Security
- [ ] No sensitive data in logs
- [ ] Environment variables properly set
- [ ] Database credentials secure
- [ ] Admin interface protected
- [ ] HTTPS configured (production)

### ✅ Performance
- [ ] Application responds quickly
- [ ] Database queries optimized
- [ ] Static files served efficiently
- [ ] Memory usage reasonable

## 🆘 Getting Help

### Logs and Debugging
```bash
# View all logs
./docker-setup.sh logs

# View specific service logs
docker-compose -f docker-compose.dev.yml logs web
docker-compose -f docker-compose.dev.yml logs db
docker-compose -f docker-compose.dev.yml logs redis

# Follow logs in real-time
docker-compose -f docker-compose.dev.yml logs -f web
```

### Container Shell Access
```bash
# Web container shell
./docker-setup.sh shell

# Database shell
docker-compose -f docker-compose.dev.yml exec db psql -U chef_user -d chef_kitchen_dev

# Redis shell
docker-compose -f docker-compose.dev.yml exec redis redis-cli
```

### Reset Everything
```bash
# Nuclear option - reset everything
./docker-setup.sh cleanup
docker system prune -a
docker volume prune
./docker-setup.sh start
```

---

## 🎉 Success Criteria

Your Docker setup is successful when:
1. ✅ All services start without errors
2. ✅ Web application loads with restaurant theme
3. ✅ Admin and user logins work
4. ✅ Database operations complete successfully
5. ✅ All restaurant-themed features display correctly
6. ✅ Services restart cleanly
7. ✅ Data persists across container restarts

**Happy cooking! 👨‍🍳🍽️**