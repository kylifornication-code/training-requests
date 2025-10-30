# 🔧 Docker Setup Troubleshooting Guide

## Common Issues and Solutions

### 1. **Permission Denied Error**
```bash
# Error: Permission denied
# Solution: Make script executable
chmod +x docker-setup.sh
```

### 2. **Docker Not Running**
```bash
# Error: Cannot connect to Docker daemon
# Solution: Start Docker Desktop
open -a Docker  # macOS
# Or start Docker Desktop manually
```

### 3. **Port Already in Use**
```bash
# Error: Port 8000/5432/6379 already in use
# Solution: Find and kill processes using ports
lsof -i :8000
lsof -i :5432  
lsof -i :6379
sudo kill -9 <PID>
```

### 4. **Docker Compose File Not Found**
```bash
# Error: docker-compose.dev.yml not found
# Solution: Run from project root directory
cd /path/to/eps-training-requests
./docker-setup.sh start
```

### 5. **Build Context Error**
```bash
# Error: Cannot locate specified Dockerfile
# Solution: Ensure Dockerfile.dev exists
ls -la Dockerfile.dev
```

### 6. **Environment File Issues**
```bash
# Error: Environment variable not set
# Solution: Check .env.development file
cat .env.development
```

### 7. **Memory/Disk Space Issues**
```bash
# Error: No space left on device
# Solution: Clean Docker resources
docker system prune -a
docker volume prune
```

## Diagnostic Commands

### Check Docker Status
```bash
# Check Docker installation
docker --version
docker-compose --version

# Check if Docker is running
docker info

# Check available resources
docker system df
```

### Check File Permissions
```bash
# Check script permissions
ls -la docker-setup.sh

# Check Docker files
ls -la Dockerfile.dev docker-compose.dev.yml
```

### Check Port Usage
```bash
# Check if ports are available
netstat -an | grep :8000
netstat -an | grep :5432
netstat -an | grep :6379
```

### Manual Docker Commands
```bash
# Try building manually
docker-compose -f docker-compose.dev.yml build

# Try starting services manually
docker-compose -f docker-compose.dev.yml up -d

# Check service status
docker-compose -f docker-compose.dev.yml ps
```

## Step-by-Step Debugging

### 1. Verify Prerequisites
```bash
# Check Docker Desktop is running
docker info

# Check current directory
pwd
ls -la | grep docker

# Check script permissions
ls -la docker-setup.sh
```

### 2. Try Manual Steps
```bash
# Create environment file manually
cp .env.production.template .env.development

# Build containers manually
docker-compose -f docker-compose.dev.yml build --no-cache

# Start services manually
docker-compose -f docker-compose.dev.yml up -d
```

### 3. Check Logs
```bash
# Check Docker Compose logs
docker-compose -f docker-compose.dev.yml logs

# Check specific service logs
docker-compose -f docker-compose.dev.yml logs web
docker-compose -f docker-compose.dev.yml logs db
```

## Reset Everything
```bash
# Nuclear option - reset all Docker resources
docker-compose -f docker-compose.dev.yml down -v
docker system prune -a
docker volume prune
./docker-setup.sh start
```

## Get Help
If you're still having issues, please provide:
1. The exact error message
2. Your operating system
3. Docker Desktop version
4. Output of `docker info`
5. Output of `ls -la docker-setup.sh`