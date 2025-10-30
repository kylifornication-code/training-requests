# 🐳 Chef's Training Kitchen - Docker Deployment

A complete Docker setup for local development and testing of the Chef's Training Kitchen application.

## 🚀 Quick Start (30 seconds)

```bash
# 1. Start everything
./docker-setup.sh start

# 2. Verify it's working
./verify-docker-setup.sh

# 3. Open your browser
open http://localhost:8000
```

**Login**: `admin` / `admin123`

## 📋 What You Get

### 🍽️ **Complete Restaurant-Themed Application**
- Beautiful restaurant UI with chef branding
- Time-based kitchen greetings
- Restaurant terminology throughout
- Professional color scheme and animations

### 🛠️ **Full Development Stack**
- **Web App**: Django application with restaurant theme
- **Database**: PostgreSQL with sample data
- **Cache**: Redis for sessions and caching
- **Admin Tools**: Database and Redis management interfaces

### 👥 **Pre-configured Users**
- **Admin**: `admin` / `admin123` (Full access)
- **Chef Leader**: `chef_leader` / `password123` (Leadership role)
- **Sous Chef**: `sous_chef` / `password123` (Team member)
- **Line Cook**: `line_cook` / `password123` (Team member)

### 📊 **Sample Data**
- Training requests with different statuses
- User profiles with proper roles
- Restaurant-themed content

## 🎯 Testing Scenarios

### 1. **Fresh Installation Test**
```bash
./docker-setup.sh cleanup
./docker-setup.sh start
./verify-docker-setup.sh
```

### 2. **Feature Testing**
- Login as different users
- Create training requests ("Recipe Orders")
- Test approval workflow
- Verify restaurant theme elements
- Check responsive design

### 3. **Data Persistence Test**
```bash
# Create some data, then restart
./docker-setup.sh restart
# Verify data persists
```

### 4. **Performance Test**
```bash
./verify-docker-setup.sh performance
```

## 🔧 Available Commands

### Setup Commands
```bash
./docker-setup.sh start              # Start all services
./docker-setup.sh start-with-admin   # Include admin tools
./docker-setup.sh stop               # Stop services
./docker-setup.sh restart            # Restart services
./docker-setup.sh cleanup            # Clean everything
```

### Development Commands
```bash
./docker-setup.sh logs               # View logs
./docker-setup.sh shell              # Web container shell
./docker-setup.sh django-shell       # Django shell
./docker-setup.sh status             # Service status
```

### Verification Commands
```bash
./verify-docker-setup.sh             # Basic verification
./verify-docker-setup.sh features    # Feature testing
./verify-docker-setup.sh performance # Performance testing
./verify-docker-setup.sh all         # All tests
```

## 🌐 Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Web App** | http://localhost:8000 | Main application |
| **Health Check** | http://localhost:8000/health/ | Service health |
| **Admin Panel** | http://localhost:8000/admin/ | Django admin |
| **Database Admin** | http://localhost:8080 | Adminer (with admin profile) |
| **Redis Admin** | http://localhost:8081 | Redis Commander (with admin profile) |

## 📁 Docker Files Structure

```
├── Dockerfile.dev              # Development container
├── docker-compose.dev.yml      # Development services
├── docker-compose.override.yml # Local overrides
├── docker-setup.sh            # Setup automation
├── verify-docker-setup.sh     # Verification tests
├── docker/
│   └── init-db.sql            # Database initialization
└── .env.development           # Development environment
```

## 🔍 Troubleshooting

### Common Issues

#### **Port Conflicts**
```bash
# Check what's using ports
lsof -i :8000 :5432 :6379

# Kill conflicting processes
sudo kill -9 <PID>
```

#### **Docker Issues**
```bash
# Restart Docker Desktop
# Clear Docker cache
docker system prune -a

# Reset everything
./docker-setup.sh cleanup
./docker-setup.sh start
```

#### **Application Not Loading**
```bash
# Check logs
./docker-setup.sh logs

# Common solutions:
./docker-setup.sh restart
./verify-docker-setup.sh
```

### Debug Mode
```bash
# Enable verbose logging
# Edit .env.development:
DEBUG=True
DJANGO_LOG_LEVEL=DEBUG

./docker-setup.sh restart
```

## 🎨 Restaurant Theme Features

### Visual Elements
- ✅ Chef's Training Kitchen branding
- ✅ Restaurant color palette (reds, golds, greens)
- ✅ Kitchen terminology ("Recipe Orders", "Chef Approved")
- ✅ Restaurant icons (utensils, chef hat, trophy)
- ✅ Time-based greetings
- ✅ Smooth animations and hover effects

### User Experience
- ✅ Role-based access (Admin, Leadership, Team Member)
- ✅ Intuitive navigation with restaurant metaphors
- ✅ Consistent spacing and professional layout
- ✅ Mobile-responsive design
- ✅ Interactive dashboard with statistics

## 📊 Verification Checklist

Run `./verify-docker-setup.sh` to check:

- [ ] Docker services running
- [ ] Database connectivity
- [ ] Redis connectivity  
- [ ] Web application health
- [ ] Homepage loads with restaurant theme
- [ ] Admin interface accessible
- [ ] Static files served correctly
- [ ] Database migrations applied
- [ ] Admin user created
- [ ] Sample data loaded

## 🚀 Production Deployment

This Docker setup is designed for **development and testing**. For production:

1. Use `docker-compose.prod.yml`
2. Configure proper environment variables
3. Set up SSL certificates
4. Configure reverse proxy (Nginx)
5. Set up monitoring and logging
6. Use production database

See `DEPLOYMENT.md` for production deployment guide.

## 📞 Support

### Getting Help
- Check logs: `./docker-setup.sh logs`
- Run verification: `./verify-docker-setup.sh`
- Reset everything: `./docker-setup.sh cleanup && ./docker-setup.sh start`

### File Issues
- Application bugs: Create GitHub issue
- Docker setup problems: Check `DOCKER_TESTING_GUIDE.md`
- Security concerns: See `SECURITY.md`

---

## 🎉 Success Criteria

Your Docker setup is successful when:
1. ✅ `./verify-docker-setup.sh` passes all tests
2. ✅ Restaurant theme displays correctly
3. ✅ All user roles work properly
4. ✅ Data persists across restarts
5. ✅ Performance is acceptable

**Happy cooking with Docker! 👨‍🍳🐳**