#!/bin/bash

# Chef's Training Kitchen - Docker Setup Script
# This script helps you set up and test the Docker deployment locally

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${PURPLE}
🍽️  Chef's Training Kitchen - Docker Setup
============================================${NC}"
}

# Function to check if Docker is installed and running
check_docker() {
    print_status "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker Desktop first."
        echo "Download from: https://www.docker.com/products/docker-desktop"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are ready!"
}

# Function to create environment file
create_env_file() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f ".env.development" ]; then
        cat > .env.development << EOF
# Chef's Training Kitchen - Development Environment
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production-very-long-and-random-string-for-development
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,chef_kitchen_dev_web

# Database Configuration
DATABASE_ENGINE=postgresql
DATABASE_NAME=chef_kitchen_dev
DATABASE_USER=chef_user
DATABASE_PASSWORD=chef_password_dev_123
DATABASE_HOST=db
DATABASE_PORT=5432

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Teams Integration (optional for development)
TEAMS_WEBHOOK_URL=

# Development Settings
DJANGO_LOG_LEVEL=INFO
ENABLE_DEBUG_TOOLBAR=True
EOF
        print_success "Created .env.development file"
    else
        print_warning ".env.development already exists, skipping creation"
    fi
}

# Function to build and start services
start_services() {
    local profile=${1:-""}
    
    print_status "Building Docker images..."
    docker-compose -f docker-compose.dev.yml build --no-cache
    
    print_status "Starting services..."
    if [ -n "$profile" ]; then
        docker-compose -f docker-compose.dev.yml --profile "$profile" up -d
    else
        docker-compose -f docker-compose.dev.yml up -d
    fi
    
    print_status "Waiting for services to be healthy..."
    sleep 10
    
    # Check service health
    check_service_health
}

# Function to check service health
check_service_health() {
    print_status "Checking service health..."
    
    # Check database
    if docker-compose -f docker-compose.dev.yml exec -T db pg_isready -U chef_user -d chef_kitchen_dev &> /dev/null; then
        print_success "✅ Database is healthy"
    else
        print_error "❌ Database is not responding"
        return 1
    fi
    
    # Check Redis
    if docker-compose -f docker-compose.dev.yml exec -T redis redis-cli ping | grep -q PONG; then
        print_success "✅ Redis is healthy"
    else
        print_error "❌ Redis is not responding"
        return 1
    fi
    
    # Check web application
    sleep 5  # Give the web app a moment to start
    if curl -f http://localhost:8000/health/ &> /dev/null; then
        print_success "✅ Web application is healthy"
    else
        print_warning "⚠️  Web application may still be starting..."
        print_status "Checking application logs..."
        docker-compose -f docker-compose.dev.yml logs --tail=20 web
    fi
}

# Function to run database migrations and setup
setup_database() {
    print_status "Setting up database..."
    
    # Run migrations
    docker-compose -f docker-compose.dev.yml exec web python manage.py migrate
    
    # Create superuser if it doesn't exist
    docker-compose -f docker-compose.dev.yml exec web python manage.py shell -c "
from django.contrib.auth.models import User
from accounts.models import UserProfile
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser('admin', 'admin@chefkitchen.local', 'admin123')
    UserProfile.objects.create(user=admin, role='ADMIN')
    print('✅ Admin user created: admin/admin123')
else:
    print('✅ Admin user already exists')
"
    
    # Create sample data
    create_sample_data
    
    print_success "Database setup completed!"
}

# Function to create sample data
create_sample_data() {
    print_status "Creating sample data..."
    
    docker-compose -f docker-compose.dev.yml exec web python manage.py shell -c "
from django.contrib.auth.models import User
from accounts.models import UserProfile
from training_requests.models import TrainingRequest
from datetime import datetime, timedelta

# Create sample users if they don't exist
users_data = [
    ('chef_leader', 'chef.leader@kitchen.local', 'Chef Leader', 'LEADERSHIP'),
    ('sous_chef', 'sous.chef@kitchen.local', 'Sous Chef', 'TEAM_MEMBER'),
    ('line_cook', 'line.cook@kitchen.local', 'Line Cook', 'TEAM_MEMBER'),
]

for username, email, full_name, role in users_data:
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(username, email, 'password123')
        user.first_name = full_name.split()[0]
        user.last_name = ' '.join(full_name.split()[1:])
        user.save()
        UserProfile.objects.create(user=user, role=role)
        print(f'✅ Created user: {username} ({role})')

# Create sample training requests
sample_requests = [
    {
        'title': 'Advanced Knife Skills Workshop',
        'description': 'Learn professional knife techniques and safety procedures',
        'training_type': 'WORKSHOP',
        'estimated_cost': 250.00,
        'start_date': datetime.now().date() + timedelta(days=30),
        'end_date': datetime.now().date() + timedelta(days=31),
        'justification': 'Essential for improving food prep efficiency and safety',
        'status': 'PENDING'
    },
    {
        'title': 'Food Safety Certification',
        'description': 'ServSafe certification course and examination',
        'training_type': 'CERTIFICATION',
        'estimated_cost': 150.00,
        'start_date': datetime.now().date() + timedelta(days=15),
        'end_date': datetime.now().date() + timedelta(days=16),
        'justification': 'Required certification for kitchen staff',
        'status': 'APPROVED'
    },
    {
        'title': 'Pastry Fundamentals Course',
        'description': 'Basic pastry and baking techniques course',
        'training_type': 'COURSE',
        'estimated_cost': 400.00,
        'start_date': datetime.now().date() + timedelta(days=45),
        'end_date': datetime.now().date() + timedelta(days=47),
        'justification': 'Expand dessert menu capabilities',
        'status': 'PENDING'
    }
]

requester = User.objects.get(username='sous_chef')
for req_data in sample_requests:
    if not TrainingRequest.objects.filter(title=req_data['title']).exists():
        TrainingRequest.objects.create(requester=requester, **req_data)
        print(f'✅ Created training request: {req_data[\"title\"]}')

print('🎉 Sample data creation completed!')
"
    
    print_success "Sample data created!"
}

# Function to show service information
show_service_info() {
    print_header
    echo -e "${GREEN}🎉 Chef's Training Kitchen is now running!${NC}"
    echo ""
    echo -e "${CYAN}📋 Service Information:${NC}"
    echo -e "  🌐 Web Application:     ${YELLOW}http://localhost:8000${NC}"
    echo -e "  🗄️  Database Admin:      ${YELLOW}http://localhost:8080${NC} (if admin profile enabled)"
    echo -e "  🔴 Redis Commander:     ${YELLOW}http://localhost:8081${NC} (if admin profile enabled)"
    echo ""
    echo -e "${CYAN}👨‍🍳 Login Credentials:${NC}"
    echo -e "  Admin User:    ${YELLOW}admin / admin123${NC}"
    echo -e "  Chef Leader:   ${YELLOW}chef_leader / password123${NC}"
    echo -e "  Sous Chef:     ${YELLOW}sous_chef / password123${NC}"
    echo -e "  Line Cook:     ${YELLOW}line_cook / password123${NC}"
    echo ""
    echo -e "${CYAN}🛠️  Useful Commands:${NC}"
    echo -e "  View logs:           ${YELLOW}docker-compose -f docker-compose.dev.yml logs -f${NC}"
    echo -e "  Stop services:       ${YELLOW}docker-compose -f docker-compose.dev.yml down${NC}"
    echo -e "  Restart services:    ${YELLOW}docker-compose -f docker-compose.dev.yml restart${NC}"
    echo -e "  Shell access:        ${YELLOW}docker-compose -f docker-compose.dev.yml exec web bash${NC}"
    echo -e "  Django shell:        ${YELLOW}docker-compose -f docker-compose.dev.yml exec web python manage.py shell${NC}"
    echo ""
}

# Function to cleanup
cleanup() {
    print_status "Cleaning up Docker resources..."
    docker-compose -f docker-compose.dev.yml down -v
    docker system prune -f
    print_success "Cleanup completed!"
}

# Main script logic
main() {
    case "${1:-start}" in
        "start")
            print_header
            check_docker
            create_env_file
            start_services
            setup_database
            show_service_info
            ;;
        "start-with-admin")
            print_header
            check_docker
            create_env_file
            start_services "admin"
            setup_database
            show_service_info
            ;;
        "stop")
            print_status "Stopping services..."
            docker-compose -f docker-compose.dev.yml down
            print_success "Services stopped!"
            ;;
        "restart")
            print_status "Restarting services..."
            docker-compose -f docker-compose.dev.yml restart
            print_success "Services restarted!"
            ;;
        "logs")
            docker-compose -f docker-compose.dev.yml logs -f
            ;;
        "shell")
            docker-compose -f docker-compose.dev.yml exec web bash
            ;;
        "django-shell")
            docker-compose -f docker-compose.dev.yml exec web python manage.py shell
            ;;
        "cleanup")
            cleanup
            ;;
        "status")
            docker-compose -f docker-compose.dev.yml ps
            check_service_health
            ;;
        "help"|"-h"|"--help")
            echo -e "${CYAN}Chef's Training Kitchen - Docker Setup Script${NC}"
            echo ""
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  start              Start all services (default)"
            echo "  start-with-admin   Start with admin tools (Adminer, Redis Commander)"
            echo "  stop               Stop all services"
            echo "  restart            Restart all services"
            echo "  logs               Show and follow logs"
            echo "  shell              Open bash shell in web container"
            echo "  django-shell       Open Django shell"
            echo "  status             Show service status and health"
            echo "  cleanup            Stop services and clean up Docker resources"
            echo "  help               Show this help message"
            ;;
        *)
            print_error "Unknown command: $1"
            echo "Use '$0 help' for available commands"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"