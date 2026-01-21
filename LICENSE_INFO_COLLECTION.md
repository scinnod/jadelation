<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2024-2026 David Kleinhans, Jade University of Applied Sciences
-->

# License Information Collection Template

This file is used to collect complete license information for all third-party dependencies.
Once completed, this information will be distributed to the NOTICE file and other documentation.

**Instructions:**
1. Fill in the information for each dependency listed below
2. For Python packages, use `pip show <package>` or check PyPI
3. For JavaScript libraries, check the source files or official websites
4. Verify that all licenses are compatible with Apache-2.0
5. Once complete, inform the assistant to distribute this information

---

## Python Dependencies (from requirements.txt)

### Django
- **Version:** 4.2
- **Copyright:** Django Software Foundation and individual contributors
- **License:** BSD-3-Clause
- **License Compatible with Apache-2.0:** ✓ YES / ☐ VERIFY
- **Source:** https://www.djangoproject.com/
- **License URL:** https://github.com/django/django/blob/main/LICENSE
- **Description:** Web application framework
- **Notes:**
Not shipped with the application but installed by users, isnÄt it?
---

### gunicorn
- **Version:** _______________ (from `pip show gunicorn`)
- **Copyright:** _______________
- **License:** _______________ (typically MIT)
- **License Compatible with Apache-2.0:** ☐ YES / ☐ VERIFY
- **Source:** https://gunicorn.org/
- **License URL:** _______________
- **Description:** WSGI HTTP Server for UNIX
- **Notes:**
Not shipped with the application but installed by users, isnÄt it? Please verify compatibility.

---

### django-crispy-forms
- **Version:** 2.0
- **Copyright:** _______________
- **License:** _______________ (typically MIT)
- **License Compatible with Apache-2.0:** ☐ YES / ☐ VERIFY
- **Source:** https://github.com/django-crispy-forms/django-crispy-forms
- **License URL:** _______________
- **Description:** Django forms rendering
- **Notes:**
Not shipped with the application but installed by users, isnÄt it? Please verify compatibility.

---

### crispy-bootstrap5
- **Version:** 0.7
- **Copyright:** _______________
- **License:** _______________ (typically MIT)
- **License Compatible with Apache-2.0:** ☐ YES / ☐ VERIFY
- **Source:** https://github.com/django-crispy-forms/crispy-bootstrap5
- **License URL:** _______________
- **Description:** Bootstrap 5 template pack for django-crispy-forms
- **Notes:**
Not shipped with the application but installed by users, isnÄt it? Please verify compatibility.

---

### pytz
- **Version:** _______________ (from `pip show pytz`)
- **Copyright:** _______________
- **License:** _______________ (typically MIT)
- **License Compatible with Apache-2.0:** ☐ YES / ☐ VERIFY
- **Source:** https://pypi.org/project/pytz/
- **License URL:** _______________
- **Description:** World timezone definitions for Python
- **Notes:**
Not shipped with the application but installed by users, isnÄt it? Please verify compatibility.

---

### python-dateutil
- **Version:** _______________ (from `pip show python-dateutil`)
- **Copyright:** _______________
- **License:** _______________ (typically Apache-2.0 or BSD)
- **License Compatible with Apache-2.0:** ☐ YES / ☐ VERIFY
- **Source:** https://github.com/dateutil/dateutil
- **License URL:** _______________
- **Description:** Extensions to the standard Python datetime module
- **Notes:**
Not shipped with the application but installed by users, isnÄt it? Please verify compatibility.

---

### requests
- **Version:** _______________ (from `pip show requests`)
- **Copyright:** _______________
- **License:** _______________ (typically Apache-2.0)
- **License Compatible with Apache-2.0:** ☐ YES / ☐ VERIFY
- **Source:** https://requests.readthedocs.io/
- **License URL:** _______________
- **Description:** HTTP library for Python
- **Notes:**
Not shipped with the application but installed by users, isnÄt it? Please verify compatibility.

---

### deepl
- **Version:** _______________ (from `pip show deepl`)
- **Copyright:** DeepL SE
- **License:** _______________ (CHECK: likely MIT or Apache-2.0)
- **License Compatible with Apache-2.0:** ☐ YES / ☐ VERIFY
- **Source:** https://github.com/DeepLcom/deepl-python
- **License URL:** _______________
- **Description:** Official DeepL API client library
- **Notes:** CRITICAL - Verify this is the official client and check license
Not shipped with the application but installed by users, isnÄt it? Please verify compatibility.

---

### markdown
- **Version:** _______________ (from `pip show markdown`)
- **Copyright:** _______________
- **License:** _______________ (typically BSD)
- **License Compatible with Apache-2.0:** ☐ YES / ☐ VERIFY
- **Source:** https://python-markdown.github.io/
- **License URL:** _______________
- **Description:** Python implementation of Markdown
- **Notes:**
Not shipped with the application but installed by users, isnÄt it? Please verify compatibility.

---

## JavaScript/CSS Libraries (served locally)

### Bootstrap
- **Version:** 5.3.8 (CONFIRMED from static files)
- **Copyright:** 2011-2024 The Bootstrap Authors
- **License:** MIT
- **License Compatible with Apache-2.0:** ✓ YES
- **Source:** https://getbootstrap.com/
- **License URL:** https://github.com/twbs/bootstrap/blob/main/LICENSE
- **Description:** Frontend UI framework
- **File Location:** apps/deepl/deeplFrontend/static/deeplFrontend/bootstrap/
- **Notes:** Full MIT license text should be included in NOTICE or referenced. Yes, please do that!

---

### jQuery
- **Version:** 3.7.1 (CONFIRMED from filename)
- **Copyright:** OpenJS Foundation and other contributors
- **License:** MIT
- **License Compatible with Apache-2.0:** ✓ YES
- **Source:** https://jquery.com/
- **License URL:** https://github.com/jquery/jquery/blob/main/LICENSE.txt
- **Description:** JavaScript library
- **File Location:** apps/deepl/deeplFrontend/static/deeplFrontend/jquery/jquery-3.7.1.slim.min.js
- **Notes:** Using slim build (without AJAX/effects modules)

---

## Docker Base Images

### python:3.11-alpine
- **Base Image:** python:3.11-alpine
- **Copyright:** Python Software Foundation and Docker Inc.
- **License:** Python Software Foundation License
- **License Compatible with Apache-2.0:** ✓ YES
- **Source:** https://hub.docker.com/_/python
- **Description:** Official Python Docker image
- **Notes:**
Not shipped with the application but installed by users, isnÄt it? Please verify compatibility.

---

### nginx:1.25-alpine
- **Base Image:** nginx:1.25-alpine
- **Copyright:** NGINX, Inc. and Igor Sysoev
- **License:** 2-clause BSD
- **License Compatible with Apache-2.0:** ✓ YES
- **Source:** https://hub.docker.com/_/nginx
- **License URL:** http://nginx.org/LICENSE
- **Description:** HTTP and reverse proxy server
- **Notes:**

Not shipped with the application but installed by users, isnÄt it? Please verify compatibility.
---

## How to Collect Missing Information

Run these commands in the Docker container to get package information:

```bash
# Get into the container
sudo docker exec -it translation_app bash

# For each Python package:
pip show gunicorn
pip show django-crispy-forms
pip show crispy-bootstrap5
pip show pytz
pip show python-dateutil
pip show requests
pip show deepl
pip show markdown

# Look for these fields:
# - Version
# - License (or License-File)
# - Home-page or Project-URL
```

For each package, also check PyPI directly:
- Go to https://pypi.org/project/<package-name>/
- Look for "License" in the left sidebar
- Check the project's GitHub repository for LICENSE file

---

## Verification Checklist

- [ ] All version numbers filled in
- [ ] All copyright holders identified
- [ ] All licenses identified and verified
- [ ] All licenses confirmed compatible with Apache-2.0
- [ ] All license URLs collected
- [ ] Any special attribution requirements noted
- [ ] Transitive dependencies reviewed (if any require attribution)
- [ ] No GPL/LGPL/AGPL licenses found (incompatible with Apache-2.0)

---

## Known License Compatibility

**Compatible with Apache-2.0:**
- ✓ MIT License
- ✓ BSD License (2-clause, 3-clause)
- ✓ Apache License 2.0
- ✓ Python Software Foundation License
- ✓ ISC License

**NOT Compatible with Apache-2.0:**
- ✗ GPL (any version)
- ✗ LGPL (any version)
- ✗ AGPL (any version)
- ✗ Creative Commons ShareAlike variants

**Requires Review:**
- ? Proprietary licenses
- ? Custom licenses
- ? Unlicensed code

---

## Additional Notes

Add any additional licensing concerns or questions here:

- My name: David Kleinhans <david.kleinhans@jade-hs.de>
- Affiliation: Jade University of Applied Sciences Wilhelmshaven Oldenburg Elsfleth
- Some of this work is based on work at my previous affiliation (Alfred-Wegener-Institute, Bremerhaven) and should be kindly acknowledged.

