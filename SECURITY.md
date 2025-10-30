# Security Guidelines for Chef's Training Kitchen

## 🔒 Repository Security

### Files Already Protected by .gitignore
- ✅ Database files (`db.sqlite3`, `*.db`)
- ✅ Environment files (`.env*` except templates)
- ✅ Session data (`cookies.txt`)
- ✅ Log files (`logs/`, `*.log`)
- ✅ Virtual environments (`venv/`, `env/`)
- ✅ Cache and temporary files
- ✅ SSL certificates and keys
- ✅ Static files collected by Django
- ✅ Media uploads
- ✅ IDE configuration files

### 🚨 Files to Remove from Repository (if committed)
If any of these files were previously committed, remove them:

```bash
# Remove sensitive files from git history
git rm --cached db.sqlite3
git rm --cached cookies.txt
git rm --cached .env
git rm --cached *.log
git rm --cached -r logs/
git rm --cached -r __pycache__/
git rm --cached -r venv/
git commit -m "Remove sensitive files from repository"
```

## 🛡️ Environment Configuration

### 1. Production Environment Variables
Create `.env.production` from the template:
```bash
cp .env.production.template .env.production
```

Then update with actual values:
- `SECRET_KEY`: Generate a new Django secret key
- `DATABASE_PASSWORD`: Use a strong database password
- `ALLOWED_HOSTS`: Set to your actual domain(s)
- `TEAMS_WEBHOOK_URL`: Your Microsoft Teams webhook (if using)

### 2. Generate New Secret Key
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### 3. Database Security
- Use strong passwords for database users
- Enable SSL connections in production
- Regularly backup your database
- Limit database user permissions

## 🔐 Django Security Settings

### Required Security Headers (already configured)
```python
# In settings.py
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### HTTPS Configuration (for production)
```python
# Force HTTPS in production
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

## 🚀 Deployment Security

### 1. Server Security
- Keep server OS updated
- Use firewall (ufw/iptables)
- Disable root SSH login
- Use SSH keys instead of passwords
- Regular security updates

### 2. Docker Security (if using)
- Use non-root user in containers
- Scan images for vulnerabilities
- Keep base images updated
- Use multi-stage builds
- Limit container resources

### 3. Nginx Security (if using)
```nginx
# Security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

# Hide server version
server_tokens off;
```

## 📊 Monitoring & Logging

### 1. Security Logging
- Monitor failed login attempts
- Log privilege escalations
- Track file access patterns
- Monitor database queries

### 2. Regular Security Checks
```bash
# Check for security updates
pip list --outdated
pip-audit  # Install with: pip install pip-audit

# Django security check
python manage.py check --deploy
```

## 🔍 Code Security Best Practices

### 1. Input Validation
- Always validate user input
- Use Django forms for validation
- Sanitize file uploads
- Validate file types and sizes

### 2. Authentication & Authorization
- Use Django's built-in authentication
- Implement proper role-based access control
- Use strong password requirements
- Consider two-factor authentication

### 3. Database Security
- Use Django ORM (avoid raw SQL)
- Implement proper permissions
- Regular database backups
- Monitor for SQL injection attempts

## 🚨 Incident Response

### If Security Breach Suspected:
1. **Immediate Actions:**
   - Change all passwords
   - Rotate secret keys
   - Check access logs
   - Disable compromised accounts

2. **Investigation:**
   - Review server logs
   - Check database for unauthorized changes
   - Analyze network traffic
   - Document findings

3. **Recovery:**
   - Restore from clean backups if needed
   - Apply security patches
   - Update security measures
   - Notify stakeholders if required

## 📋 Security Checklist

### Before Deployment:
- [ ] All sensitive data in environment variables
- [ ] Strong secret key generated
- [ ] Database passwords are strong
- [ ] HTTPS configured
- [ ] Security headers enabled
- [ ] Debug mode disabled
- [ ] Allowed hosts configured
- [ ] Static files properly served
- [ ] Media files secured
- [ ] Backup strategy in place

### Regular Maintenance:
- [ ] Update dependencies monthly
- [ ] Review access logs weekly
- [ ] Check for security updates
- [ ] Backup database regularly
- [ ] Monitor error logs
- [ ] Review user permissions
- [ ] Test backup restoration

## 📞 Security Contacts

- **System Administrator:** [Your contact info]
- **Security Team:** [Security team contact]
- **Emergency Contact:** [Emergency contact]

## 📚 Additional Resources

- [Django Security Documentation](https://docs.djangoproject.com/en/stable/topics/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Django Security Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Python Security Best Practices](https://python.org/dev/security/)

---

**Remember:** Security is an ongoing process, not a one-time setup. Regularly review and update your security measures.