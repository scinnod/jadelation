<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2024-2026 David Kleinhans, Jade University of Applied Sciences
-->

# Security Policy

## ⚠️ Critical Security Requirement

**This service provides unrestricted access to the DeepL API and MUST NOT be exposed to the public internet without authentication.**

Every translation request:
- Uses your DeepL API quota
- Incurs costs on your DeepL API account
- Is logged for statistics

If exposed publicly, malicious actors could:
- Exhaust your API quota
- Generate significant costs
- Use your API key for unauthorized translations

### Deployment Options

The core requirement is that **unauthenticated access from the public internet must be prevented**. There are several valid ways to achieve this:

**Option A – Authentication proxy (recommended for internet-facing deployments)**
```
Internet → nginx (with auth) → OAuth2-proxy → Keycloak → DeepL Frontend
           ─────────────────────────────────────────────
                    Authentication Layer
```
Example: [Django Auth Stack](https://github.com/scinnod/django-auth-stack)

**Option B – Protected Network (VPN or private LAN)**
```
VPN / Private LAN → DeepL Frontend
────────────────────────────────────
  Network-level access control only
```
If the service is only reachable inside a trusted network (e.g. a corporate intranet, a site-to-site VPN, or a home lab), authentication at the application level may not be necessary. Ensure that:
- The host/container is not reachable from the public internet
- Network access is restricted to trusted users (e.g. via firewall rules or VPN gateway)
- You understand the trust model of your network

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

**Contact:** david.kleinhans@jade-hs.de

### What to include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Acknowledgment:** Within 48 hours
- **Initial Assessment:** Within 1 week
- **Resolution:** Depends on severity

## Supported Versions

Only the latest version receives security updates.

## Required Security Measures

### Authentication

1. **Never expose this service directly to the public internet without access control**
2. Choose the approach that fits your environment:
   - **Authentication proxy** (e.g. [Django Auth Stack](https://github.com/scinnod/django-auth-stack)): suitable for internet-facing deployments
   - **Protected network** (VPN, private LAN, firewall rules): suitable when network-level isolation already restricts access to trusted users
3. Only users from your organization should be able to reach the service

### Django Security Settings

1. **Set `DEBUG=False` in production** - Debug mode exposes sensitive information
2. **Configure `ALLOWED_HOSTS`** - Only allow your specific domain(s)
3. **Configure `CSRF_TRUSTED_ORIGINS`** - Match your domain exactly
4. **Use auto-generated `SECRET_KEY`** - Let entrypoint.sh generate it
5. **Use HTTPS** - Always deploy behind an HTTPS-terminating proxy

### API Key Security

1. **Keep `DEEPL_AUTHKEY` secret** - Never commit to version control
2. **Use environment variables** - Load from env file, not code
3. **Restrict API key permissions** - Use DeepL's key management if available
4. **Monitor usage** - Check the built-in statistics regularly

### Network Security

1. **Internal network only** - Application container should not be directly accessible
2. **nginx in front** - Use the included nginx configuration
3. **External proxy** - Connect via the shared Docker network

## Security Checklist

Before deploying to production:

- [ ] Access control in place (authentication proxy or protected network)
- [ ] `DEBUG=False` in environment
- [ ] `ALLOWED_HOSTS` set to your domain only
- [ ] `CSRF_TRUSTED_ORIGINS` configured
- [ ] HTTPS enabled on upstream proxy
- [ ] `DEEPL_AUTHKEY` not in any committed files
- [ ] Container not directly accessible from internet
- [ ] Regular backups configured
- [ ] Log monitoring in place
