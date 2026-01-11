# Design Principles & Development Guidelines

This document outlines the core design principles and development guidelines for this Django project. These principles should be followed by all developers and AI agents working on the codebase.

## Database

- Use **SQLite** for small projects with low concurrency requirements
- Use **PostgreSQL** for production environments with higher load or concurrent users
- Database configuration should be environment-driven via environment variables
- All database migrations must be version-controlled

## Django Framework Compliance

- Code must be compliant with the **latest Django LTS (Long Term Support) version**
- **Never use deprecated methods or features** - always check Django documentation for the current LTS
- Stay informed about deprecation warnings and migrate code proactively
- Future-proof code by following Django's recommended patterns and best practices
- Test compatibility when upgrading between Django versions

## Project Organization

- Follow **Django's recommended project structure and best practices**:
  - Apps should be focused and single-purpose
  - Settings organized logically (use environment variables for configuration)
  - Static files managed through Django's static files system
  - Templates organized within app directories
  - Management commands in `management/commands/` directories
  
## Internationalization (i18n)

- **All user-facing text must use Django's translation features**
  - Use `gettext_lazy()` or `_()` for translatable strings
  - Console/log output is excluded from translation requirements
  - Mark all strings in templates with `{% trans %}` or `{% blocktrans %}`
  - Generate and maintain `.po` files for all supported languages
  - Compile messages to `.mo` files before deployment

## Code Comments

- Templates and JavaScript code should contain **helpful comments for debugging and maintenance**
- Comments should explain **what** the code does and **why**, not detailed implementation
- **Do not reveal system internals** in comments:
  - ✗ Don't mention: "Using Django framework", "DeepL API integration", specific package names
  - ✓ Do mention: "Validates user input", "Formats date for display", "Handles form submission"
- Keep comments concise and relevant - avoid making users curious about system architecture

## Docker & Deployment

### Docker Compose Requirements
- Each project must include a **docker-compose.yml** for orchestration
- Services must be configured to run in the **`proxy` network** without encryption
- Default internal port: **8000** (configurable via environment variables)
- Designed for use with an **upstream proxy server** (e.g., nginx proxy manager)
- Include **nginx service** within docker-compose for:
  - Serving static files efficiently
  - Proxying dynamic requests to the application
  - Making the service self-consistent and production-ready
- Application should **not** handle SSL/TLS (delegated to upstream proxy)
- Use separate networks for isolation:
  - `proxy` network: External network for upstream proxy (must be created manually)
  - Internal network: For communication between nginx and application

### Dockerfile Requirements
- Each project must include a **Dockerfile** for containerization
- Use official **python slim base image** for Django applications (e.g., `python:3.x-slim`)
- Use **hardened and minimal Alpine images** for supporting services (e.g., nginx: `nginx:alpine`)
- Alpine images provide smaller attack surface and reduced image size
- Python slim variant is preferred for Django due to better compatibility with packages
- Minimize image layers and size
- Use multi-stage builds when appropriate
- Set proper working directory and user permissions

### Entrypoint Script
- Include an **entrypoint.sh** script for container initialization
- The entrypoint must handle **secret key generation** automatically:
  - Secret key path: `/secrets/django_secret_key` (mounted as Docker volume)
  - **Store secrets outside the app directory** to prevent exposure
  - Generate key if it doesn't exist
  - Never hardcode secrets

**Example secret key generation in entrypoint.sh:**
```bash
#!/bin/bash
set -e

# Generate Django secret key if it doesn't exist
SECRET_KEY_FILE="${SECRET_KEY_FILE:-/secrets/django_secret_key}"
SECRET_KEY_DIR=$(dirname "$SECRET_KEY_FILE")

if [ ! -f "$SECRET_KEY_FILE" ]; then
    echo "Generating new Django secret key..."
    mkdir -p "$SECRET_KEY_DIR"
    python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())' > "$SECRET_KEY_FILE"
    chmod 600 "$SECRET_KEY_FILE"
    echo "Secret key generated at $SECRET_KEY_FILE"
fi

# Export secret key to environment
export DJANGO_SECRET_KEY=$(cat "$SECRET_KEY_FILE")

# Run database migrations
python manage.py migrate --noprofile

# Collect static files
python manage.py collectstatic --noinput --clear

# Start the application
exec "$@"
```

### Docker Best Practices
- Use Docker volumes for persistent data (databases, secrets, logs, uploads)
- **Mount secrets outside the application directory** (e.g., `/secrets/`) to prevent accidental exposure
- Use Docker networks for service isolation:
  - External `proxy` network for upstream proxy connection
  - Internal network for inter-service communication
- Configure via environment variables and `.env` files
- Never mount application code in production (only in development)
- Use health checks for service monitoring
- Upstream proxy should connect to: `http://<container-name>:8000`

## Code Quality Standards

### Clean Code Principles
- **No workarounds or hacks** - implement proper Docker-native solutions
- If a feature doesn't align with Docker principles, reconsider the approach
- Write code that works naturally within containerized environments
- Avoid host-specific dependencies or assumptions

### Development Philosophy
- **Efficiency**: Optimize for performance without premature optimization
- **Portability**: Code should run identically in dev, staging, and production
- **Sustainability**: Write maintainable code that others can understand
- **Simplicity**: Keep solutions as simple as possible (KISS principle)
  - Solve the problem at hand, not hypothetical future problems
  - Avoid over-engineering - no need to "invent the world formula"
  - Prefer straightforward solutions over clever tricks
  
### Code Review Checklist
- ✓ Uses latest Django LTS features (no deprecated code)
- ✓ User-facing strings are translatable
- ✓ Follows Django project structure conventions
- ✓ Works correctly in Docker environment
- ✓ Configuration via environment variables
- ✓ Comments are helpful but don't reveal internals
- ✓ Code is simple, readable, and maintainable
- ✓ No hardcoded secrets or environment-specific paths

## Version Control

- Commit message should be clear and descriptive
- Never commit secrets, credentials, or sensitive data
- Include `.gitignore` for Python, Django, and Docker artifacts
- Document breaking changes in commit messages

## Testing

- Write tests for business logic and critical paths
- Test with the same database engine used in production
- Test in containerized environment before deployment
- Ensure migrations are reversible and tested

---

**Remember**: These principles exist to ensure code quality, security, and maintainability. When in doubt, choose the simpler, more standard approach that aligns with Django and Docker best practices.
