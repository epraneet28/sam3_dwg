---
## Metadata
**Priority Level:** P3 (Lower)
**Original Audit:** #15 Logging & Data Exposure
**Last Updated:** 2025-12-26
**AI/Vibe-Coding Risk Level:** MEDIUM

---

# Logging & Data Exposure Audit Prompt (Production-Ready, Security-Focused)

## Role
Act as a Senior Security Engineer and Privacy Specialist. Perform a comprehensive Logging & Data Exposure Audit on the provided codebase to identify information leakage risks before production deployment.

## Primary Goal
Identify where logs, error messages, API responses, and debug output expose sensitive data, internal system details, or user content that could aid attackers or violate privacy requirements.

## Context
- This code was developed with a focus on speed ("vibecoded") and may have verbose logging, detailed error messages, and debug output left in place.
- I need you to find all data exposure vectors before production deployment.

## Tech Stack
- Backend: Python 3.12 + FastAPI + Uvicorn
- Frontend: React 19 + TypeScript 5.9 + Vite 7
- Database: SQLite3
- Document Processing: Docling, OpenCV, Pillow, pdf2image
- Real-time: WebSockets
- External Integration: Label Studio SDK
- State: Zustand (frontend), JSON checkpoints (backend)

## Security & Privacy Targets
- No PII in logs (names, emails, document content)
- No internal paths, stack traces, or system info in API responses
- No secrets, API keys, or credentials in any output
- No document text content in logs or error messages
- Structured logging with appropriate log levels
- Error messages that are helpful to users but not to attackers

## How to Provide Code
I will paste/upload the codebase files below. Analyze all provided files systematically.
If any critical context is missing (logging configuration, error handlers, environment settings), infer what you can from the code and explicitly list assumptions.

## Environment & Assumptions (you must do this first)
1) Infer and list:
   - Logging framework (Python logging, loguru, structlog, etc.)
   - Log level configuration and where it's set
   - Error handling middleware (FastAPI exception handlers)
   - Frontend error boundaries and error display
   - API response serialization patterns
   - Debug mode indicators
2) If you cannot infer any of the above, provide best-practice defaults and mark as "Needs Confirmation".

## Audit Requirements
Scan the files and generate a report identifying high-confidence instances of the risks below.
Also include "Suspicious Patterns" when something looks risky but requires confirmation.

---

## 1) Sensitive Data in Logs

### A) Document Content Logging
- Look for logging of OCR text, extracted content, or document data.
- Common hotspots: Pipeline stage processors, checkpoint handlers, debug statements.
- Flag patterns: `logger.debug(f"Extracted text: {text}")`, `print(document.content)`.
- Suggested Fix: Log document IDs and metadata only, never content. Use structured logging with explicit field selection.

### B) User Data in Logs
- Find logging of user identifiers, session data, or request bodies.
- Flag patterns: `logger.info(f"Request: {request.json()}")`, logging full headers.
- Suggested Fix: Log request IDs and operation types only. Implement request body redaction.

### C) File Paths and System Information
- Look for logging of absolute file paths, system directories, or internal structure.
- Common hotspots: File upload handlers, checkpoint operations, error messages.
- Flag patterns: `logger.error(f"File not found: {full_path}")`, `print(os.getcwd())`.
- Suggested Fix: Log relative paths or file IDs. Never expose server filesystem structure.

### D) Credentials and API Keys
- Find logging of API keys, tokens, passwords, or connection strings.
- Flag patterns: `logger.debug(f"Using API key: {key}")`, logging Label Studio credentials.
- Suggested Fix: Never log credentials. Use environment variable names in logs, not values.

### E) Database Queries with Data
- Look for SQL query logging that includes data values.
- Flag patterns: `logger.debug(f"Query: {query}")` with interpolated values.
- Suggested Fix: Log query structure without data. Use parameterized query logging.

---

## 2) Error Messages Leaking Internals

### A) Stack Traces in API Responses
- Find unhandled exceptions that return full tracebacks to clients.
- Common hotspots: Missing exception handlers, debug mode enabled.
- Flag patterns: FastAPI without custom exception handlers, `traceback.format_exc()` in responses.
- Suggested Fix: Implement centralized exception handler returning generic errors. Log full traces server-side only.

### B) Database Error Details
- Look for database errors passed directly to API responses.
- Flag patterns: `raise HTTPException(detail=str(db_error))`, SQLite error messages exposed.
- Suggested Fix: Map database errors to user-friendly messages. Log originals server-side.

### C) File System Errors
- Find file operation errors exposing paths or permissions.
- Flag patterns: `FileNotFoundError` message passed to client, permission errors with paths.
- Suggested Fix: Return "Document not found" without path details. Log full errors server-side.

### D) External Service Errors
- Look for Label Studio, Docling, or other service errors passed to clients.
- Flag patterns: Raw API errors from external services in responses.
- Suggested Fix: Wrap external errors with generic messages. Log full error for debugging.

### E) Validation Error Over-Exposure
- Find validation errors that reveal internal schema or field names.
- Flag patterns: Pydantic errors with internal field names, type hints exposed.
- Suggested Fix: Sanitize validation messages. Map internal names to user-facing terms.

---

## 3) Debug & Development Artifacts

### A) Debug Mode in Production
- Look for `DEBUG=True`, verbose logging enabled, or development settings.
- Common hotspots: Environment config, FastAPI settings, Vite config.
- Flag patterns: Hardcoded `debug=True`, missing production checks.
- Suggested Fix: Environment-based configuration with production defaults.

### B) Console.log / Print Statements
- Find `print()`, `console.log()` with sensitive data.
- Common hotspots: Frontend components, backend handlers, utility functions.
- Flag patterns: `print(f"Processing: {data}")`, `console.log(response)`.
- Suggested Fix: Remove or replace with proper logging. Use log levels appropriately.

### C) Development Comments with Secrets
- Look for TODO comments, hardcoded test credentials, or debug URLs.
- Flag patterns: `# TODO: remove before prod`, `apiKey = "test123"`, localhost URLs.
- Suggested Fix: Remove all development artifacts. Use environment variables.

### D) Source Maps in Production
- Check for source maps enabled in production builds.
- Flag patterns: Vite config with sourcemaps enabled, `.map` files in build output.
- Suggested Fix: Disable source maps in production or use hidden source maps.

### E) Verbose Error Pages
- Find detailed error pages with stack traces or debug info.
- Flag patterns: React error boundaries showing component trees, FastAPI debug pages.
- Suggested Fix: Custom error pages with generic messages. Log details server-side.

---

## 4) API Response Data Exposure

### A) Over-Fetching in Responses
- Look for API responses returning more data than needed.
- Common hotspots: Document endpoints returning full content, list endpoints with excessive fields.
- Flag patterns: Returning full Pydantic models without field selection.
- Suggested Fix: Use response models with explicit field inclusion. Implement DTOs.

### B) Internal IDs and References
- Find internal database IDs, file paths, or system references in responses.
- Flag patterns: Auto-increment IDs, internal checkpoint paths, server-side UUIDs.
- Suggested Fix: Use opaque public IDs. Remove internal references from responses.

### C) Timing Information Leakage
- Look for response timing that could enable timing attacks.
- Flag patterns: Different error paths with measurable timing differences.
- Suggested Fix: Constant-time comparisons for sensitive operations. Normalize response times.

### D) Error Response Enumeration
- Find error responses that enable resource enumeration.
- Flag patterns: "Document not found" vs "Access denied" revealing existence.
- Suggested Fix: Use consistent "Not found or access denied" messages.

### E) Metadata Exposure
- Look for server version, framework details, or infrastructure info in responses.
- Flag patterns: Server header with version, X-Powered-By headers, version endpoints.
- Suggested Fix: Remove or obscure server identification headers.

---

## 5) WebSocket & Real-time Exposure

### A) WebSocket Message Content
- Look for sensitive data in WebSocket messages.
- Common hotspots: Progress updates with document content, error broadcasts.
- Flag patterns: Broadcasting document text, logging WebSocket payloads.
- Suggested Fix: Send IDs and status only. Never broadcast document content.

### B) WebSocket Error Details
- Find detailed error messages in WebSocket communications.
- Flag patterns: Full exception messages in WebSocket error events.
- Suggested Fix: Generic error codes over WebSocket. Log details server-side.

### C) Connection State Logging
- Look for excessive logging of connection events with client info.
- Flag patterns: Logging client IPs, connection parameters, session data.
- Suggested Fix: Log connection counts and errors only. Anonymize client identifiers.

---

## 6) Frontend Data Exposure

### A) Sensitive Data in Browser Storage
- Look for PII, tokens, or document content in localStorage/sessionStorage.
- Common hotspots: Zustand persist, cached API responses, debug data.
- Flag patterns: Storing document text, API keys, or user data in browser storage.
- Suggested Fix: Store IDs only. Use secure, httpOnly cookies for auth.

### B) React Component State Exposure
- Find sensitive data in React DevTools-accessible state.
- Flag patterns: Full document content in Zustand stores, API responses in state.
- Suggested Fix: Minimize state. Remove sensitive data after use.

### C) Network Tab Visibility
- Look for sensitive data visible in browser network inspector.
- Common hotspots: API responses, WebSocket messages, request bodies.
- Flag patterns: Document content in responses, credentials in requests.
- Suggested Fix: Minimize response data. Use request body encryption for sensitive ops.

### D) Client-Side Error Reporting
- Find client-side error reporting that captures sensitive context.
- Flag patterns: Error boundaries capturing component state, Sentry with full context.
- Suggested Fix: Filter sensitive data from error reports. Use allowlists.

---

## 7) Log Infrastructure Security

### A) Log File Permissions
- Check for insecure log file locations or permissions.
- Flag patterns: Logs in web-accessible directories, world-readable log files.
- Suggested Fix: Logs outside webroot. Restrict permissions to application user.

### B) Log Retention and Rotation
- Look for unbounded log growth or missing rotation.
- Flag patterns: No logrotate config, logs growing indefinitely.
- Suggested Fix: Implement log rotation. Define retention policy.

### C) Log Aggregation Security
- Find insecure log shipping or aggregation.
- Flag patterns: Unencrypted log transmission, logs to public endpoints.
- Suggested Fix: TLS for log shipping. Authenticate log endpoints.

### D) Structured Logging Consistency
- Look for inconsistent log formats that complicate security analysis.
- Flag patterns: Mixed `print()`, `logging`, custom formats.
- Suggested Fix: Standardize on structured logging (JSON). Include correlation IDs.

---

## Output Format (Mandatory)

For each issue found, provide:

```
[SEVERITY: CRITICAL | HIGH | MEDIUM | MONITOR]

Location: FileName : Line Number(s)
Risk Category: Logging | Error Handling | API Response | WebSocket | Frontend | Debug Artifacts

The Problem:
- 2-4 sentences explaining the exposure risk.
- Be specific about what data is exposed and to whom (logs, clients, attackers).

Privacy/Security Impact:
- Describe the real-world consequence: data breach, compliance violation, attack enablement.
- Include Confidence: High | Medium | Low

How to Verify:
- Concrete verification step (grep for patterns, review log files, test API responses, check browser DevTools).

The Fix:
- Provide the secure code snippet.
- Show before/after if useful.
- If fix requires configuration, show the config change and where it belongs.

Compliance Note:
- Note any GDPR/CCPA/SOC2 implications.
- Identify if this blocks specific compliance requirements.
```

## Severity Classification
- **CRITICAL**: Exposes credentials, PII, or enables direct attacks (API keys in logs, document content in responses).
- **HIGH**: Exposes internal structure or significant debugging info (stack traces, file paths, system info).
- **MEDIUM**: Leaks minor internal details or has compliance implications (verbose errors, development artifacts).
- **MONITOR**: Acceptable for now but should be addressed for mature security posture.

---

## Vibe Score Rubric (Data Exposure Posture 1-10)

Rate overall data exposure risk based on severity/quantity and systemic issues:
- **9-10**: Production-ready; minimal exposure, structured logging, proper error handling.
- **7-8**: Minor issues; 1-2 areas need attention before production.
- **5-6**: Significant exposure risks; several areas need remediation.
- **3-4**: Multiple high-severity issues; not production-ready.
- **<3**: Critical exposure; credentials or PII actively leaking.

---

## Include:
- The score
- Brief justification (2-5 bullets)
- A prioritized Top 3 fixes list (highest impact first)

## Final Section: Summary & Action Plan (Mandatory)
1) Fix Now (before production)
2) Fix Soon (next iteration)
3) Monitor (log review + thresholds)

## Also include:
- Estimated time to implement all Fix Now items (range is fine)
- Logging infrastructure recommendations:
  - Structured logging library (structlog, python-json-logger)
  - Log level configuration per environment
  - Sensitive data detection patterns
  - Log review process for security
- Recommended verification commands:
  - `grep -r "print(" --include="*.py"` -> find print statements
  - `grep -r "console.log" --include="*.ts" --include="*.tsx"` -> find console.log
  - `grep -rE "(password|secret|key|token)" --include="*.py"` -> find potential credential logging
  - Review sample API error responses for stack trace leakage

---

## Stack-Specific Checks for Python/FastAPI + React

### FastAPI Error Handling
```python
# BAD: Leaks internal details
@app.exception_handler(Exception)
async def handler(request, exc):
    return JSONResponse({"detail": str(exc)})  # Exposes internals

# GOOD: Generic error with logging
@app.exception_handler(Exception)
async def handler(request, exc):
    logger.exception("Unhandled error", request_id=request.state.request_id)
    return JSONResponse({"detail": "Internal server error"}, status_code=500)
```

### Pydantic Response Model Filtering
```python
# BAD: Returns everything
@router.get("/documents/{id}")
async def get_document(id: str) -> Document:
    return document  # May include internal fields

# GOOD: Explicit response model
class DocumentResponse(BaseModel):
    id: str
    name: str
    status: str
    # Excludes: file_path, internal_id, processing_details

@router.get("/documents/{id}", response_model=DocumentResponse)
async def get_document(id: str):
    return document
```

### React Error Boundaries
```tsx
// BAD: Shows error details
<ErrorBoundary fallback={<div>{error.stack}</div>}>

// GOOD: Generic error with logging
<ErrorBoundary
  fallback={<div>Something went wrong</div>}
  onError={(error) => logToService(error)}
>
```

### Document Processing Logging
```python
# BAD: Logs document content
logger.debug(f"Processing page text: {page.text[:500]}")

# GOOD: Logs metadata only
logger.debug(f"Processing page", extra={
    "page_num": page.number,
    "element_count": len(page.elements),
    "document_id": doc.id
})
```

### WebSocket Message Security
```python
# BAD: Broadcasts content
await websocket.send_json({
    "type": "progress",
    "text_extracted": text_content  # Exposes document content
})

# GOOD: Status only
await websocket.send_json({
    "type": "progress",
    "stage": "ocr",
    "page": 5,
    "total": 20
})
```
