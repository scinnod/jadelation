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

### Required Deployment Architecture

```
Internet → nginx (with auth) → OAuth2-proxy → Keycloak → DeepL Frontend
           ─────────────────────────────────────────────
                    Authentication Layer (REQUIRED)
```

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

### Authentication (MANDATORY)

1. **Deploy behind Edge-Auth Stack** or equivalent authentication gateway
2. Never expose this service directly to the internet
3. Only authenticated users from your organization should have access

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

- [ ] Authentication proxy configured and tested
- [ ] `DEBUG=False` in environment
- [ ] `ALLOWED_HOSTS` set to your domain only
- [ ] `CSRF_TRUSTED_ORIGINS` configured
- [ ] HTTPS enabled on upstream proxy
- [ ] `DEEPL_AUTHKEY` not in any committed files
- [ ] Container not directly accessible from internet
- [ ] Regular backups configured
- [ ] Log monitoring in place
