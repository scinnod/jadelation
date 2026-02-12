<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2024-2026 David Kleinhans, Jade University of Applied Sciences
-->

# Overrides Directory

This directory contains your **organization-specific files** that replace the defaults built into the application image (in `apps/deepl/data/about/`) or add custom branding.

## Not Version Controlled

**This directory's contents are gitignored.** Only the directory structure (`.gitkeep` files) and this README are tracked. Your organization's files stay local and are never committed to the repository.

## How It Works

```
overrides/                          →  Mounted into container  →  Target path
├── about/about_de.md                                            /app/data/about/
├── about/about_en.md                                            /app/data/about/
└── logo/logo.png                                                /app/static/logo/
```

The `docker-compose.override.yml` file mounts your files **directly into** the container, replacing the defaults. This makes it explicit what gets overwritten.

## Directory Structure

```
overrides/
├── README.md              # This file (tracked)
├── about/
│   ├── .gitkeep           # Tracked (preserves directory structure)
│   ├── about_de.md        # YOUR German about text (not tracked)
│   └── about_en.md        # YOUR English about text (not tracked)
└── logo/
    ├── .gitkeep           # Tracked (preserves directory structure)
    └── logo.png           # YOUR logo (not tracked)
```

## Quick Start

### 1. Set up the override file

```bash
cp docker-compose.override.yml.example docker-compose.override.yml
```

### 2. Add your about texts

Create or edit `overrides/about/about_de.md` and `overrides/about/about_en.md` with your organization-specific text. Use the files in `apps/deepl/data/about/` as a starting point.

### 3. Add your logo (optional)

```bash
cp /path/to/your-logo.png overrides/logo/logo.png
```

Configure the logo filename in `env/deepl.env`:
```bash
LOGO_FILENAME=logo.png
```

### 4. Start the application

```bash
docker-compose up -d
```

## What Can Be Overridden

| Override Location | Replaces | Purpose |
|-------------------|----------|---------|
| `overrides/about/` | `apps/deepl/data/about/` | About page content (Markdown) |
| `overrides/logo/` | Built-in static logo directory | Organization logo |

## Why This Approach?

1. **Explicit** - Reading `docker-compose.override.yml` shows exactly what's replaced
2. **Simple** - No app-level path layering, just filesystem mounts
3. **Clean** - Organization files stay separate from the repository
4. **Safe** - Gitignored content can't accidentally be committed

## See Also

- [docker-compose.override.yml.example](../docker-compose.override.yml.example) - Mount configuration
- [apps/deepl/data/about/](../apps/deepl/data/about/) - Default about texts (built into image)
