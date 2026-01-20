<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2024-2026 David Kleinhans, Jade University of Applied Sciences
-->

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

- [x] LICENSE file present (Apache-2.0)
- [x] SECURITY.md present
- [x] CONTRIBUTING.md present
- [x] .gitignore comprehensive
- [x] NOTICE file created

<!-- TODO: Review NOTICE file for complete third-party dependency list -->

## GitHub Repository Setup

### Repository Settings

- [ ] Repository visibility: Public
- [ ] Description: "Privacy-focused DeepL translation frontend for institutional use"
- [ ] Topics: django, deepl, translation, docker, keycloak, privacy
- [ ] License: Apache-2.0

<!-- TODO: Update repository settings on GitHub after license change -->

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
- [ ] Confirm LICENSE file displays correctly on GitHub
- [ ] Review NOTICE file and ensure it's visible to users

## License Migration - TODO Items

### CRITICAL: Review Third-Party Licenses
- [ ] **TODO**: Extract exact versions of all dependencies from requirements.txt
- [ ] **TODO**: Verify license compatibility of each dependency with Apache-2.0
- [ ] **TODO**: Check Django license (BSD-3-Clause) - compatible with Apache-2.0
- [ ] **TODO**: Check deepl library license and add to NOTICE
- [ ] **TODO**: Check gunicorn license and add to NOTICE  
- [ ] **TODO**: Check django-crispy-forms license and add to NOTICE
- [ ] **TODO**: Check crispy-bootstrap5 license and add to NOTICE
- [ ] **TODO**: Check requests library license and add to NOTICE
- [ ] **TODO**: Check markdown library license and add to NOTICE
- [ ] **TODO**: Review Bootstrap exact version in static files and verify MIT license
- [ ] **TODO**: Review jQuery exact version in static files and verify MIT license
- [ ] **TODO**: Document all transitive dependencies if required

### Package Metadata Review
- [ ] **TODO**: Check if project has setup.py or pyproject.toml that needs license update
- [ ] **TODO**: If using pip package metadata, update license classifier to Apache-2.0
- [ ] **TODO**: Review any package.json if Node.js tools are used

### File Header Verification
- [ ] **TODO**: Verify all .py files have SPDX-License-Identifier: Apache-2.0 headers
- [ ] **TODO**: Verify all .md files have SPDX headers in HTML comments
- [ ] **TODO**: Verify all .yml files have SPDX headers
- [ ] **TODO**: Verify all shell scripts have SPDX headers
- [ ] **TODO**: Check for any .html template files that may need license headers
- [ ] **TODO**: Check for any .css or .js files that may need license headers

### Documentation Updates
- [ ] **TODO**: Review all references to "AGPL" or "GNU" in codebase - should be none remaining
- [ ] **TODO**: Update any hardcoded license references in code comments
- [ ] **TODO**: Search for any remaining "copyleft" references and review context
- [ ] **TODO**: Update any developer documentation about license requirements

### Legal and Compliance
- [ ] **TODO**: Ensure contributors are aware of license change (if applicable)
- [ ] **TODO**: Review if any code was contributed under AGPL-3.0 and handle appropriately
- [ ] **TODO**: Verify copyright holder has authority to change license
- [ ] **TODO**: Consider keeping record of license change decision

### Final Verification
- [ ] **TODO**: Run comprehensive search for "AGPL" in all files - should find none except in git history
- [ ] **TODO**: Run comprehensive search for "GPL" in all files
- [ ] **TODO**: Verify NOTICE file is complete with all third-party attributions
- [ ] **TODO**: Double-check Apache-2.0 license text in LICENSE file is complete and unmodified
- [ ] Test clone and deployment instructions
- [ ] Add repository topics
- [ ] Link to edge-auth-stack repository
- [ ] Verify security warning is visible
