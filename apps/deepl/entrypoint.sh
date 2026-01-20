#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2024-2026 David Kleinhans, Jade University of Applied Sciences
# ==============================================================================
# Entrypoint script for DeepL Translation Frontend
# ==============================================================================
set -e

# Color output for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting DeepL Translation Frontend...${NC}"

# ==============================================================================
# Fix Volume Permissions
# ==============================================================================
# Docker volumes are created with root ownership. Fix permissions for appuser.
echo -e "${GREEN}Fixing volume permissions...${NC}"

# Fix permissions for mounted volumes
for dir in /secrets /app/data/db /app/logs /app/staticfiles; do
  if [ -d "$dir" ]; then
    echo -e "${GREEN}Setting ownership for $dir${NC}"
    chown -R appuser:appuser "$dir" 2>/dev/null || true
    chmod -R u+w "$dir" 2>/dev/null || true
  fi
done

# Switch to appuser for remaining operations
echo -e "${GREEN}Switching to appuser...${NC}"

# ==============================================================================
# Secret Key Management
# ==============================================================================
SECRET_KEY_FILE="${SECRET_KEY_FILE:-/secrets/django_secret_key}"

if [ ! -f "$SECRET_KEY_FILE" ]; then
  echo -e "${YELLOW}Secret key file not found. Generating new secret key...${NC}"
  
  # Create secrets directory if it doesn't exist
  mkdir -p "$(dirname "$SECRET_KEY_FILE")"
  
  # Generate secure random secret key using Python (as appuser)
  # This is Django's recommended method
  gosu appuser python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" > "$SECRET_KEY_FILE"
  
  # Set restrictive permissions (readable only by owner)
  chown appuser:appuser "$SECRET_KEY_FILE"
  chmod 600 "$SECRET_KEY_FILE"
  
  echo -e "${GREEN}Secret key generated and saved to: $SECRET_KEY_FILE${NC}"
else
  echo -e "${GREEN}Using existing secret key from: $SECRET_KEY_FILE${NC}"
fi

# Export secret key as environment variable for Django
export DJANGO_SECRET_KEY=$(cat "$SECRET_KEY_FILE")

# ==============================================================================
# Database Wait Logic (if using external database)
# ==============================================================================
if [ -n "$DB_HOST" ] && [ "$DB_HOST" != "NONE" ]; then
  echo -e "${GREEN}Waiting for database $DB_HOST:$DB_PORT...${NC}"
  
  # Wait up to 30 seconds for database
  RETRY=30
  until nc -z "$DB_HOST" "$DB_PORT" || [ $RETRY -eq 0 ]; do
    echo "Database not ready, waiting... ($RETRY attempts left)"
    RETRY=$((RETRY-1))
    sleep 1
  done
  
  if [ $RETRY -eq 0 ]; then
    echo -e "${YELLOW}Warning: Could not connect to database after 30 seconds${NC}"
  else
    echo -e "${GREEN}Database is ready!${NC}"
  fi
else
  echo -e "${GREEN}Using SQLite database (no external database configured)${NC}"
fi

# ==============================================================================
# Database Directory Setup
# ==============================================================================
# Ensure database directory exists and has proper permissions
DATABASE_DIR="/app/data/db"
echo -e "${GREEN}Checking database directory: $DATABASE_DIR${NC}"

if [ ! -d "$DATABASE_DIR" ]; then
  echo -e "${YELLOW}Creating database directory: $DATABASE_DIR${NC}"
  mkdir -p "$DATABASE_DIR" || {
    echo -e "${YELLOW}Warning: Could not create directory $DATABASE_DIR${NC}"
  }
fi

# Test if directory is writable
if [ ! -w "$DATABASE_DIR" ]; then
  echo -e "${YELLOW}Warning: Database directory $DATABASE_DIR is not writable${NC}"
  echo -e "${YELLOW}This may cause database errors. Check volume permissions.${NC}"
else
  echo -e "${GREEN}Database directory is writable${NC}"
fi

# Ensure logs directory exists
if [ ! -d "/app/logs" ]; then
  echo -e "${YELLOW}Creating logs directory: /app/logs${NC}"
  mkdir -p /app/logs
fi

# ==============================================================================
# Django Setup
# ==============================================================================
echo -e "${GREEN}Running database migrations...${NC}"
gosu appuser python manage.py migrate --noinput

echo -e "${GREEN}Collecting static files...${NC}"
gosu appuser python manage.py collectstatic --noinput

# ==============================================================================
# Start Application Server
# ==============================================================================
GUNICORN_WORKERS="${GUNICORN_WORKERS:-3}"
GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-120}"
GUNICORN_LOG_LEVEL="${GUNICORN_LOG_LEVEL:-info}"

echo -e "${GREEN}Starting Gunicorn with $GUNICORN_WORKERS workers...${NC}"

# Run Gunicorn as appuser using gosu for proper signal handling
exec gosu appuser gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "$GUNICORN_WORKERS" \
  --timeout "$GUNICORN_TIMEOUT" \
  --log-level "$GUNICORN_LOG_LEVEL" \
  --access-logfile /app/logs/gunicorn-access.log \
  --error-logfile /app/logs/gunicorn-error.log \
  --capture-output \
  --enable-stdio-inheritance
