# Security Review Checklist

## 🔒 Authentication & Authorization

- [ ] Authentication required for protected endpoints
- [ ] Authorization checks present (user has permission)
- [ ] No authentication bypass vulnerabilities
- [ ] Session management secure (timeout, regeneration)
- [ ] Password requirements enforced (if applicable)
- [ ] Multi-factor authentication considered
- [ ] API keys/tokens validated properly

## 🚨 Secrets & Credentials

- [ ] No API keys in code
- [ ] No passwords in code
- [ ] No tokens in code
- [ ] No database credentials in code
- [ ] All secrets in environment variables
- [ ] .env files in .gitignore
- [ ] No secrets in logs or error messages
- [ ] Secrets rotation plan documented

## 💉 Injection Vulnerabilities

### SQL Injection
- [ ] All database queries use parameterized queries
- [ ] No string concatenation for SQL
- [ ] ORM used correctly (not raw queries with user input)
- [ ] Input sanitized before database operations

### Command Injection
- [ ] No `os.system()` or `subprocess` with user input
- [ ] Shell=False used if subprocess needed
- [ ] User input validated/sanitized for commands
- [ ] Consider safer alternatives to shell commands

### Code Injection
- [ ] No `eval()` on user input
- [ ] No `exec()` on user input
- [ ] No dynamic imports from user input
- [ ] Template engines used safely

### XSS (Cross-Site Scripting)
- [ ] All user output properly escaped
- [ ] HTML sanitization for rich text
- [ ] Content-Security-Policy headers set
- [ ] No innerHTML with user data

## 🔐 Data Protection

### Encryption
- [ ] Sensitive data encrypted at rest
- [ ] TLS/HTTPS used for data in transit
- [ ] Strong encryption algorithms (AES-256, RSA-2048+)
- [ ] No weak or deprecated crypto

### Data Exposure
- [ ] No sensitive data in logs
- [ ] No sensitive data in error messages
- [ ] API responses don't leak internal details
- [ ] No PII in URLs or query parameters
- [ ] Database backups encrypted

## 🛡️ Input Validation

- [ ] All user inputs validated (type, format, range)
- [ ] File uploads validated (type, size, content)
- [ ] Whitelist validation used (not blacklist)
- [ ] Rate limiting on API endpoints
- [ ] CSRF tokens used for state-changing operations
- [ ] Size limits on request bodies

## 📝 Logging & Monitoring

- [ ] Security events logged (login, auth failures, etc.)
- [ ] No sensitive data in logs (passwords, keys, PII)
- [ ] Sufficient context for security auditing
- [ ] Anomaly detection considered
- [ ] Log tampering protection

## 🔧 Dependencies & Libraries

- [ ] All dependencies up to date
- [ ] No known vulnerabilities in dependencies
- [ ] Dependencies from trusted sources
- [ ] Minimal dependencies (reduce attack surface)
- [ ] Regular security audits scheduled

## 🌐 API Security

- [ ] Authentication required for APIs
- [ ] Rate limiting implemented
- [ ] Input validation on all parameters
- [ ] CORS properly configured
- [ ] No mass assignment vulnerabilities
- [ ] API versioning implemented

## 🗄️ Database Security

- [ ] Principle of least privilege for DB access
- [ ] No default credentials
- [ ] Database connection strings secured
- [ ] Backups encrypted and tested
- [ ] Audit logging enabled

## ⚡ Denial of Service (DoS)

- [ ] Rate limiting on expensive operations
- [ ] Timeout limits on operations
- [ ] Resource quotas enforced
- [ ] No algorithmic complexity attacks
- [ ] No ReDoS (Regular Expression DoS)

## 🔍 Security Testing

- [ ] Security tests included
- [ ] Penetration testing considered
- [ ] Fuzz testing for critical inputs
- [ ] Security regression tests

## 📋 Compliance & Privacy

- [ ] GDPR compliance if handling EU data
- [ ] Data retention policies followed
- [ ] Right to deletion implemented if required
- [ ] Privacy policy updated if needed
- [ ] Consent mechanisms for data collection

## Common Vulnerability Patterns to Check

### Python
```python
# ❌ BAD: SQL Injection
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# ✅ GOOD: Parameterized Query
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))

# ❌ BAD: Command Injection
os.system(f"ls {user_directory}")

# ✅ GOOD: Safe Alternative
os.listdir(user_directory)

# ❌ BAD: Hardcoded Secret
API_KEY = "sk-1234567890abcdef"

# ✅ GOOD: Environment Variable
API_KEY = os.environ.get("API_KEY")
```

### Web
```javascript
// ❌ BAD: XSS Vulnerability
element.innerHTML = userInput;

// ✅ GOOD: Safe Text Content
element.textContent = userInput;

// ❌ BAD: Open Redirect
window.location = req.query.redirect;

// ✅ GOOD: Validated Redirect
if (ALLOWED_DOMAINS.includes(new URL(req.query.redirect).hostname)) {
  window.location = req.query.redirect;
}
```

## Severity Ratings

**🚨 CRITICAL (Immediate Fix Required)**
- Remote code execution
- Authentication bypass
- Exposed secrets/credentials
- SQL injection
- Data breach risk

**⚠️ HIGH (Fix Before Merge)**
- Improper authorization
- Sensitive data exposure
- XSS vulnerabilities
- Weak encryption

**💡 MEDIUM (Should Fix)**
- Missing security headers
- Insufficient logging
- Outdated dependencies
- Rate limiting missing

**📝 LOW (Document/Track)**
- Security improvements
- Defense in depth opportunities
- Hardening recommendations
