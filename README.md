# DeepL Translation Frontend

[![Django Tests](https://github.com/javidkl/jade-django-1-deepl/actions/workflows/django-tests.yml/badge.svg)](https://github.com/javidkl/jade-django-1-deepl/actions/workflows/django-tests.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A privacy-focused web interface for the DeepL translation API, designed for institutional use with enhanced privacy controls and usage tracking.

> ⚠️ **IMPORTANT SECURITY WARNING**
> 
> This service provides **unrestricted access to the DeepL API via your API key**. Every translation request uses your API quota and incurs costs.
> 
> **NEVER expose this service to the public internet without access control!**
> 
> - Deploy in a **protected network** (VPN, corporate intranet, firewall-restricted LAN) **or** behind an **authentication proxy** (e.g., [Django Auth Stack](https://github.com/scinnod/django-auth-stack))
> - Only users from your organization should be able to reach the service
> - Unauthorized access could result in significant API costs and quota exhaustion
> - See the [Authentication](#authentication) section for deployment options

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

The core requirement is to **prevent unauthenticated access from the public internet**. Two deployment models are supported:

### Option A: Authentication Proxy (internet-facing deployments)

Deploy behind [Django Auth Stack](https://github.com/scinnod/django-auth-stack) — a production-ready gateway combining nginx, Keycloak SSO, and OAuth2-proxy.

**Setup:**
1. Deploy the Django Auth Stack first
2. Configure Keycloak realm and client
3. Set up nginx virtual host (see Django Auth Stack documentation)

**Authentication pattern:** All requests are authenticated at nginx level before reaching Django (X-Remote-User header). No Django-internal authentication or `@login_required` decorators are needed.

See the [Django Auth Stack documentation](https://github.com/scinnod/django-auth-stack) for detailed configuration.

### Option B: Protected Network (VPN / private LAN)

If the service is only reachable inside a trusted network — a corporate intranet, a site-to-site or client VPN, or a home lab — network-level isolation alone may be sufficient. Ensure:

- The host/container is **not** reachable from the public internet (firewall, private VLAN, etc.)
- Network access is restricted to trusted users via VPN gateway or equivalent
- You understand and accept the trust model of your network

In this scenario no application-level authentication proxy is required.

### Local Development

For local development, no authentication setup is needed — the application itself has none. Simply:
1. Set `DJANGO_DEBUG=True` in your env file (enables Django's development mode)
2. Access the service directly at `http://localhost:8000`

### SSO Logout

When deployed behind an SSO proxy (OAuth2-proxy, Keycloak, etc.), users may want to log out of the SSO session. Since this application has no built-in authentication (it relies on the upstream proxy), it provides an optional logout button that redirects to the proxy's logout endpoint.

To enable the logout button:
1. Set `SSO_LOGOUT_URL` in your environment file to your proxy's logout URL
2. The logout link will appear in the footer of all pages

Example configurations:
```bash
# OAuth2-proxy
SSO_LOGOUT_URL=https://auth.example.com/oauth2/sign_out

# Keycloak
SSO_LOGOUT_URL=https://auth.example.com/realms/myrealm/protocol/openid-connect/logout
```

**Note**: The logout is anonymous - no username is displayed since the application doesn't have access to user identity information. Users simply click "logout" to end their SSO session.

## Features

### Translation Interface
- Automatic language detection or manual selection
- Support for German ↔ English translations
- Formality control (formal/informal)
- Custom glossary integration
- Real-time character usage display
- Keyboard shortcut support (Ctrl+Enter to submit)

### Document Translation (Optional)
- Translate entire Word (.docx) and PowerPoint (.pptx) files
- In-place text replacement preserving document structure and formatting
- Automatic file download after translation
- No files stored permanently — temporary files are cleaned up automatically
- Enable via `DOCUMENT_TRANSLATION_ENABLED=True` in the environment file

### Usage Statistics
- Daily, monthly, and yearly usage reports
- Request count and character usage tracking
- Language direction breakdown (DE→EN, EN→DE)
- Document translation share shown per period (visible only to users eligible for document translation)
- API quota monitoring

### Glossary Management
- Upload custom terminology CSV files
- List all active glossaries
- Remove outdated glossaries
- Automatic glossary application based on language pair

See [docs/GLOSSARY_MANAGEMENT.md](docs/GLOSSARY_MANAGEMENT.md) for detailed glossary documentation.

### Security Features
- CSRF protection enabled
- Secure session management
- Security headers (XSS filter, content type nosniff, frame options)
- HSTS support for production
- Environment-based configuration (no credentials in code)
- SQL injection protection via Django ORM
- Configurable maximum translation length to limit API cost per request (`MAX_TRANSLATION_LENGTH`)
- Comprehensive error logging

## Requirements

- Python 3.12+
- Django 5.2+ (LTS)
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
- `APP_TITLE_<LANG>`: Application title per language (`APP_TITLE_EN`, `APP_TITLE_DE`, …)
- `ORGANIZATION_NAME_<LANG>`: Your organization name per language (footer)
- `FOOTER_TEXT`: Custom footer text
- `LOGO_FILENAME`: Logo file in `overrides/logo/` directory (see step 3)
- `PRIMARY_COLOR`: Primary brand color (hex without #, e.g., `0d6efd`)
- `SECONDARY_COLOR`: Secondary brand color (hex without #, e.g., `6610f2`)

Optional SSO integration:
- `SSO_LOGOUT_URL`: Logout URL for upstream SSO proxy (see [SSO Logout](#sso-logout))

### 3. Customize Branding (Optional)

The application supports organization-specific customization via a `docker-compose.override.yml` file that mounts your files into the container:

```bash
# Set up the override mechanism
cp docker-compose.override.yml.example docker-compose.override.yml

# Add your logo
cp /path/to/your/logo.png overrides/logo/logo.png
# Update LOGO_FILENAME in env/deepl.env

# Customize the about page texts
# Edit overrides/about/about_de.md and overrides/about/about_en.md
```

See [overrides/README.md](overrides/README.md) for details on what can be customized.

### 4. Run with Docker Compose

```bash
docker-compose up -d
```

The application will be available at `http://localhost:8000` (or configured domain).

**For detailed Docker documentation**, see [docs/DOCKER.md](docs/DOCKER.md).

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

> ⚠️ **CRITICAL**: Before deploying to production, you MUST set up authentication. Deploy the [Django Auth Stack](https://github.com/scinnod/django-auth-stack) first, then connect this service via the shared Docker network.

### Docker + Nginx Setup

1. **Deploy Django Auth Stack first** (see [Authentication](#authentication) section)

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

- [ ] **Authentication proxy deployed** ([Django Auth Stack](https://github.com/scinnod/django-auth-stack) or equivalent)
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

See [docs/GLOSSARY_MANAGEMENT.md](docs/GLOSSARY_MANAGEMENT.md) for complete documentation.

## Configuration Reference

### Environment Variables

See `env/deepl.env.sample` for all available configuration options.

Key settings:
- **DeepL API**: `DEEPL_AUTHKEY`
- **Django Security**: `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`
- **Branding**: `APP_TITLE_<LANG>`, `ORGANIZATION_NAME_<LANG>`, `FOOTER_TEXT`, `LOGO_FILENAME`
- **Corporate Identity**: `PRIMARY_COLOR`, `SECONDARY_COLOR` (hex codes without #)
- **Translation**: `TRANSLATION_DETECTION_LEN`, `MAX_TRANSLATION_LENGTH`, `STATISTICS_DAYS`, `STATISTICS_MONTHS`, `STATISTICS_YEARS`
- **Document Translation**: `DOCUMENT_TRANSLATION_ENABLED` (set to `True` to enable .docx/.pptx file translation)
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

Tests use pytest with mocked DeepL API calls (no API key needed):

```bash
# With Docker (recommended)
docker-compose exec deepl pip install -r requirements-test.txt
docker-compose exec deepl python -m pytest -v

# With coverage
docker-compose exec deepl python -m pytest --cov=deeplFrontend --cov-report=term-missing
```

Tests also run automatically via GitHub Actions on push/PR. See [docs/TESTING.md](docs/TESTING.md) for details.

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
.
├── apps/deepl/                          # Django application
│   ├── config/                          # Django project settings
│   ├── data/about/                      # Default about page texts (built into image)
│   ├── deeplFrontend/                   # Main app
│   │   ├── management/                  # Custom management commands
│   │   ├── static/                      # Static files (CSS, JS, logos)
│   │   ├── templates/                   # HTML templates
│   │   ├── models.py                    # Database models
│   │   ├── views.py                     # View logic
│   │   └── forms.py                     # Form definitions
│   ├── manage.py                        # Django management script
│   └── requirements.txt                 # Python dependencies
├── env/                                 # Environment configuration
│   └── deepl.env.sample                 # Sample environment file
├── nginx/                               # Nginx configuration
├── overrides/                           # Organization-specific customizations
│   ├── about/                           # Custom about page texts
│   └── logo/                            # Custom logo
├── docs/                                # Documentation
│   ├── DOCKER.md                        # Docker deployment guide
│   ├── GLOSSARY_MANAGEMENT.md           # Glossary documentation
│   ├── DESIGN_PRINCIPLES.md             # Design principles
│   └── TESTING.md                       # Testing guide
├── docker-compose.yml                   # Docker orchestration
└── docker-compose.override.yml.example  # Override template for customization
```

## Documentation

| Document | Description |
|----------|-------------|
| [docs/DOCKER.md](docs/DOCKER.md) | Docker deployment guide |
| [docs/DOCUMENT_TRANSLATION.md](docs/DOCUMENT_TRANSLATION.md) | Document translation (docx/pptx) |
| [docs/GLOSSARY_MANAGEMENT.md](docs/GLOSSARY_MANAGEMENT.md) | Glossary management |
| [docs/DESIGN_PRINCIPLES.md](docs/DESIGN_PRINCIPLES.md) | Design principles |
| [docs/TESTING.md](docs/TESTING.md) | Testing guide |
| [overrides/README.md](overrides/README.md) | Organization-specific customization |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines |
| [SECURITY.md](SECURITY.md) | Security policy |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

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
- Review [docs/GLOSSARY_MANAGEMENT.md](docs/GLOSSARY_MANAGEMENT.md) for glossary issues
- Check application logs for detailed error messages
- See [SECURITY.md](SECURITY.md) for security-related issues
- Consult [Django documentation](https://docs.djangoproject.com/)
- Consult [DeepL API documentation](https://www.deepl.com/docs-api)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for the full version history.
