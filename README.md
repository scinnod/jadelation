# DeepL Translation Frontend

A privacy-focused web interface for the DeepL translation API, designed for institutional use with enhanced privacy controls and usage tracking.

## Overview

This Django-based application provides a user-friendly frontend for DeepL's enterprise translation API. It offers:

- **Privacy-First Design**: All static assets (Bootstrap, jQuery) served locally, no external CDN dependencies
- **Usage Tracking**: Comprehensive statistics on translation requests and character usage
- **Glossary Support**: Manage custom terminology glossaries via Django management commands
- **Internationalization**: Support for multiple interface languages (English, German)
- **Responsive Design**: Mobile-friendly interface using Bootstrap 5
- **Production-Ready**: Security hardened, Docker-ready, designed for nginx reverse proxy deployment

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
- `APP_TITLE`: Application title
- `ORGANIZATION_NAME`: Your organization name (footer)
- `FOOTER_TEXT`: Custom footer text
- `LOGO_FILENAME`: Logo file in static/logo/ directory

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

### Docker + Nginx Setup

1. **Configure environment variables** in `env/deepl.env`:
   - Set `DJANGO_DEBUG=False`
   - Configure `DJANGO_ALLOWED_HOSTS`
   - Set strong `DJANGO_SECRET_KEY`
   - Configure `CSRF_TRUSTED_ORIGINS`

2. **Update nginx configuration** in `nginx/nginx.conf`:
   - Set your domain name
   - Configure SSL certificates (recommended)
   - Adjust rate limiting as needed

3. **Deploy**:
   ```bash
   docker-compose up -d
   ```

4. **Create superuser** (optional, for admin access):
   ```bash
   docker-compose exec deepl python manage.py createsuperuser
   ```

### Security Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Use strong `SECRET_KEY` (50+ random characters)
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Set up HTTPS with valid SSL certificates
- [ ] Configure `CSRF_TRUSTED_ORIGINS` for your domain
- [ ] Review and adjust `SECURE_*` settings in settings.py
- [ ] Set up regular database backups
- [ ] Configure log rotation for Django logs
- [ ] Monitor DeepL API usage and quotas
- [ ] Keep dependencies updated

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
- **Django Security**: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`
- **Branding**: `APP_TITLE`, `ORGANIZATION_NAME`, `FOOTER_TEXT`, `LOGO_FILENAME`
- **Translation**: `TRANSLATION_DETECTION_LEN`, `STATISTICS_DAYS`, `STATISTICS_MONTHS`, `STATISTICS_YEARS`
- **Localization**: `TIME_ZONE`, `LANGUAGE_CODE`

### Database

The application uses SQLite (`db.sqlite3`) as its database:
- Suitable for low to medium traffic
- No additional setup required
- Includes WAL mode for better concurrency
- Database file is stored in a Docker volume for persistence

## Troubleshooting

### Application won't start
- Check `DEEPL_AUTHKEY` is set correctly
- Verify `DJANGO_SECRET_KEY` is configured
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

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Specify your license here]

## Credits

**Original Author**: David Kleinhans (Alfred Wegener Institute)

This project was originally developed at the Alfred Wegener Institute for Polar and Marine Research (AWI) to provide secure, privacy-focused translation services for research and administrative purposes.

## Support

For issues and questions:
- Check the [Troubleshooting](#troubleshooting) section
- Review [GLOSSARY_MANAGEMENT.md](GLOSSARY_MANAGEMENT.md) for glossary issues
- Check application logs for detailed error messages
- Consult [Django documentation](https://docs.djangoproject.com/)
- Consult [DeepL API documentation](https://www.deepl.com/docs-api)

## Changelog

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
