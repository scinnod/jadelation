# Contributing Guide

Thank you for your interest in contributing to this project!

## Project Context

This is a university infrastructure project developed at Jade University of Applied Sciences. While we welcome contributions, please understand that support capacity is limited.

## How to Contribute

### Reporting Issues

1. Check existing issues first
2. Provide clear reproduction steps
3. Include environment details (OS, Docker version, etc.)

### Pull Requests

1. Fork the repository
2. Create a feature branch
3. Follow existing code style
4. Add tests if applicable
5. Update documentation
6. Submit PR with clear description

## Code Standards

### Python

- Follow PEP 8 guidelines
- Use type hints where practical
- Add docstrings to functions/classes
- Keep functions focused and small

### Django

- Use Django best practices
- Translate user-facing strings
- No hardcoded secrets

### Templates

- Use Django template language
- Keep logic minimal in templates
- Ensure responsive design

## Internationalization

All user-facing text must be translatable:
- Use `gettext_lazy()` or `_()` for strings
- Mark template strings with `{% translate %}`

## License

By contributing, you agree that your contributions will be licensed under AGPL-3.0-or-later.

## Contact

**Maintainer:** David Kleinhans  
**Email:** david.kleinhans@jade-hs.de  
**Affiliation:** Jade University of Applied Sciences
