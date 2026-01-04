# Security Audit + Threat Model

## Role
Act as a **Senior Security Engineer** specializing in web application security, API security, and document processing systems. You have deep expertise in OWASP Top 10, secure file handling, authentication/authorization patterns, and identifying attack vectors in Python/FastAPI and React/TypeScript applications.

## Primary Goal
Conduct a comprehensive security audit of the Docling-Interactive codebase to identify vulnerabilities, misconfigurations, and attack vectors across authentication, authorization, input validation, file handling, secrets management, dependency security, and API/WebSocket security. Provide actionable remediation guidance with severity classifications.

## Context
This codebase was **vibecoded** (rapidly prototyped) without formal security testing or threat modeling. Assume security best practices were NOT followed during initial development. The application handles sensitive document processing with file uploads, checkpoint storage, external API integrations, and real-time WebSocket communication.

**Your task**: Perform an adversarial security review. Think like an attacker. Identify every exploitable weakness.

## Tech Stack

**Backend:**
- Python 3.12 + FastAPI + Uvicorn (ASGI server)
- Docling (document processing engine with ML models)
- Pydantic v2 (data validation)
- SQLite3 (database)
- OpenCV, Pillow, pdf2image (image/document processing)
- Label Studio SDK (annotation tool integration)
- WebSockets (real-time communication)

**Frontend:**
- React 19 + TypeScript 5.9
- Vite 7 (build tool)
- Tailwind CSS 4 (styling)
- Zustand (state management)
- React Router DOM 7 (routing)
- Playwright (E2E testing)

**Infrastructure:**
- Docker (Python 3.11-slim-bookworm base image)
- REST API + WebSocket server
- File system storage (PDFs, checkpoints, images)

**Key Attack Surfaces:**
- PDF upload endpoint (arbitrary file upload)
- Checkpoint file storage and retrieval (path traversal)
- Label Studio API integration (leaked credentials)
- WebSocket connections (authentication bypass)
- SQLite database operations (SQL injection)
- File path handling throughout pipeline stages
- CORS configuration for frontend-backend communication

---

## Detailed Audit Requirements

### 1. Authentication & Session Management

**1.1 Authentication Implementation**
- Is authentication implemented at all? Check for `/login`, `/auth`, token validation endpoints
- If using JWT/session tokens: Check signing algorithm (HS256 vs RS256), secret strength, expiration handling
- Search for hardcoded credentials in code
- Check for authentication bypass patterns (e.g., `if user or True:`)
- Verify authentication middleware is applied to ALL protected routes

**1.2 Session Security**
- Session token storage: httpOnly cookies vs localStorage (XSS risk)
- Session fixation vulnerabilities (token regeneration on login)
- Session timeout configuration
- Logout implementation (token invalidation vs client-side only)

**1.3 Password Handling**
- Password hashing algorithm (bcrypt/argon2 vs MD5/SHA1)
- Password complexity requirements
- Password reset flow security (token expiration, single-use tokens)

**Focus Areas:**
- `backend/api/endpoints/` - Authentication decorators/dependencies
- `backend/core/config/settings.py` - Secret key configuration
- `frontend/src/` - Token storage patterns
- WebSocket authentication handshake

### 2. Authorization & Access Control

**2.1 Insecure Direct Object References (IDOR)**
- Document access by ID: Can user A access user B's documents?
- Check endpoints like `/documents/{doc_id}`, `/checkpoints/{checkpoint_id}`
- Test: Do endpoints validate ownership before returning data?
- Search for queries like `SELECT * FROM documents WHERE id = ?` without user ownership check

**2.2 Privilege Escalation**
- Role-based access control (RBAC) implementation
- Admin vs regular user separation
- Can regular users access admin endpoints by guessing URLs?
- Check for role validation in endpoint decorators

**2.3 Path Traversal in File Access**
- Checkpoint retrieval: `/checkpoints/../../etc/passwd`
- PDF access: `/documents/../../../sensitive_file.pdf`
- Image access: `/images/{doc_id}/page_{page}/../../../config.json`
- Search for `os.path.join()` with user-controlled input
- Look for `open(user_input)` patterns without validation

**Focus Areas:**
- `backend/api/endpoints/documents_extended.py` - Document access control
- `backend/core/checkpoint/` - Checkpoint file path handling
- `backend/upload/validation.py` - File path validation

### 3. Injection Vulnerabilities

**3.1 SQL Injection**
- SQLite query construction patterns
- Search for string concatenation in queries: `f"SELECT * FROM {table} WHERE id={user_input}"`
- Check for parameterized queries vs raw string interpolation
- ORM usage (if any) - second-order injection risks

**3.2 Command Injection**
- Shell command execution with user input
- Search for `subprocess.run()`, `os.system()`, `subprocess.Popen()`
- Check PDF processing: Does pdf2image use shell=True?
- Image processing commands (ImageMagick, pdftoppm)

**3.3 Path Traversal (File System)**
- Checkpoint loading: User-controlled checkpoint paths
- File upload destination paths
- Export file paths
- Search for `os.path.join(base, user_input)` - does it use `os.path.abspath()` + prefix check?

**3.4 Server-Side Request Forgery (SSRF)**
- Label Studio integration: Can users control API endpoint URLs?
- Any URL fetching based on user input
- Webhook configurations

**Focus Areas:**
- Database query patterns throughout backend
- `backend/core/docling_pipeline/` - External command execution
- `backend/services/label_studio/` - API endpoint construction

### 4. Cross-Site Scripting (XSS) & CSRF

**4.1 Reflected XSS**
- API error messages: Do they reflect user input unsanitized?
- Search for error responses returning user input directly

**4.2 Stored XSS**
- Document metadata storage (filename, title, description)
- Checkpoint JSON content - is it ever rendered without sanitization?
- Label Studio annotations - malicious payloads in annotation data

**4.3 CSRF Protection**
- POST/PUT/DELETE endpoints: CSRF token validation?
- Check for SameSite cookie attribute
- State-changing GET requests (anti-pattern)

**4.4 Content Security Policy (CSP)**
- CSP headers configured?
- Inline script restrictions
- External resource loading policies

**Focus Areas:**
- FastAPI response models - raw string returns
- Frontend rendering of backend data (dangerouslySetInnerHTML usage)
- `backend/main.py` - Security header middleware

### 5. Secrets & Configuration Management

**5.1 Hardcoded Secrets**
- Search for API keys, passwords, tokens in code
- Check `.env.example` vs actual `.env` patterns
- Database credentials
- Label Studio API keys
- JWT signing secrets

**5.2 Environment Variable Security**
- Are secrets loaded from environment variables?
- `.env` file in `.gitignore`?
- Docker secrets vs environment variables in docker-compose
- Default/example secrets in production use

**5.3 Secrets in Logs**
- Logging configuration - are secrets redacted?
- Error messages exposing sensitive data
- Debug mode enabled in production

**Focus Areas:**
- `backend/core/config/settings.py` - Secret loading
- `.env`, `.env.example` files
- `backend/services/label_studio/` - API key handling

### 6. File Upload Security

**6.1 File Type Validation**
- Magic byte validation vs extension checking
- Check: Does code verify PDF signature (`%PDF-1.`) or just `.pdf` extension?
- Can users upload arbitrary files (`.exe`, `.sh`, web shells)?
- MIME type validation (Content-Type header is user-controlled)

**6.2 PDF Bomb / Billion Laughs Attack**
- File size limits enforced?
- Decompression bomb protection (nested objects, infinite loops)
- Timeout limits on PDF processing
- Memory limits during document parsing

**6.3 Malicious PDF Exploits**
- JavaScript in PDFs (if rendering in browser)
- PDF form exploits
- Embedded file extraction risks
- Polyglot files (PDF+ZIP, PDF+HTML)

**6.4 Upload Path Security**
- Upload destination path traversal: `filename="../../../shell.php"`
- Filename sanitization (special characters, null bytes)
- Overwriting existing files
- Predictable file paths enabling enumeration

**Focus Areas:**
- `backend/upload/validation.py` - Upload validation logic
- File upload endpoints in `backend/api/endpoints/`
- PDF processing in `backend/core/docling_pipeline/`

### 7. Dependency & Supply Chain Security

**7.1 Vulnerable Dependencies**
- Run `pip-audit` - check for known CVEs
- Check `npm audit` for frontend vulnerabilities
- Docling dependency tree - transitive vulnerabilities
- Pillow, OpenCV CVEs (image processing bugs)

**7.2 Dependency Pinning**
- `requirements.txt` - pinned versions vs `package>=1.0`?
- `package-lock.json` present and committed?
- Docker base image pinning

**7.3 Malicious Package Risk**
- Typosquatting in requirements
- Unmaintained packages (last update > 2 years ago)
- Supply chain attack vectors

**Focus Areas:**
- `requirements.txt` or `pyproject.toml`
- `package.json` and `package-lock.json`
- Dockerfile base images

### 8. WebSocket Security

**8.1 WebSocket Authentication**
- Are WebSocket connections authenticated?
- Token validation on connection handshake
- Can unauthenticated users connect and receive data?

**8.2 WebSocket Authorization**
- Per-message authorization checks
- Can user A subscribe to user B's document processing updates?
- Room/channel isolation (if implemented)

**8.3 Message Injection**
- User-controlled message content - is it validated?
- JSON injection in WebSocket messages
- Message flooding/DoS protection

**8.4 WebSocket Origin Validation**
- Origin header checking
- Cross-Site WebSocket Hijacking (CSWSH)

**Focus Areas:**
- `backend/websocket/handlers.py` - Connection handling
- WebSocket authentication middleware

### 9. API Security

**9.1 CORS Configuration**
- Allowed origins - wildcard (`*`) vs specific domains?
- Credentials allowed with CORS?
- Overly permissive CORS enabling CSRF

**9.2 Rate Limiting**
- Rate limiting implemented on endpoints?
- Brute force protection on authentication
- DoS protection on expensive operations (PDF processing)

**9.3 API Information Disclosure**
- Verbose error messages exposing stack traces
- `/docs`, `/redoc` endpoints in production
- Debug mode enabled

**9.4 Input Validation**
- Pydantic model validation - are all inputs validated?
- Type coercion bypasses
- Extra fields allowed in Pydantic models (`Extra.allow` risk)
- Array/object size limits (JSON bomb attacks)

**9.5 HTTP Security Headers**
- Strict-Transport-Security (HSTS)
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- Referrer-Policy
- Permissions-Policy

**Focus Areas:**
- `backend/main.py` - CORS, middleware, security headers
- Pydantic models in `backend/api/models/` and `backend/models/`

### 10. Infrastructure & Deployment Security

**10.1 Docker Security**
- Running as root user in container?
- Sensitive data in Docker layers
- Docker socket exposure
- Secrets in environment variables vs Docker secrets

**10.2 File System Permissions**
- Checkpoint directory permissions
- Upload directory permissions
- Log file permissions
- SQLite database file permissions

**10.3 Database Security**
- SQLite file permissions (world-readable?)
- Database encryption at rest
- Backup security

**Focus Areas:**
- `Dockerfile` - user configuration, permissions
- File system setup scripts
- Database initialization

---

## Output Format

Provide findings in this EXACT structure:

### Severity Classification
- **CRITICAL**: Immediate exploitation possible, severe impact (RCE, data breach, auth bypass)
- **HIGH**: Exploitable with moderate effort, significant impact (IDOR, XSS, SQL injection)
- **MEDIUM**: Requires specific conditions, moderate impact (info disclosure, weak config)
- **MONITOR**: Potential risk, needs investigation or hardening (dependency updates, best practices)

### Finding Template

```
## [SEVERITY] Finding #N: [Concise Title]

**Location:**
- File: `/path/to/file.py` (lines X-Y)
- Component: [Backend API / Frontend / WebSocket / Docker / etc.]

**Risk Category:** [Authentication / Authorization / Injection / XSS / File Upload / etc.]

**The Problem:**
[2-3 sentences describing WHAT is vulnerable and WHY it's a security issue]

**Code Evidence:**
[Exact vulnerable code snippet with context]

**Security Impact:**
- **Confidentiality:** [How attacker accesses unauthorized data]
- **Integrity:** [How attacker modifies data/system]
- **Availability:** [How attacker disrupts service]
- **Attack Scenario:** [Step-by-step realistic exploit example]

**How to Verify:**
[Exact commands/curl requests to test vulnerability]

**The Fix:**
[Concrete code fix with secure implementation]

**Trade-off Consideration:**
[Any usability, performance, or compatibility impacts of the fix]

**References:**
- [OWASP link or CVE if applicable]
```

---

## Security Score Rubric

Rate overall security posture (1-10):

**1-2 (Critical Risk)**: Multiple critical vulnerabilities, no authentication, hardcoded secrets, trivial RCE
**3-4 (High Risk)**: Auth bypass possible, IDOR everywhere, SQL injection, XSS, no input validation
**5-6 (Medium Risk)**: Auth implemented but flawed, some authorization gaps, missing file validation
**7-8 (Low Risk)**: Core security controls present, minor misconfigurations, dependency updates needed
**9-10 (Minimal Risk)**: Defense in depth, security headers, proper validation, regular audits

Include:
- **Overall Score:** X/10
- **Breakdown:** Authentication (X/10), Authorization (X/10), Input Validation (X/10), File Security (X/10), Infrastructure (X/10)
- **Biggest Risk:** [The single most critical issue to fix immediately]

---

## Final Section: Summary & Action Plan

### Fix Now (Next 24-48 hours)
- [ ] **[CRITICAL Finding #X]**: [One-line description]
  - Impact: [Why this is urgent]
  - Effort: [Low/Medium/High]

### Fix Soon (Next Sprint)
- [ ] **[HIGH Finding #X]**: [One-line description]
  - Impact: [Business/security risk]
  - Effort: [Low/Medium/High]

### Monitor (Ongoing)
- [ ] **[MEDIUM Finding #X]**: [One-line description]
  - Action: [Monitoring/hardening step]

### Security Hardening Recommendations
- [ ] Implement authentication if missing
- [ ] Add rate limiting to all endpoints
- [ ] Enable security headers middleware
- [ ] Implement comprehensive input validation
- [ ] Add file upload magic byte validation
- [ ] Secure checkpoint file path handling
- [ ] Rotate and externalize all secrets
- [ ] Update vulnerable dependencies
- [ ] Implement CSRF protection
- [ ] Add WebSocket authentication
- [ ] Enable audit logging
- [ ] Implement principle of least privilege

### Compliance & Standards
- [ ] OWASP Top 10 compliance check
- [ ] GDPR considerations (if processing EU user data)
- [ ] SOC 2 preparation (if enterprise customers)

---

## Instructions for Audit

1. **Start with reconnaissance**: Map attack surface, identify all entry points
2. **Prioritize by risk**: Focus on auth, file uploads, and data access first
3. **Test assumptions**: Don't assume validation exists - verify in code
4. **Think like an attacker**: How would you exploit this for maximum impact?
5. **Be specific**: Provide exact file paths, line numbers, and exploit code
6. **Provide fixes**: Every finding needs actionable remediation
7. **Consider context**: Balance security with project maturity and use case

**Deliverable**: Comprehensive security audit report with prioritized findings, proof-of-concept exploits where safe, and remediation roadmap.
