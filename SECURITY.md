# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT** open a public GitHub issue
2. Email the maintainer directly or use GitHub's private vulnerability reporting
3. Include a detailed description and steps to reproduce
4. Allow reasonable time for a fix before public disclosure

## Security Measures

This project implements the following security practices:

- **OIDC Federation**: No stored cloud credentials — GitHub Actions uses short-lived tokens
- **Managed Identity**: Azure services authenticate via identity, not secrets
- **Non-root containers**: Docker images run as unprivileged `appuser`
- **Secret management**: API keys use `SecretStr` (never logged in plaintext)
- **Dependency scanning**: Bandit security scans run on every CI build
- **Input validation**: All API inputs validated via Pydantic schemas
- **CORS**: Configurable allowed origins (not wildcard in production)
