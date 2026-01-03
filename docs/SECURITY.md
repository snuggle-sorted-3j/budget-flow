# Security Guidelines

## API Key Management

⚠️ **NEVER commit API keys or secrets to the repository!**

### Protected Files
- `.env` - Contains API keys (already in `.gitignore`)
- `*.json` files with API keys
- Configuration files with credentials

### Best Practices

1. **Use `.env` file** for local development
   ```bash
   # .env file (NOT in git)
   FIRECRAWL_API_KEY=fc-your-key-here
   OPENAI_API_KEY=sk-your-key-here
   AZURE_SQL_PASSWORD=YourPassword123!
   ```

2. **Use environment variables** in production
   ```bash
   export OPENAI_API_KEY=sk-your-key
   export FIRECRAWL_API_KEY=fc-your-key
   ```

3. **Rotate keys** if accidentally exposed
   - Generate new keys immediately
   - Revoke old keys in provider dashboard

## Dependency Security

### Automated Scanning

We use **Bandit** for security scanning:

```bash
# Run security scan
bandit -r . -ll --skip B101,B601

# In CI/CD (automated)
pre-commit run bandit --all-files
```

### Common Issues to Watch

1. **SQL Injection**
   - ✅ Use parameterized queries (SQLAlchemy ORM)
   - ❌ Never use string formatting for SQL

2. **Hardcoded Secrets**
   - ✅ Use environment variables
   - ❌ Never hardcode API keys in code

3. **Insecure HTTP**
   - ✅ Use HTTPS for all API calls
   - ❌ Never use HTTP for production

4. **Dependency Vulnerabilities**
   ```bash
   # Check for known vulnerabilities
   pip install safety
   safety check
   ```

## Security Checklist

Before each commit:
- [ ] No API keys in code or committed files
- [ ] All external API calls use HTTPS
- [ ] SQL queries use parameterization
- [ ] No hardcoded passwords or secrets
- [ ] `.env` file is in `.gitignore`
- [ ] Bandit security scan passes

## Reporting Security Issues

If you discover a security vulnerability:
1. **DO NOT** create a public issue
2. Email security team or maintainer privately
3. Provide detailed description and reproduction steps
4. Wait for approval before disclosing publicly
