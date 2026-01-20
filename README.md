# DeepL Translation Frontend

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A privacy-focused web interface for the DeepL translation API, designed for institutional use with enhanced privacy controls and usage tracking.

> ⚠️ **IMPORTANT SECURITY WARNING**
> 
> This service provides **unrestricted access to your DeepL API key**. Every translation request uses your API quota and incurs costs.
> 
> **NEVER expose this service to the public internet without authentication!**
> 
> - This service MUST be deployed behind an authentication proxy (e.g., [Edge-Auth Stack](https://github.com/javidkl/jade-django-0-nginx-auth-stack))
> - Only authenticated users from your organization should have access
> - Unauthorized access could result in significant API costs and quota exhaustion
> - See the [Authentication](#authentication) section for proper deployment

## Overview

This Django-based application provides a user-friendly frontend for DeepL's enterprise translation API. It offers:

- **Privacy-First Design**: All static assets (Bootstrap, jQuery) served locally, no external CDN dependencies
- **Usage Tracking**: Comprehensive statistics on translation requests and character usage
- **Glossary Support**: Manage custom terminology glossaries via Django management commands
- **Internationalization**: Support for multiple interface languages (English, German)
- **Responsive Design**: Mobile-friendly interface using Bootstrap 5
- **Corporate Identity**: Customizable colors and logo via environment variables
- **Production-Ready**: Security hardened, Docker-ready, designed for nginx reverse proxy deployment

## Authentication

This service is designed to work behind the [Edge-Auth Stack](https://github.com/javidkl/jade-django-0-nginx-auth-stack) - a production-ready authentication gateway combining nginx, Keycloak SSO, and OAuth2-proxy.

### Prerequisites

1. Deploy the Edge-Auth Stack first
2. Configure Keycloak realm and client
3. Set up nginx virtual host (see edge-auth-stack documentation)

### Authentication Pattern

This service uses **Pattern B** authentication:
- **All requests are authenticated at nginx level before reaching Django**
- No Django-internal authentication implementation required
- Users are already authenticated when requests reach Django (X-Remote-User header)
- No `@login_required` decorators needed - nginx handles everything

See the [Edge-Auth Stack Django Integration Guide](https://github.com/javidkl/jade-django-0-nginx-auth-stack/blob/main/docs/django-integration.md) for detailed configuration.

### Running Without Authentication (Development)

For local development without the auth stack:
1. Set `DJANGO_DEBUG=True` in your env file
2. Access the service directly at `http://localhost:8000`

## Features

### Translation Interface
- Automatic language detection or manual selection
- Support for German ↔ English translations
- Formality control (formal/informal)
- Custom glossary integration
- Real-time character usage display
- Keyboard shortcut support (Ctrl+Enter to submit)

### Usage Statistics
- Daily, monthly, and yearly usage reports
- Request count and character usage tracking
- Language direction breakdown (DE→EN, EN→DE)
- API quota monitoring

### Glossary Management
- Upload custom terminology CSV files
- List all active glossaries
- Remove outdated glossaries
- Automatic glossary application based on language pair

See [GLOSSARY_MANAGEMENT.md](GLOSSARY_MANAGEMENT.md) for detailed glossary documentation.

### Security Features
- CSRF protection enabled
- Secure session management
- Security headers (XSS filter, content type nosniff, frame options)
- HSTS support for production
- Environment-based configuration (no credentials in code)
- SQL injection protection via Django ORM
- Comprehensive error logging

## Requirements

- Python 3.8+
- Django 4.2+
- DeepL API Pro account (API key required)
- SQLite (default) or PostgreSQL
- Docker and Docker Compose (for containerized deployment)

## Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd poc-deepl
```

### 2. Configure Environment

Copy the sample environment file and configure your settings:

```bash
cp env/deepl.env.sample env/deepl.env
nano env/deepl.env  # Edit with your settings
```

Required settings:
- `DEEPL_AUTHKEY`: Your DeepL API authentication key
- `DJANGO_ALLOWED_HOSTS`: Comma-separated list of allowed domains

**Note**: `DJANGO_SECRET_KEY` is automatically generated on first run and stored securely in a Docker volume. No manual configuration needed!

Optional branding:
- `APP_TITLE_EN`, `APP_TITLE_DE`: Application title (multilingual)
- `ORGANIZATION_NAME_EN`, `ORGANIZATION_NAME_DE`: Your organization name (footer)
- `FOOTER_TEXT`: Custom footer text
- `LOGO_FILENAME`: Logo file in user_files/logo/ directory
- `PRIMARY_COLOR`: Primary brand color (hex without #, e.g., `0d6efd`)
- `SECONDARY_COLOR`: Secondary brand color (hex without #, e.g., `6610f2`)

### 3. Add Logo (Optional)

```bash
cp /path/to/your/logo.png apps/deepl/deeplFrontend/static/logo/
# Update LOGO_FILENAME in env/deepl.env
```

### 4. Run with Docker Compose

```bash
docker-compose up -d
```

The application will be available at `http://localhost:8000` (or configured domain).

**For detailed Docker documentation**, see [DOCKER.md](DOCKER.md).

### 5. Create Database and Run Migrations

```bash
docker-compose exec deepl python manage.py migrate
```

### 6. Collect Static Files

```bash
docker-compose exec deepl python manage.py collectstatic --noinput
```

## Manual Installation (Development)

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
cd apps/deepl
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp ../../env/deepl.env.sample ../../env/deepl.env
# Edit deepl.env with your configuration
```

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Collect Static Files

```bash
python manage.py collectstatic
```

### 6. Run Development Server

```bash
python manage.py runserver
```

Access at `http://127.0.0.1:8000`

## Production Deployment

> ⚠️ **CRITICAL**: Before deploying to production, you MUST set up authentication. Deploy the [Edge-Auth Stack](https://github.com/javidkl/jade-django-0-nginx-auth-stack) first, then connect this service via the shared Docker network.

### Docker + Nginx Setup

1. **Deploy Edge-Auth Stack first** (see [Authentication](#authentication) section)

2. **Configure environment variables** in `env/deepl.env`:
   - Set `DJANGO_DEBUG=False`
   - Configure `DJANGO_ALLOWED_HOSTS`
   - Configure `CSRF_TRUSTED_ORIGINS`
   - Note: `SECRET_KEY` is auto-generated - no manual configuration needed

3. **Update nginx configuration** in `nginx/nginx.conf`:
   - Adjust rate limiting as needed

4. **Deploy**:
   ```bash
   docker-compose up -d
   ```

4. **Create superuser** (optional, for admin access):
   ```bash
   docker-compose exec deepl python manage.py createsuperuser
   ```

### Security Checklist

- [ ] **Authentication proxy deployed** (Edge-Auth Stack or equivalent)
- [ ] Service NOT directly accessible from internet
- [ ] `DEBUG=False` in production
- [ ] `SECRET_KEY` auto-generated (don't set manually)
- [ ] `ALLOWED_HOSTS` configured with your domain only
- [ ] HTTPS enabled (on upstream proxy)
- [ ] `CSRF_TRUSTED_ORIGINS` configured for your domain
- [ ] `DEEPL_AUTHKEY` not in any committed files
- [ ] Regular database backups configured
- [ ] DeepL API usage monitoring enabled

See [SECURITY.md](SECURITY.md) for detailed security guidance.

## Glossary Management

Upload and manage custom terminology glossaries:

```bash
# Upload a glossary
docker-compose exec deepl python manage.py glossary_put glossary.csv "Name" DE EN-GB --comment "Description"

# List all glossaries
docker-compose exec deepl python manage.py glossary_list --verbose

# Remove a glossary
docker-compose exec deepl python manage.py glossary_remove "Name"
```

See [GLOSSARY_MANAGEMENT.md](GLOSSARY_MANAGEMENT.md) for complete documentation.

## Configuration Reference

### Environment Variables

See `env/deepl.env.sample` for all available configuration options.

Key settings:
- **DeepL API**: `DEEPL_AUTHKEY`
- **Django Security**: `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`
- **Branding**: `APP_TITLE_EN`, `APP_TITLE_DE`, `ORGANIZATION_NAME_EN`, `ORGANIZATION_NAME_DE`, `FOOTER_TEXT`, `LOGO_FILENAME`
- **Corporate Identity**: `PRIMARY_COLOR`, `SECONDARY_COLOR` (hex codes without #)
- **Translation**: `TRANSLATION_DETECTION_LEN`, `STATISTICS_DAYS`, `STATISTICS_MONTHS`, `STATISTICS_YEARS`
- **Localization**: `TIME_ZONE`, `LANGUAGE_CODE`

Note: `SECRET_KEY` is auto-generated on first run - do not configure manually.

### Database

The application uses SQLite (`db.sqlite3`) as its database:
- Suitable for low to medium traffic
- No additional setup required
- Includes WAL mode for better concurrency
- Database file is stored in a Docker volume for persistence

## Troubleshooting

### Application won't start
- Check `DEEPL_AUTHKEY` is set correctly
- Check `DJANGO_ALLOWED_HOSTS` includes your domain
- Review logs: `docker-compose logs deepl`

### Translations not working
- Verify DeepL API key is valid
- Check API quota hasn't been exceeded
- Review application logs for API errors

### Glossaries not loading
- Ensure glossaries are uploaded via management command
- Restart application after uploading new glossaries
- Check logs for glossary loading errors
- Verify glossary language pairs match translation direction

### Static files not loading
- Run `python manage.py collectstatic`
- Check nginx configuration
- Verify `STATIC_ROOT` and `STATIC_URL` settings

## Development

### Running Tests

```bash
python manage.py test deeplFrontend
```

### Code Style

Follow PEP 8 guidelines. Format with:
```bash
black apps/deepl/
```

### Database Migrations

After model changes:
```bash
python manage.py makemigrations
python manage.py migrate
```

## Project Structure

```
poc-deepl/
├── apps/deepl/              # Django application
│   ├── deeplFrontend/       # Main app
│   │   ├── management/      # Custom management commands
│   │   ├── static/          # Static files (CSS, JS, logos)
│   │   ├── templates/       # HTML templates
│   │   ├── models.py        # Database models
│   │   ├── views.py         # View logic
│   │   └── forms.py         # Form definitions
│   ├── config/              # Django project settings
│   ├── manage.py            # Django management script
│   └── requirements.txt     # Python dependencies
├── env/                     # Environment configuration
│   └── deepl.env.sample     # Sample environment file
├── nginx/                   # Nginx configuration
├── docker-compose.yml       # Docker orchestration
├── Dockerfile               # Django container
└── GLOSSARY_MANAGEMENT.md   # Glossary documentation
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

This project is licensed under the **Apache License 2.0**.

See [LICENSE](LICENSE) for the full license text.

See [NOTICE](NOTICE) for copyright notices and third-party dependency information.

## Credits

**Author**: David Kleinhans  
**Affiliation**: Jade University of Applied Sciences  
**Contact**: david.kleinhans@jade-hs.de

This project was originally developed at the Alfred Wegener Institute for Polar and Marine Research (AWI) and is now maintained at Jade University of Applied Sciences to provide secure, privacy-focused translation services for research and administrative purposes.

## Support

For issues and questions:
- Check the [Troubleshooting](#troubleshooting) section
- Review [GLOSSARY_MANAGEMENT.md](GLOSSARY_MANAGEMENT.md) for glossary issues
- Check application logs for detailed error messages
- See [SECURITY.md](SECURITY.md) for security-related issues
- Consult [Django documentation](https://docs.djangoproject.com/)
- Consult [DeepL API documentation](https://www.deepl.com/docs-api)

## Changelog

### Version 2.1 (January 2026)
- Added corporate identity customization (colors, logo via environment)
- Added authentication documentation for Edge-Auth Stack integration
- Added SPDX license headers
- Improved documentation for GitHub publication

### Version 2.0 (December 2025)
- Added glossary management system with Django commands
- Implemented environment-based configuration
- Enhanced security with production-ready settings
- Added comprehensive logging
- Refactored templates for better maintainability
- Moved to local static assets (Bootstrap, jQuery)
- Added responsive design improvements
- Implemented configurable branding

### Version 1.0
- Initial release with basic translation functionality
- Usage statistics tracking
- Multi-language interface support
