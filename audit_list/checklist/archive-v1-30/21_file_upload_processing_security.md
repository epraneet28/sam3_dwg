# File Upload & Processing Security Audit Prompt (Production-Ready, Attack-Resistant)

## Role
Act as a Senior Application Security Engineer specializing in file upload vulnerabilities and document processing attacks. Perform a comprehensive File Upload & Processing Security Audit on the provided codebase to identify and remediate attack vectors before production deployment.

## Primary Goal
Identify where AI-generated file handling logic creates security vulnerabilities, and provide concrete fixes that make the system resistant to malicious file uploads and processing attacks.

## Context
- This code was developed with a focus on speed ("vibecoded") and file upload security is often overlooked in AI-generated code.
- Document processing pipelines are high-value attack targets due to complex parsing logic and system-level operations.
- I need you to find exploitable vulnerabilities before attackers do.

## Tech Stack
- Backend: Python 3.12 + FastAPI + Uvicorn
- Document Processing: Docling engine
- Image Processing: OpenCV, Pillow, pdf2image
- Validation: Pydantic v2
- Database: SQLite3
- File Storage: Local filesystem with checkpoint system
- Integration: Label Studio SDK

## Attack Surface Overview
- PDF upload endpoints
- Image extraction and rendering
- Checkpoint file read/write operations
- Temporary file handling
- Multi-page document processing
- Label Studio import/export

## How to Provide Code
I will paste/upload the codebase files below. Analyze all provided files systematically.
If any critical context is missing (upload endpoints, file storage paths, validation logic), infer what you can from the code and explicitly list assumptions. If you cannot infer, state "Needs Confirmation" and tell me exactly which file/setting is needed.

## Environment & Assumptions (you must do this first)
1) Infer and list:
   - Upload endpoint locations and frameworks (FastAPI UploadFile, etc.)
   - File storage strategy (temp files, permanent storage, paths)
   - Validation libraries in use (python-magic, filetype, etc.)
   - Maximum file size limits (if configured)
   - Allowed file types and how they're enforced
   - Temporary file cleanup mechanisms
2) If you cannot infer any of the above, provide best-practice defaults and mark as "Needs Confirmation".

## Audit Requirements
Scan the files and generate a report identifying high-confidence instances of the risks below.
Also include "Suspicious Patterns" when something looks risky but requires confirmation (call out exactly what to verify).

---

## 1) File Type Validation Vulnerabilities

### A) Extension-Only Validation (CRITICAL)
- Look for validation that only checks file extension (.pdf, .png) without magic byte verification.
- Common hotspots: FastAPI upload endpoints, file save logic, import functions.
- Attack Vector: Attacker uploads malicious.pdf that's actually an executable or polyglot file.
- Suggested Fix: Use `python-magic` or `filetype` library to verify magic bytes match expected type.

```python
# VULNERABLE
if not filename.endswith('.pdf'):
    raise HTTPException(400, "Only PDF files allowed")

# SECURE
import magic

def validate_pdf(file_content: bytes) -> bool:
    mime = magic.from_buffer(file_content, mime=True)
    return mime == 'application/pdf'
```

### B) MIME Type Spoofing
- Flag reliance on `Content-Type` header from request without server-side verification.
- Attack Vector: Attacker sets `Content-Type: application/pdf` but sends malicious file.
- Suggested Fix: Always verify file content server-side; never trust client-provided MIME types.

### C) Polyglot File Detection
- Check if system handles files that are valid in multiple formats (PDF/ZIP, PNG/HTML).
- Attack Vector: Polyglot file passes validation but exploits downstream parser.
- Suggested Fix: Strict magic byte validation, content sanitization, and sandboxed processing.

### D) Double Extension Attacks
- Look for handling of files like `malicious.pdf.exe` or `file.php.pdf`.
- Attack Vector: Web server or OS may execute based on secondary extension.
- Suggested Fix: Extract and validate only the final extension; sanitize filename completely.

---

## 2) PDF-Specific Attack Vectors

### A) PDF Bomb / Decompression Bomb (CRITICAL)
- Check for limits on:
  - Decompression ratio (zip bomb inside PDF)
  - Page count limits
  - Embedded object limits
  - Stream size limits
- Attack Vector: 1KB PDF expands to 10GB, causing OOM or disk exhaustion.
- Suggested Fix: Implement decompression limits and resource monitors.

```python
# SECURE: pdf2image with resource limits
from pdf2image import convert_from_bytes
from pdf2image.exceptions import PDFPageCountError

MAX_PAGES = 500
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

def safe_pdf_to_images(pdf_bytes: bytes):
    if len(pdf_bytes) > MAX_FILE_SIZE:
        raise ValueError("PDF exceeds maximum file size")

    # Use timeout and memory limits
    images = convert_from_bytes(
        pdf_bytes,
        first_page=1,
        last_page=MAX_PAGES,
        timeout=60,  # seconds
        size=(2000, None),  # limit max dimension
    )
    return images
```

### B) Malicious PDF JavaScript/Actions
- Check if PDF parsing executes or preserves JavaScript, form actions, or launch commands.
- Attack Vector: PDF with embedded JS runs when opened in viewer.
- Suggested Fix: Strip or sanitize PDF actions during processing; use safe rendering mode.

### C) External Entity Injection (XXE in PDF)
- Check if PDF parser follows external references or URIs.
- Attack Vector: PDF references external DTD/entity causing SSRF or data exfiltration.
- Suggested Fix: Disable external entity resolution in PDF parsing libraries.

### D) Embedded File Extraction
- Check handling of PDFs with embedded files (attachments, portfolios).
- Attack Vector: Malicious files hidden in PDF attachments bypass scanning.
- Suggested Fix: Extract and scan all embedded files; limit or block embedded content.

---

## 3) Path Traversal & File System Attacks

### A) Path Traversal in Upload Filename (CRITICAL)
- Look for user-controlled filenames used in file paths without sanitization.
- Common patterns: `os.path.join(upload_dir, filename)`, `f"{base_path}/{filename}"`.
- Attack Vector: Filename `../../../etc/passwd` or `....//....//etc/passwd` escapes upload directory.
- Suggested Fix: Use secure filename function; never use user input directly in paths.

```python
# VULNERABLE
save_path = os.path.join(UPLOAD_DIR, request.filename)

# SECURE
from werkzeug.utils import secure_filename
import uuid

def safe_save_path(original_filename: str, upload_dir: str) -> str:
    # Generate unique filename, preserve extension safely
    ext = os.path.splitext(original_filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Invalid extension: {ext}")

    safe_name = f"{uuid.uuid4()}{ext}"
    full_path = os.path.join(upload_dir, safe_name)

    # Verify path is within upload directory
    real_path = os.path.realpath(full_path)
    real_upload = os.path.realpath(upload_dir)
    if not real_path.startswith(real_upload):
        raise ValueError("Path traversal detected")

    return full_path
```

### B) Symlink Following
- Check if file operations follow symlinks that could point outside allowed directories.
- Attack Vector: Attacker creates symlink in upload directory pointing to sensitive files.
- Suggested Fix: Use `os.path.realpath()` and verify final path is within allowed directory.

### C) Checkpoint File Path Injection
- Check if checkpoint filenames or paths are derived from user input (document IDs, page numbers).
- Attack Vector: Malicious document ID like `../../config` writes to arbitrary location.
- Suggested Fix: Validate and sanitize all path components; use allowlist for path patterns.

### D) Temporary File Predictable Names
- Look for tempfile creation with predictable names or insecure permissions.
- Attack Vector: Race condition allows attacker to replace temp file before processing.
- Suggested Fix: Use `tempfile.mkstemp()` or `tempfile.NamedTemporaryFile()` with secure defaults.

---

## 4) File Size & Resource Exhaustion

### A) Missing Upload Size Limits (CRITICAL)
- Check for explicit file size limits in FastAPI/Starlette configuration.
- Attack Vector: 10GB upload exhausts disk space, memory, or causes timeout.
- Suggested Fix: Configure limits at multiple layers (reverse proxy, framework, application).

```python
# FastAPI with size limits
from fastapi import FastAPI, File, UploadFile, HTTPException

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Check content-length header first (fast fail)
    if file.size and file.size > MAX_UPLOAD_SIZE:
        raise HTTPException(413, "File too large")

    # Stream and count bytes (don't trust header)
    contents = bytearray()
    while chunk := await file.read(8192):
        contents.extend(chunk)
        if len(contents) > MAX_UPLOAD_SIZE:
            raise HTTPException(413, "File too large")

    return {"size": len(contents)}
```

### B) Memory Exhaustion via Large Files
- Check if entire file is read into memory vs streamed.
- Attack Vector: Large file causes OOM, crashing the application.
- Suggested Fix: Stream file processing; use chunked reading; implement memory limits.

### C) Disk Exhaustion via Temp Files
- Check for cleanup of temporary files after processing (success or failure).
- Attack Vector: Failed uploads accumulate, filling disk.
- Suggested Fix: Use context managers; implement cleanup on exception; periodic cleanup job.

### D) Processing Time Limits
- Check for timeouts on document processing operations.
- Attack Vector: Malformed PDF causes infinite loop or extremely long processing.
- Suggested Fix: Implement processing timeouts; use subprocess with timeout for heavy operations.

---

## 5) Temporary File Security

### A) Insecure Temp Directory (CRITICAL)
- Check if temp files are created in predictable or shared locations.
- Attack Vector: Other users on shared system can access/modify temp files.
- Suggested Fix: Use private temp directory with restrictive permissions.

```python
# SECURE: Private temp directory
import tempfile
import os

def get_secure_temp_dir() -> str:
    """Create a private temp directory for this application."""
    base_temp = os.environ.get('APP_TEMP_DIR', '/var/tmp/docling-secure')
    os.makedirs(base_temp, mode=0o700, exist_ok=True)
    return tempfile.mkdtemp(dir=base_temp)
```

### B) Temp File Cleanup Failures
- Check for cleanup in finally blocks or context managers.
- Look for exceptions that skip cleanup code.
- Attack Vector: Sensitive document data persists in temp files after processing.
- Suggested Fix: Use `try/finally` or context managers; implement background cleanup.

### C) Temp File Permission Issues
- Check permissions on created temp files (should not be world-readable).
- Attack Vector: Sensitive data in temp files readable by other processes.
- Suggested Fix: Set restrictive permissions (0600) on creation.

### D) Orphaned Temp Files After Crash
- Check for startup cleanup of stale temp files from previous runs.
- Attack Vector: Accumulated temp files from crashes leak data or exhaust disk.
- Suggested Fix: Implement startup cleanup based on file age; use unique session directories.

---

## 6) Image Processing Vulnerabilities

### A) Image Bomb / Pixel Flood (CRITICAL)
- Check for dimension limits before image processing with Pillow/OpenCV.
- Attack Vector: 1x1 pixel JPEG with dimensions declared as 65535x65535 causes OOM.
- Suggested Fix: Set Pillow's MAX_IMAGE_PIXELS; validate dimensions before processing.

```python
# SECURE: Pillow with limits
from PIL import Image

# Set global limit
Image.MAX_IMAGE_PIXELS = 178956970  # ~13000x13000

def safe_open_image(file_path: str, max_dimension: int = 10000) -> Image.Image:
    """Open image with dimension validation."""
    with Image.open(file_path) as img:
        width, height = img.size
        if width > max_dimension or height > max_dimension:
            raise ValueError(f"Image too large: {width}x{height}")
        # Load the image data
        img.load()
        return img.copy()
```

### B) Malicious Image Metadata
- Check if EXIF/metadata from uploaded images is processed or displayed.
- Attack Vector: XSS payload in EXIF comment displayed in UI.
- Suggested Fix: Strip or sanitize image metadata before storage/display.

### C) Image Format Confusion
- Check for format-specific vulnerabilities (SVG script injection, GIF LZW bomb).
- Attack Vector: SVG with embedded JavaScript; GIF with extreme LZW compression.
- Suggested Fix: Convert uploaded images to safe format; disable SVG processing or sanitize.

### D) OpenCV/Pillow CVE Exposure
- Check versions of image processing libraries against known CVEs.
- Attack Vector: Exploit known vulnerability in outdated library version.
- Suggested Fix: Keep libraries updated; subscribe to security advisories.

---

## 7) Filename & Content Injection

### A) Filename XSS in UI Display
- Check if original filenames are displayed in frontend without sanitization.
- Attack Vector: Filename `<script>alert('xss')</script>.pdf` executes in browser.
- Suggested Fix: HTML-escape filenames; use sanitized display names.

### B) SQL Injection via Filename
- Check if filenames are used in database queries without parameterization.
- Attack Vector: Filename containing SQL injection payload corrupts database.
- Suggested Fix: Always use parameterized queries; never interpolate filenames.

### C) Command Injection via Filename
- Check if filenames are passed to shell commands or subprocess.
- Attack Vector: Filename `; rm -rf /; .pdf` executes shell command.
- Suggested Fix: Never use shell=True; use array arguments; sanitize filenames.

```python
# VULNERABLE
import subprocess
subprocess.run(f"pdfinfo {uploaded_file}", shell=True)

# SECURE
subprocess.run(["pdfinfo", uploaded_file], shell=False, check=True)
```

### D) Log Injection via Filename
- Check if filenames are logged without sanitization.
- Attack Vector: Filename with newlines/control characters corrupts log parsing.
- Suggested Fix: Sanitize or encode filenames before logging.

---

## 8) Concurrent Upload & Race Conditions

### A) TOCTOU (Time-of-Check-Time-of-Use)
- Check for race conditions between validation and use of uploaded file.
- Attack Vector: File is validated, then replaced before processing.
- Suggested Fix: Validate and process atomically; use file descriptors not paths.

### B) Duplicate Upload Collision
- Check handling of simultaneous uploads with same document ID.
- Attack Vector: Race condition causes partial overwrite or corruption.
- Suggested Fix: Use atomic operations; implement locking; generate unique IDs server-side.

### C) Checkpoint Race Conditions
- Check for atomic checkpoint file writes during concurrent document processing.
- Attack Vector: Simultaneous checkpoint writes corrupt state.
- Suggested Fix: Write-then-rename pattern; file locking; per-document locks.

---

## Output Format (Mandatory)

For each issue found, provide:

```
[SEVERITY: CRITICAL | HIGH | MEDIUM | LOW]

Location: FileName : Line Number(s)
Risk Category: File Validation | Path Traversal | Resource Exhaustion | Injection | Race Condition

The Vulnerability:
- 2-4 sentences explaining the attack vector and potential impact.
- Be specific about attack type: RCE, data exfiltration, DoS, XSS, path traversal, etc.

Exploitation Scenario:
- Describe how an attacker would exploit this vulnerability.
- Include example malicious input if applicable.

How to Verify:
- A concrete verification step (send malicious file, test path, check logs, etc.).
- Security testing tool recommendation if applicable (Burp Suite, custom script, etc.).

The Fix:
- Provide the secure code snippet.
- Show before/after if useful.
- If fix requires library installation, include pip/npm command.

Defense in Depth:
- Additional layers of protection beyond the primary fix.
- Include monitoring/alerting recommendations.
```

## Severity Classification
- **CRITICAL**: Remote code execution, arbitrary file access, complete data breach possible.
- **HIGH**: Significant data exposure, denial of service, or privilege escalation.
- **MEDIUM**: Limited data exposure or functionality abuse.
- **LOW**: Minor security hygiene issue; defense in depth improvement.

---

## Security Score Rubric (1-10)

Rate overall file upload security based on severity/quantity of vulnerabilities:
- **9-10**: Production-ready; defense in depth implemented; minor improvements only.
- **7-8**: Needs 1-2 critical fixes; good security awareness evident.
- **5-6**: Multiple high/critical issues; significant security gaps.
- **3-4**: Fundamental security controls missing; high risk of exploitation.
- **<3**: Do not deploy; trivially exploitable; requires complete redesign.

---

## Include:
- The score
- Brief justification (2-5 bullets)
- A prioritized Top 5 fixes list (highest impact first)

## Final Section: Summary & Action Plan (Mandatory)
1) Fix Immediately (blocking deployment)
2) Fix Before Production (high priority)
3) Implement Soon (defense in depth)
4) Monitor (detection and response)

## Also include:
- Estimated time to implement all "Fix Immediately" items (range is fine)
- Security testing checklist:
  - [ ] Malicious file type test (executable disguised as PDF)
  - [ ] PDF bomb test (decompression ratio)
  - [ ] Path traversal test (../../../etc/passwd filename)
  - [ ] Oversized file test (exceed limits)
  - [ ] Malformed file test (corrupted headers)
  - [ ] Concurrent upload race condition test
  - [ ] Filename injection test (XSS, SQL, command)
- Recommended security tools:
  - `python-magic` for file type validation
  - `safety` or `pip-audit` for dependency scanning
  - `bandit` for static security analysis
  - OWASP ZAP for dynamic testing
