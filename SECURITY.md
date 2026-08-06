# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within Local RAG, please follow our responsible disclosure process:

### How to Report

1. **DO NOT** create a public GitHub issue for security vulnerabilities
2. Send a detailed report to the maintainers via:
   - Private security advisory on GitHub (recommended)
   - Or contact the repository owner directly

3. Include the following information in your report:
   - Type of vulnerability
   - Full paths of source file(s) related to the vulnerability
   - Location of the affected source code (tag/commit/direct link)
   - Any special configuration required to reproduce the issue
   - Step-by-step instructions to reproduce the issue
   - Proof-of-concept or exploit code (if possible)
   - Impact of the issue, including how an attacker might exploit it

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your report within 48 hours
- **Initial Assessment**: We will assess the severity and impact of the vulnerability
- **Updates**: We will provide updates on the progress of fixing the vulnerability
- **Disclosure**: Once the fix is available, we will coordinate public disclosure with credit to the reporter

### Security Best Practices for Deployment

When deploying Local RAG, follow these security best practices:

#### Authentication

- [ ] Change default JWT secret key in production (`JWT_SECRET_KEY`)
- [ ] Change default admin/user passwords (`ADMIN_PASSWORD`, `USER_PASSWORD`)
- [ ] Use strong, unique passwords for all accounts
- [ ] Implement HTTPS/TLS for all connections
- [ ] Configure appropriate token expiration times

#### API Security

- [ ] Enable authentication for production deployments (`enable_auth=True`)
- [ ] Configure CORS appropriately for your domain (do not use `*` in production)
- [ ] Implement rate limiting (Redis-backed sliding window is included)
- [ ] Monitor API logs for suspicious activity
- [ ] Set up alerts for failed authentication attempts

#### Container Security

- [ ] Use read-only root filesystem where possible
- [ ] Run containers as non-root user (default in our Dockerfile)
- [ ] Regularly update base images and dependencies
- [ ] Scan container images for vulnerabilities (Trivy, Docker Scout)
- [ ] Use Docker secrets or external vault for sensitive configuration
- [ ] Configure resource limits to prevent DoS attacks

#### Data Security

- [ ] Secure ChromaDB storage location
- [ ] Implement backups with encryption
- [ ] Protect model files from unauthorized access
- [ ] Never commit `.env` files or credentials to version control

### Known Security Considerations

#### Local LLM Execution (llama.cpp)

When using local LLM execution:
- Models are executed in your local environment
- No data leaves your infrastructure
- You are responsible for securing model files

#### Cloud LLM Providers

When using cloud LLM providers:
- Query data may be sent to third-party APIs
- Review each provider's privacy policy and terms
- Use API keys securely (store in `.env`, never commit)

#### Rate Limiting

Rate limiting is implemented but:
- In-memory rate limiter does not persist across restarts
- Redis rate limiter is recommended for production
- Redis should be password-protected in production environments

### Security Updates

Security updates will be released as patch versions (e.g., 1.0.1) for critical issues.
Minor versions (e.g., 1.1.0) may include security improvements.

Subscribe to GitHub notifications to stay informed about security updates.
