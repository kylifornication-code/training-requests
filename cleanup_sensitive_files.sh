#!/bin/bash

# Chef's Training Kitchen - Sensitive Files Cleanup Script
# This script helps remove sensitive files from git repository

echo "🔒 Chef's Training Kitchen - Security Cleanup Script"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if file exists and remove from git
remove_if_exists() {
    local file=$1
    if [ -f "$file" ]; then
        echo -e "${YELLOW}Found sensitive file: $file${NC}"
        read -p "Remove $file from git tracking? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git rm --cached "$file" 2>/dev/null
            echo -e "${GREEN}✅ Removed $file from git tracking${NC}"
        else
            echo -e "${YELLOW}⚠️  Skipped $file${NC}"
        fi
    fi
}

# Function to check if directory exists and remove from git
remove_dir_if_exists() {
    local dir=$1
    if [ -d "$dir" ]; then
        echo -e "${YELLOW}Found sensitive directory: $dir${NC}"
        read -p "Remove $dir from git tracking? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git rm -r --cached "$dir" 2>/dev/null
            echo -e "${GREEN}✅ Removed $dir from git tracking${NC}"
        else
            echo -e "${YELLOW}⚠️  Skipped $dir${NC}"
        fi
    fi
}

echo "🔍 Checking for sensitive files..."

# Database files
remove_if_exists "db.sqlite3"
remove_if_exists "*.db"

# Environment files (keep templates)
for env_file in .env .env.local .env.development .env.production; do
    remove_if_exists "$env_file"
done

# Session and auth files
remove_if_exists "cookies.txt"
remove_if_exists "session_data"
remove_if_exists "auth_tokens"

# Log files
remove_dir_if_exists "logs"
for log_file in *.log access.log error.log; do
    remove_if_exists "$log_file"
done

# Cache and temporary files
remove_dir_if_exists "__pycache__"
remove_dir_if_exists ".pytest_cache"
remove_dir_if_exists "htmlcov"

# Virtual environments
remove_dir_if_exists "venv"
remove_dir_if_exists "env"
remove_dir_if_exists ".venv"

# Static files (should be generated, not committed)
remove_dir_if_exists "staticfiles"

# Media uploads (user content, should not be in git)
remove_dir_if_exists "media/uploads"
remove_dir_if_exists "media/training_requests"

# IDE files
remove_dir_if_exists ".vscode"
remove_if_exists ".DS_Store"

# SSL certificates and keys
for cert_file in *.pem *.key *.crt *.p12 *.pfx; do
    remove_if_exists "$cert_file"
done

# Backup files
for backup_file in *.bak *.backup *.old *.orig; do
    remove_if_exists "$backup_file"
done

echo ""
echo "🔧 Checking git status..."
git status --porcelain

echo ""
echo "📋 Security Recommendations:"
echo "1. Review and commit the .gitignore file"
echo "2. Create .env.production from .env.production.template"
echo "3. Generate a new SECRET_KEY for production"
echo "4. Set strong database passwords"
echo "5. Configure HTTPS for production deployment"
echo "6. Review the SECURITY.md file for complete guidelines"

echo ""
echo -e "${GREEN}✅ Security cleanup completed!${NC}"
echo "Run 'git add .gitignore SECURITY.md' and commit the security improvements."

# Check if there are any changes to commit
if [ -n "$(git status --porcelain)" ]; then
    echo ""
    read -p "Commit security improvements now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add .gitignore SECURITY.md cleanup_sensitive_files.sh
        git commit -m "🔒 Add comprehensive security configuration

- Add comprehensive .gitignore for Django project
- Add SECURITY.md with security guidelines and best practices
- Add cleanup script for removing sensitive files from git
- Protect environment files, databases, logs, and credentials
- Include deployment security recommendations"
        echo -e "${GREEN}✅ Security improvements committed!${NC}"
    fi
fi