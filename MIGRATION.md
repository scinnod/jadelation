# Migration Guide - Anonymization and Configuration Update

This guide helps you migrate from the hardcoded AWI-specific configuration to the new environment-based configuration system.

## What Changed

### 1. **Removed Hardcoded References**
   - Removed "Alfred Wegener Institute" and "Jade Hochschule" references from templates
   - Removed author name "David Kleinhans" from footer (retained in documentation)
   - Removed hardcoded logo paths

### 2. **New Environment Variables**
   - `APP_TITLE`: Application browser title
   - `ORGANIZATION_NAME`: Your organization name (footer)
   - `FOOTER_TEXT`: Custom footer text with `{year}` placeholder
   - `LOGO_FILENAME`: Logo file in `static/logo/` directory
   - `LOGO_MAX_WIDTH`: Maximum logo width (default: 250px)

### 3. **Template Changes**
   - Logo code moved to `base.html` (DRY principle)
   - Logo display is conditional (only shown if `LOGO_FILENAME` is set)
   - Footer uses environment variables instead of hardcoded text

### 4. **Static Files Structure**
   - New directory: `apps/deepl/deeplFrontend/static/logo/`
   - Old logo path: `static/deeplFrontend/Logo_JadeHochschule_7.jpg`
   - New logo path: `static/logo/your-logo.png` (configurable)

## Migration Steps

### Step 1: Update Environment File

1. **Copy your current `env/deepl.env` to backup:**
   ```bash
   cp env/deepl.env env/deepl.env.backup
   ```

2. **Add new variables to `env/deepl.env`:**
   ```bash
   # Application Branding
   APP_TITLE=DeepL Translation Frontend
   ORGANIZATION_NAME=Your Organization Name
   FOOTER_TEXT={year}+ Translation Service
   LOGO_FILENAME=
   LOGO_MAX_WIDTH=250
   
   # Translation Settings (optional - uses defaults if not set)
   TRANSLATION_DETECTION_LEN=30
   STATISTICS_DAYS=31
   STATISTICS_MONTHS=24
   STATISTICS_YEARS=5
   ```

3. **Customize the values** for your organization

### Step 2: Move Logo File (If Using Logo)

1. **Copy your logo to the new location:**
   ```bash
   # If you have a logo
   cp apps/deepl/deeplFrontend/static/deeplFrontend/Logo_JadeHochschule_7.jpg \
      apps/deepl/deeplFrontend/static/logo/your-logo.jpg
   ```

2. **Update environment variable:**
   ```bash
   # In env/deepl.env
   LOGO_FILENAME=your-logo.jpg
   ```

3. **Or disable logo entirely:**
   ```bash
   # In env/deepl.env
   LOGO_FILENAME=
   ```

### Step 3: Update Database Migration

The new Glossary model requires a database migration:

```bash
# If running in Docker
docker-compose exec deepl python manage.py makemigrations
docker-compose exec deepl python manage.py migrate

# If running locally
python manage.py makemigrations
python manage.py migrate
```

### Step 4: Collect Static Files

```bash
# If running in Docker
docker-compose exec deepl python manage.py collectstatic --noinput

# If running locally
python manage.py collectstatic --noinput
```

### Step 5: Restart Application

```bash
# If running in Docker
docker-compose restart deepl

# If running locally
# Stop and restart your development server
```

## Example Configurations

### Minimal Configuration (No Branding)

```bash
# env/deepl.env
DEEPL_AUTHKEY=your-api-key
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=deepl.example.com

# Minimal branding (no logo, simple footer)
APP_TITLE=Translation Service
ORGANIZATION_NAME=
FOOTER_TEXT={year}+ Translation Service
LOGO_FILENAME=
```

### Full Branding Configuration

```bash
# env/deepl.env
DEEPL_AUTHKEY=your-api-key
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=deepl.example.com

# Full branding
APP_TITLE=ACME Translation Portal
ORGANIZATION_NAME=ACME Corporation
FOOTER_TEXT={year}+ Secure Translation Service
LOGO_FILENAME=acme-logo.png
LOGO_MAX_WIDTH=200
```

### University/Research Configuration

```bash
# env/deepl.env
DEEPL_AUTHKEY=your-api-key
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=translate.university.edu

# University branding
APP_TITLE=University Translation Service
ORGANIZATION_NAME=Example University
FOOTER_TEXT={year}+ Research Translation Services
LOGO_FILENAME=university-seal.svg
LOGO_MAX_WIDTH=180
```

## Verification Checklist

After migration, verify:

- [ ] Application starts without errors
- [ ] Logo displays correctly (or is hidden if not configured)
- [ ] Footer shows correct organization name and year
- [ ] Browser tab shows correct `APP_TITLE`
- [ ] Statistics pages work correctly
- [ ] Translation functionality works
- [ ] All environment variables are set
- [ ] Database migrations completed successfully
- [ ] Static files collected successfully

## Troubleshooting

### Logo not displaying
- Check `LOGO_FILENAME` is set in `env/deepl.env`
- Verify file exists in `apps/deepl/deeplFrontend/static/logo/`
- Run `collectstatic` to copy files to `staticfiles/`
- Check browser console for 404 errors
- Verify filename matches exactly (case-sensitive)

### Footer shows "{year}+"
- Restart the application after changing environment variables
- Check context processor is configured in settings.py
- Verify `FOOTER_TEXT` is set in environment

### "Variable not found" errors
- Ensure all new variables are added to `env/deepl.env`
- Check for typos in variable names
- Restart application after changes

### Static files not loading
- Run: `python manage.py collectstatic`
- Check nginx configuration serves `/static/` correctly
- Verify `STATIC_ROOT` and `STATIC_URL` in settings.py

## Rolling Back

If you need to roll back:

1. **Restore environment file:**
   ```bash
   cp env/deepl.env.backup env/deepl.env
   ```

2. **Restore old logo path** (manual template edit required)

3. **Restart application:**
   ```bash
   docker-compose restart deepl
   ```

Note: The database migration for Glossary model should be kept even if rolling back templates.

## Support

If you encounter issues during migration:

1. Check application logs: `docker-compose logs deepl`
2. Verify environment file syntax
3. Ensure all required variables are set
4. Review this migration guide
5. Consult main README.md for configuration details

## Credits

This migration maintains backward compatibility while allowing flexible branding. The original AWI-specific implementation by David Kleinhans has been generalized for broader use.
