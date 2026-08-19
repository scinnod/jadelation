<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2024-2026 David Kleinhans, Jade University of Applied Sciences
-->

# Docker Deployment Guide

This document provides detailed information about the Docker deployment setup for the DeepL Translation Frontend.

> ⚠️ **IMPORTANT**: This service provides unrestricted access to the DeepL API via your API key. It MUST NOT be exposed to the public internet without access control. See [SECURITY.md](../SECURITY.md) for deployment options (authentication proxy or protected network).

## Architecture Overview

The application uses a multi-container Docker setup:

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Host                          │
│                                                         │
│  ┌──────────────┐              ┌──────────────────┐   │
│  │    Nginx     │◄─────────────┤  External Users  │   │
│  │ Reverse Proxy│              └──────────────────┘   │
│  └──────┬───────┘                                      │
│         │                                               │
│         ▼                                               │
│  ┌──────────────────────────────────────────────┐     │
│  │         DeepL Django Application             │     │
│  │                                              │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │     │
│  │  │ Gunicorn │  │  Django  │  │  DeepL   │  │     │
│  │  │  Server  │──┤   ORM    │──┤   API    │  │     │
│  │  └──────────┘  └────┬─────┘  └──────────┘  │     │
│  │                     │                        │     │
│  │                     ▼                        │     │
│  │              ┌──────────────┐               │     │
│  │              │    SQLite    │               │     │
│  │              │   Database   │               │     │
│  │              └──────────────┘               │     │
│  └──────────────────────────────────────────────┘     │
│                                                         │
│  ┌────────────────────────────────────────────────┐   │
│  │          Docker Volumes (Persistent)           │   │
│  │  ┌─────────┐ ┌──────────┐ ┌──────┐ ┌──────┐  │   │
│  │  │ Secrets │ │ Database │ │ Logs │ │Static│  │   │
│  │  └─────────┘ └──────────┘ └──────┘ └──────┘  │   │
│  └────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Best Practices Implemented

### 1. **Security**

#### Non-Root User
- Application runs as non-root user `appuser`
- Reduces attack surface
- Follows security best practices

#### Secret Key Management
- **Automatic Generation**: Secret key auto-generated on first run
- **File-Based Storage**: Stored in `/app/secrets/django_secret_key`
- **Docker Volume**: Persisted in `translation_secrets` volume
- **Restricted Permissions**: File has `600` permissions (owner read/write only)
- **No Environment Exposure**: Not stored in environment variables or logs

#### Security Options
- `no-new-privileges`: Prevents privilege escalation
- Read-only configuration mounts
- Internal network for app communication

### 2. **Reliability**

#### Health Checks
- **Nginx**: HTTP endpoint check every 30s
- **Application**: Django check command every 60s
- Automatic container restart on failure

#### Database Wait Logic
- Waits for external database (PostgreSQL) if configured
- Timeout mechanism (30 seconds)
- Graceful fallback to SQLite

#### Resource Limits
- CPU: 2 cores max, 0.5 reserved
- Memory: 1GB max, 256MB reserved
- Prevents resource starvation

### 3. **Performance**

#### Multi-Stage Build
- Optimized image size
- Separated build dependencies
- Cached layer optimization

#### Static File Serving
- Static files served by Nginx (not Django)
- Shared volume between containers
- Improved performance

#### Gunicorn Configuration
- Multiple worker processes (default: 3)
- Configurable timeout (default: 120s)
- Access and error logging

### 4. **Maintainability**

#### Volume Management
- Separate volumes for different data types:
  - `translation_secrets`: Secret keys
  - `translation_database`: SQLite database
  - `translation_logs`: Application logs
  - `translation_staticfiles`: Collected static files

#### Environment Configuration
- All settings via environment variables
- Sample configuration provided
- Clear documentation

#### Logging
- Structured logging to files
- Separate access and error logs
- Log rotation support

## Container Details

### Nginx Container

**Image**: `nginx:1.27-alpine`  
**Purpose**: Reverse proxy and static file server

**Volumes**:
- `./nginx/nginx.conf`: Main configuration (read-only)
- `./nginx/proxy_params`: Proxy parameters (read-only)
- `./nginx/certs`: SSL certificates (read-only)
- `staticfiles`: Shared static files (read-only)

**Ports**:
- `8000:80` - HTTP
- `8443:443` - HTTPS

**Health Check**: HTTP request to localhost every 30s

**Upload Size Limit**: The `client_max_body_size` directive is set to `55M` to allow document uploads up to 50 MB (the limit enforced by the Django form, plus multipart overhead). If you run an **external reverse proxy** in front of this container, you must configure a matching or higher body size limit there as well — otherwise the outer proxy will reject large uploads with a `413 Request Entity Too Large` error before they reach this nginx.

### DeepL Application Container

**Base Image**: `python:3.12-slim`  
**User**: Non-root (`appuser`)

**Volumes**:
- `secrets`: Secret key storage
- `database`: SQLite database file
- `logs`: Application logs
- `staticfiles`: Collected static files

**Optional Override Volumes** (via `docker-compose.override.yml`):
- `./overrides/about` → `/app/data/about`: Organization-specific about page texts
- `./overrides/logo` → `/app/static/logo`: Organization logo

**Environment Variables**:
- From `env/deepl.env` file
- `SECRET_KEY_FILE`: Path to secret key file
- `GUNICORN_WORKERS`: Number of worker processes
- `GUNICORN_TIMEOUT`: Request timeout
- `GUNICORN_LOG_LEVEL`: Logging verbosity

**Health Check**: Django check command every 60s

## Volume Details

### translation_secrets
**Purpose**: Store Django secret key  
**Path in Container**: `/app/secrets`  
**Contents**: `django_secret_key` file  
**Permissions**: 600 (owner read/write only)

**Backup**: Should be backed up for disaster recovery

### translation_database
**Purpose**: SQLite database file  
**Path in Container**: `/app/data`  
**Contents**: `db.sqlite3`, `db.sqlite3-wal`, `db.sqlite3-shm`

**Backup**: Critical - regular backups recommended

### translation_logs
**Purpose**: Application and server logs  
**Path in Container**: `/app/logs`  
**Contents**:
- `django.log`: Django application logs
- `gunicorn-access.log`: HTTP access logs
- `gunicorn-error.log`: Server error logs

**Maintenance**: Consider log rotation

### translation_staticfiles
**Purpose**: Collected static assets  
**Path in Container**: `/app/staticfiles`  
**Contents**: CSS, JavaScript, images, etc.

**Note**: Can be regenerated with `collectstatic`

## Organization-Specific Customization

The application ships with generic default texts and no logo. Organizations can customize these by using Docker Compose's override mechanism:

### Setup

```bash
# Copy the example override file
cp docker-compose.override.yml.example docker-compose.override.yml

# Add your about texts and logo to the overrides/ directory
# Edit overrides/about/about_de.md and overrides/about/about_en.md
# Copy your logo to overrides/logo/

# Start (override is automatically merged)
docker-compose up -d
```

### How It Works

The `docker-compose.override.yml` mounts files from `overrides/` into the container, replacing the built-in defaults:

| Override Location | Container Path | Purpose |
|-------------------|---------------|---------|
| `overrides/about/` | `/app/data/about/` | About page content (Markdown) |
| `overrides/logo/` | `/app/static/logo/` | Organization logo |

The `overrides/` directory structure is tracked in version control (via `.gitkeep` files), but the actual content files are gitignored to keep organization-specific data out of the repository.

See [overrides/README.md](../overrides/README.md) for details.

## Secret Key Management

### How It Works

1. **First Run**:
   - `entrypoint.sh` checks for secret key file
   - If not found, generates using Django's `get_random_secret_key()`
   - Saves to `/app/secrets/django_secret_key`
   - Sets file permissions to 600

2. **Subsequent Runs**:
   - Reads existing key from file
   - Exports as `DJANGO_SECRET_KEY` environment variable
   - Django reads from environment

3. **Persistence**:
   - File stored in Docker volume `translation_secrets`
   - Survives container restarts and updates
   - Shared across container instances (if scaling)

### Manual Secret Key Management

#### View Current Secret Key
```bash
docker exec translation-app cat /app/secrets/django_secret_key
```

#### Backup Secret Key
```bash
docker cp translation-app:/app/secrets/django_secret_key ./backup/
```

#### Restore Secret Key
```bash
docker cp ./backup/django_secret_key translation-app:/app/secrets/
docker restart translation-app
```

#### Regenerate Secret Key
```bash
# Stop container
docker-compose down

# Remove secret volume
docker volume rm translation_secrets

# Start container (will generate new key)
docker-compose up -d

# WARNING: This will invalidate all sessions!
```

## Deployment Commands

### Initial Deployment

```bash
# 1. Configure environment
cp env/deepl.env.sample env/deepl.env
nano env/deepl.env  # Edit configuration

# 2. Build and start containers
docker-compose up -d

# 3. Check logs
docker-compose logs -f

# 4. Verify health
docker-compose ps
```

### Updates and Maintenance

#### Update Application Code
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose build deepl
docker-compose up -d

# Run migrations if needed
docker-compose exec deepl python manage.py migrate
```

#### View Logs
```bash
# All containers
docker-compose logs -f

# Specific container
docker-compose logs -f deepl
docker-compose logs -f nginx

# Application logs from volume
docker exec translation-app tail -f /app/logs/django.log
```

#### Database Operations
```bash
# Create migration
docker-compose exec deepl python manage.py makemigrations

# Apply migrations
docker-compose exec deepl python manage.py migrate

# Backup database
docker cp translation-app:/app/data/db.sqlite3 ./backup/db.sqlite3

# Restore database
docker cp ./backup/db.sqlite3 translation-app:/app/data/
docker-compose restart deepl
```

#### Manage Glossaries
```bash
# Upload glossary
docker-compose exec deepl python manage.py glossary_put /path/to/glossary.csv "Name" DE EN-GB

# List glossaries
docker-compose exec deepl python manage.py glossary_list --verbose

# Remove glossary
docker-compose exec deepl python manage.py glossary_remove "Name"
```

### Backup and Restore

#### Full Backup
```bash
#!/bin/bash
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup database
docker cp translation-app:/app/data/db.sqlite3 "$BACKUP_DIR/"

# Backup secret key
docker cp translation-app:/app/secrets/django_secret_key "$BACKUP_DIR/"

# Backup environment
cp env/deepl.env "$BACKUP_DIR/"

echo "Backup completed: $BACKUP_DIR"
```

#### Restore from Backup
```bash
#!/bin/bash
BACKUP_DIR="$1"

if [ -z "$BACKUP_DIR" ]; then
  echo "Usage: $0 <backup_directory>"
  exit 1
fi

# Stop application
docker-compose down

# Restore database
docker volume create translation_database
docker run --rm -v translation_database:/data -v "$BACKUP_DIR":/backup alpine cp /backup/db.sqlite3 /data/

# Restore secret key
docker volume create translation_secrets
docker run --rm -v translation_secrets:/secrets -v "$BACKUP_DIR":/backup alpine sh -c "cp /backup/django_secret_key /secrets/ && chmod 600 /secrets/django_secret_key"

# Restore environment
cp "$BACKUP_DIR/deepl.env" env/

# Start application
docker-compose up -d

echo "Restore completed from: $BACKUP_DIR"
```

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose logs deepl

# Common issues:
# - Missing environment file
# - Invalid configuration
# - Permission issues
```

### Secret Key Issues
```bash
# Verify secret key file exists
docker exec translation-app ls -la /app/secrets/

# Check file contents
docker exec translation-app cat /app/secrets/django_secret_key

# Verify environment variable
docker exec translation-app env | grep DJANGO_SECRET_KEY
```

### Database Issues
```bash
# Check database file
docker exec translation-app ls -la /app/data/

# Run migrations
docker-compose exec deepl python manage.py migrate

# Check database integrity
docker exec translation-app python manage.py check --database default
```

### Permission Issues
```bash
# Check file ownership
docker exec translation-app ls -la /app/

# If needed, fix permissions
docker exec -u root translation-app chown -R appuser:appuser /app/data
docker exec -u root translation-app chown -R appuser:appuser /app/secrets
```

## Production Recommendations

1. **SSL/TLS**: Configure HTTPS with valid certificates
2. **Backups**: Implement automated backup solution
3. **Monitoring**: Set up health monitoring and alerting
4. **Log Rotation**: Configure log rotation to prevent disk fill
5. **Resource Tuning**: Adjust CPU/memory limits based on usage
6. **Security Scanning**: Regularly scan images for vulnerabilities
7. **Updates**: Keep base images and dependencies updated
8. **Scaling**: Consider load balancer if scaling horizontally

## Environment Variables Reference

See `env/deepl.env.sample` for complete list.

**Key Variables**:
- `DEEPL_AUTHKEY`: DeepL API key (required)
- `DJANGO_DEBUG`: Debug mode (False for production)
- `DJANGO_ALLOWED_HOSTS`: Allowed domains
- `SECRET_KEY_FILE`: Path to secret key file
- `DATABASE_DIR`: Database directory path
- `GUNICORN_WORKERS`: Number of workers
- `GUNICORN_TIMEOUT`: Request timeout

## Security Checklist

- [ ] Secret key file has 600 permissions
- [ ] Application runs as non-root user
- [ ] Debug mode disabled in production
- [ ] ALLOWED_HOSTS configured correctly
- [ ] HTTPS enabled with valid certificates
- [ ] Regular security updates applied
- [ ] Backups encrypted and stored securely
- [ ] Monitoring and alerting configured
- [ ] Log access restricted
- [ ] DeepL API key stored securely
