# Logo Directory

Place your organization's logo file in this directory and configure the filename in your `deepl.env` file.

## Supported Formats
- PNG (.png)
- JPG/JPEG (.jpg, .jpeg)
- SVG (.svg)

## Configuration

Set the `LOGO_FILENAME` variable in your `env/deepl.env` file:

```bash
# Example for PNG logo
LOGO_FILENAME=logo.png

# Example for SVG logo
LOGO_FILENAME=company-logo.svg
```

## Logo Display

- The logo will be displayed in the top-right corner of all pages
- Maximum width can be configured with `LOGO_MAX_WIDTH` (default: 250px)
- The logo is responsive and will scale appropriately on mobile devices
- If `LOGO_FILENAME` is empty or not set, no logo will be displayed

## Example

1. Copy your logo file here:
   ```bash
   cp /path/to/your/logo.png apps/deepl/deeplFrontend/static/logo/
   ```

2. Update your `env/deepl.env`:
   ```bash
   LOGO_FILENAME=logo.png
   LOGO_MAX_WIDTH=250
   ```

3. Run collectstatic (if using in production):
   ```bash
   python manage.py collectstatic
   ```

4. Restart the application to apply changes
