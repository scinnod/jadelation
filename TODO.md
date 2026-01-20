# Pre-Publication Checklist

## ⚠️ Critical Security Reminder

**This service provides unrestricted access to your DeepL API key and MUST be deployed behind authentication.**

Every translation uses your API quota and incurs costs. See [SECURITY.md](SECURITY.md) for details.

## Before Publishing

### Security Review

- [x] No hardcoded secrets in code
- [x] No API keys in committed files
- [x] `DEBUG = False` by default in production
- [x] `ALLOWED_HOSTS` configured via environment
- [x] `CSRF_TRUSTED_ORIGINS` configured via environment
- [x] `SECRET_KEY` auto-generated (not manually configured)
- [x] `DEEPL_AUTHKEY` loaded from environment only
- [x] Security warnings in documentation

### Code Quality

- [x] No TODO/FIXME comments with sensitive info
- [x] Test data is generic
- [x] Logging does not expose secrets
- [x] Error messages are safe
- [x] SPDX license headers in key Python files

### Documentation

- [x] README.md is complete and accurate
- [x] Authentication pattern documented
- [x] Environment variables documented
- [x] Deployment instructions clear
- [x] Security warnings prominent

### Files

- [x] LICENSE file present (AGPL-3.0)
- [x] SECURITY.md present
- [x] CONTRIBUTING.md present
- [x] .gitignore comprehensive

## GitHub Repository Setup

### Repository Settings

- [ ] Repository visibility: Public
- [ ] Description: "Privacy-focused DeepL translation frontend for institutional use"
- [ ] Topics: django, deepl, translation, docker, keycloak, privacy
- [ ] License: AGPL-3.0

### Files to Verify Before Push

```bash
# Check for secrets (should return nothing sensitive)
git diff --cached | grep -i "password\|secret\|key\|token\|authkey"

# Verify .gitignore is working
git status

# Check no env files are staged
git diff --cached --name-only | grep -E "\.env$|deepl\.env$"
```

## Post-Publication

- [ ] Verify README renders correctly on GitHub
- [ ] Test clone and deployment instructions
- [ ] Add repository topics
- [ ] Link to edge-auth-stack repository
- [ ] Verify security warning is visible
