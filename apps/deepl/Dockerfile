# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2024-2026 David Kleinhans, Jade University of Applied Sciences
# ==============================================================================
# Dockerfile for DeepL Translation Frontend
# ==============================================================================
# Multi-stage build for optimized production image
# ==============================================================================

FROM python:3.11-slim AS base

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    gosu \
    gettext \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create app user (security: don't run as root)
# Use UID 1000 to match typical host user for volume mount compatibility
RUN groupadd -r -g 1000 appuser && useradd -r -u 1000 -g appuser appuser

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/staticfiles /app/secrets /app/data /app/data/db && \
    chown -R appuser:appuser /app

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Don't switch to non-root user yet - entrypoint needs to fix volume permissions first
# USER directive moved to entrypoint.sh after fixing permissions

# Expose port (informational only)
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"]
