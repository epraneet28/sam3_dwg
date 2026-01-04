# Security Threat Model & Comprehensive Audit

**Priority:** P0 (Critical)
**Merged from:** Archive items #2 (Security Audit), #21 (File Upload Security), #23 (Image Processing Security)
**Status:** Active - Requires immediate attention before production deployment

---

## Role & Objective

Act as a **Senior Security Engineer** specializing in web application security, API security, document processing systems, file upload vulnerabilities, and image processing attacks. You have deep expertise in OWASP Top 10, secure file handling, authentication/authorization patterns, and identifying attack vectors in Python/FastAPI and React/TypeScript applications.

**Primary Goal:** Conduct a comprehensive security audit of the Docling-Interactive codebase to identify vulnerabilities, misconfigurations, and attack vectors across all security domains. Provide actionable remediation guidance with severity classifications.

## Context

⚠️ **AI-CODING RISK**: This codebase was **vibecoded** (rapidly prototyped) without formal security testing or threat modeling. Assume security best practices were NOT followed during initial development. The application handles sensitive document processing with file uploads, checkpoint storage, external API integrations, and real-time WebSocket communication.

**Your task**: Perform an adversarial security review. Think like an attacker. Identify every exploitable weakness.

## Tech Stack

**Backend:** 🐍 PYTHON/FASTAPI
- Python 3.12 + FastAPI + Uvicorn (ASGI server)
- Docling (document processing engine with ML models)
- Pydantic v2 (data validation)
- SQLite3 (database)
- OpenCV, Pillow, pdf2image (image/document processing)
- Label Studio SDK (annotation tool integration)
- WebSockets (real-time communication)

**Frontend:** ⚛️ REACT/TS
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

## Key Attack Surfaces

- PDF upload endpoint (arbitrary file upload)
- Checkpoint file storage and retrieval (path traversal)
- Label Studio API integration (leaked credentials)
- WebSocket connections (authentication bypass)
- SQLite database operations (SQL injection)
- File path handling throughout pipeline stages
- CORS configuration for frontend-backend communication
- Image processing endpoints (DoS, RCE via malicious images)
- Temporary file handling (race conditions, information disclosure)

---

## Detailed Audit Requirements

### 1. Authentication & Session Management

**1.1 Authentication Implementation**
- [ ] Is authentication implemented at all? Check for `/login`, `/auth`, token validation endpoints
- [ ] If using JWT/session tokens: Check signing algorithm (HS256 vs RS256), secret strength, expiration handling
- [ ] Search for hardcoded credentials in code
- [ ] Check for authentication bypass patterns (e.g., `if user or True:`)
- [ ] Verify authentication middleware is applied to ALL protected routes

**1.2 Session Security**
- [ ] Session token storage: httpOnly cookies vs localStorage (XSS risk)
- [ ] Session fixation vulnerabilities (token regeneration on login)
- [ ] Session timeout configuration
- [ ] Logout implementation (token invalidation vs client-side only)

**1.3 Password Handling**
- [ ] Password hashing algorithm (bcrypt/argon2 vs MD5/SHA1)
- [ ] Password complexity requirements
- [ ] Password reset flow security (token expiration, single-use tokens)

**Focus Areas:**
- `backend/api/endpoints/` - Authentication decorators/dependencies
- `backend/core/config/settings.py` - Secret key configuration
- `frontend/src/` - Token storage patterns
- WebSocket authentication handshake

### 2. Authorization & Access Control

**2.1 Insecure Direct Object References (IDOR)**
- [ ] Document access by ID: Can user A access user B's documents?
- [ ] Check endpoints like `/documents/{doc_id}`, `/checkpoints/{checkpoint_id}`
- [ ] Test: Do endpoints validate ownership before returning data?
- [ ] Search for queries like `SELECT * FROM documents WHERE id = ?` without user ownership check

**2.2 Privilege Escalation**
- [ ] Role-based access control (RBAC) implementation
- [ ] Admin vs regular user separation
- [ ] Can regular users access admin endpoints by guessing URLs?
- [ ] Check for role validation in endpoint decorators

**2.3 Path Traversal in File Access**
- [ ] Checkpoint retrieval: `/checkpoints/../../etc/passwd`
- [ ] PDF access: `/documents/../../../sensitive_file.pdf`
- [ ] Image access: `/images/{doc_id}/page_{page}/../../../config.json`
- [ ] Search for `os.path.join()` with user-controlled input
- [ ] Look for `open(user_input)` patterns without validation

**Focus Areas:**
- `backend/api/endpoints/documents_extended.py` - Document access control
- `backend/core/checkpoint/` - Checkpoint file path handling
- `backend/upload/validation.py` - File path validation

### 3. Injection Vulnerabilities

**3.1 SQL Injection**
- [ ] SQLite query construction patterns
- [ ] Search for string concatenation in queries: `f"SELECT * FROM {table} WHERE id={user_input}"`
- [ ] Check for parameterized queries vs raw string interpolation
- [ ] ORM usage (if any) - second-order injection risks

**3.2 Command Injection**
- [ ] Shell command execution with user input
- [ ] Search for `subprocess.run()`, `os.system()`, `subprocess.Popen()`
- [ ] Check PDF processing: Does pdf2image use shell=True?
- [ ] Image processing commands (ImageMagick, pdftoppm)

**3.3 Path Traversal (File System)**
- [ ] Checkpoint loading: User-controlled checkpoint paths
- [ ] File upload destination paths
- [ ] Export file paths
- [ ] Search for `os.path.join(base, user_input)` - does it use `os.path.abspath()` + prefix check?

**3.4 Server-Side Request Forgery (SSRF)**
- [ ] Label Studio integration: Can users control API endpoint URLs?
- [ ] Any URL fetching based on user input
- [ ] Webhook configurations

**Focus Areas:**
- Database query patterns throughout backend
- `backend/core/docling_pipeline/` - External command execution
- `backend/services/label_studio/` - API endpoint construction

### 4. Cross-Site Scripting (XSS) & CSRF

**4.1 Reflected XSS**
- [ ] API error messages: Do they reflect user input unsanitized?
- [ ] Search for error responses returning user input directly

**4.2 Stored XSS**
- [ ] Document metadata storage (filename, title, description)
- [ ] Checkpoint JSON content - is it ever rendered without sanitization?
- [ ] Label Studio annotations - malicious payloads in annotation data

**4.3 CSRF Protection**
- [ ] POST/PUT/DELETE endpoints: CSRF token validation?
- [ ] Check for SameSite cookie attribute
- [ ] State-changing GET requests (anti-pattern)

**4.4 Content Security Policy (CSP)**
- [ ] CSP headers configured?
- [ ] Inline script restrictions
- [ ] External resource loading policies

**Focus Areas:**
- FastAPI response models - raw string returns
- Frontend rendering of backend data (dangerouslySetInnerHTML usage)
- `backend/main.py` - Security header middleware

### 5. Secrets & Configuration Management

**5.1 Hardcoded Secrets**
- [ ] Search for API keys, passwords, tokens in code
- [ ] Check `.env.example` vs actual `.env` patterns
- [ ] Database credentials
- [ ] Label Studio API keys
- [ ] JWT signing secrets

**5.2 Environment Variable Security**
- [ ] Are secrets loaded from environment variables?
- [ ] `.env` file in `.gitignore`?
- [ ] Docker secrets vs environment variables in docker-compose
- [ ] Default/example secrets in production use

**5.3 Secrets in Logs**
- [ ] Logging configuration - are secrets redacted?
- [ ] Error messages exposing sensitive data
- [ ] Debug mode enabled in production

**Focus Areas:**
- `backend/core/config/settings.py` - Secret loading
- `.env`, `.env.example` files
- `backend/services/label_studio/` - API key handling

---

## 6. File Upload & Processing Security

⚠️ **AI-CODING RISK**: File upload security is often overlooked in AI-generated code. Document processing pipelines are high-value attack targets due to complex parsing logic and system-level operations.

### 6.1 File Type Validation (CRITICAL)

**6.1.1 Extension-Only Validation**
- [ ] Look for validation that only checks file extension (.pdf, .png) without magic byte verification
- [ ] Common hotspots: FastAPI upload endpoints, file save logic, import functions
- [ ] Attack Vector: Attacker uploads malicious.pdf that's actually an executable or polyglot file

**Vulnerable Pattern:**
```python
# VULNERABLE
if not filename.endswith('.pdf'):
    raise HTTPException(400, "Only PDF files allowed")
```

**Secure Pattern:**
```python
# SECURE
import magic

def validate_pdf(file_content: bytes) -> bool:
    mime = magic.from_buffer(file_content, mime=True)
    return mime == 'application/pdf'
```

**6.1.2 MIME Type Spoofing**
- [ ] Flag reliance on `Content-Type` header from request without server-side verification
- [ ] Attack Vector: Attacker sets `Content-Type: application/pdf` but sends malicious file
- [ ] Fix: Always verify file content server-side; never trust client-provided MIME types

**6.1.3 Polyglot File Detection**
- [ ] Check if system handles files that are valid in multiple formats (PDF/ZIP, PNG/HTML)
- [ ] Attack Vector: Polyglot file passes validation but exploits downstream parser
- [ ] Fix: Strict magic byte validation, content sanitization, and sandboxed processing

**6.1.4 Double Extension Attacks**
- [ ] Look for handling of files like `malicious.pdf.exe` or `file.php.pdf`
- [ ] Attack Vector: Web server or OS may execute based on secondary extension
- [ ] Fix: Extract and validate only the final extension; sanitize filename completely

**Magic Byte Reference:**
```python
MAGIC_BYTES = {
    'pdf': b'%PDF-',
    'png': b'\x89PNG\r\n\x1a\n',
    'jpeg': b'\xff\xd8\xff',
    'gif': b'GIF87a' or b'GIF89a',
}

def validate_magic_bytes(file_content: bytes, expected_type: str) -> bool:
    magic = MAGIC_BYTES.get(expected_type)
    if not magic:
        return False
    return file_content.startswith(magic)
```

### 6.2 PDF-Specific Attack Vectors (CRITICAL)

**6.2.1 PDF Bomb / Decompression Bomb**
- [ ] Check for limits on:
  - Decompression ratio (zip bomb inside PDF)
  - Page count limits
  - Embedded object limits
  - Stream size limits
- [ ] Attack Vector: 1KB PDF expands to 10GB, causing OOM or disk exhaustion

**Secure Implementation:**
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

**6.2.2 Malicious PDF JavaScript/Actions**
- [ ] Check if PDF parsing executes or preserves JavaScript, form actions, or launch commands
- [ ] Attack Vector: PDF with embedded JS runs when opened in viewer
- [ ] Fix: Strip or sanitize PDF actions during processing; use safe rendering mode

**6.2.3 External Entity Injection (XXE in PDF)**
- [ ] Check if PDF parser follows external references or URIs
- [ ] Attack Vector: PDF references external DTD/entity causing SSRF or data exfiltration
- [ ] Fix: Disable external entity resolution in PDF parsing libraries

**6.2.4 Embedded File Extraction**
- [ ] Check handling of PDFs with embedded files (attachments, portfolios)
- [ ] Attack Vector: Malicious files hidden in PDF attachments bypass scanning
- [ ] Fix: Extract and scan all embedded files; limit or block embedded content

### 6.3 Path Traversal & File System Attacks (CRITICAL)

**6.3.1 Path Traversal in Upload Filename**
- [ ] Look for user-controlled filenames used in file paths without sanitization
- [ ] Common patterns: `os.path.join(upload_dir, filename)`, `f"{base_path}/{filename}"`
- [ ] Attack Vector: Filename `../../../etc/passwd` or `....//....//etc/passwd` escapes upload directory

**Vulnerable Pattern:**
```python
# VULNERABLE
save_path = os.path.join(UPLOAD_DIR, request.filename)
```

**Secure Pattern:**
```python
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

**6.3.2 Symlink Following**
- [ ] Check if file operations follow symlinks that could point outside allowed directories
- [ ] Attack Vector: Attacker creates symlink in upload directory pointing to sensitive files
- [ ] Fix: Use `os.path.realpath()` and verify final path is within allowed directory

**6.3.3 Checkpoint File Path Injection**
- [ ] Check if checkpoint filenames or paths are derived from user input (document IDs, page numbers)
- [ ] Attack Vector: Malicious document ID like `../../config` writes to arbitrary location
- [ ] Fix: Validate and sanitize all path components; use allowlist for path patterns

**6.3.4 Temporary File Predictable Names**
- [ ] Look for tempfile creation with predictable names or insecure permissions
- [ ] Attack Vector: Race condition allows attacker to replace temp file before processing
- [ ] Fix: Use `tempfile.mkstemp()` or `tempfile.NamedTemporaryFile()` with secure defaults

### 6.4 File Size & Resource Exhaustion (CRITICAL)

**6.4.1 Missing Upload Size Limits**
- [ ] Check for explicit file size limits in FastAPI/Starlette configuration
- [ ] Attack Vector: 10GB upload exhausts disk space, memory, or causes timeout

**Secure Implementation:**
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

**6.4.2 Memory Exhaustion via Large Files**
- [ ] Check if entire file is read into memory vs streamed
- [ ] Attack Vector: Large file causes OOM, crashing the application
- [ ] Fix: Stream file processing; use chunked reading; implement memory limits

**6.4.3 Disk Exhaustion via Temp Files**
- [ ] Check for cleanup of temporary files after processing (success or failure)
- [ ] Attack Vector: Failed uploads accumulate, filling disk
- [ ] Fix: Use context managers; implement cleanup on exception; periodic cleanup job

**6.4.4 Processing Time Limits**
- [ ] Check for timeouts on document processing operations
- [ ] Attack Vector: Malformed PDF causes infinite loop or extremely long processing
- [ ] Fix: Implement processing timeouts; use subprocess with timeout for heavy operations

### 6.5 Temporary File Security (CRITICAL)

**6.5.1 Insecure Temp Directory**
- [ ] Check if temp files are created in predictable or shared locations
- [ ] Attack Vector: Other users on shared system can access/modify temp files

**Secure Pattern:**
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

**6.5.2 Temp File Cleanup Failures**
- [ ] Check for cleanup in finally blocks or context managers
- [ ] Look for exceptions that skip cleanup code
- [ ] Attack Vector: Sensitive document data persists in temp files after processing
- [ ] Fix: Use `try/finally` or context managers; implement background cleanup

**6.5.3 Temp File Permission Issues**
- [ ] Check permissions on created temp files (should not be world-readable)
- [ ] Attack Vector: Sensitive data in temp files readable by other processes
- [ ] Fix: Set restrictive permissions (0600) on creation

**6.5.4 Orphaned Temp Files After Crash**
- [ ] Check for startup cleanup of stale temp files from previous runs
- [ ] Attack Vector: Accumulated temp files from crashes leak data or exhaust disk
- [ ] Fix: Implement startup cleanup based on file age; use unique session directories

### 6.6 Filename & Content Injection

**6.6.1 Filename XSS in UI Display**
- [ ] Check if original filenames are displayed in frontend without sanitization
- [ ] Attack Vector: Filename `<script>alert('xss')</script>.pdf` executes in browser
- [ ] Fix: HTML-escape filenames; use sanitized display names

**6.6.2 SQL Injection via Filename**
- [ ] Check if filenames are used in database queries without parameterization
- [ ] Attack Vector: Filename containing SQL injection payload corrupts database
- [ ] Fix: Always use parameterized queries; never interpolate filenames

**6.6.3 Command Injection via Filename**
- [ ] Check if filenames are passed to shell commands or subprocess
- [ ] Attack Vector: Filename `; rm -rf /; .pdf` executes shell command

**Vulnerable vs Secure:**
```python
# VULNERABLE
import subprocess
subprocess.run(f"pdfinfo {uploaded_file}", shell=True)

# SECURE
subprocess.run(["pdfinfo", uploaded_file], shell=False, check=True)
```

**6.6.4 Log Injection via Filename**
- [ ] Check if filenames are logged without sanitization
- [ ] Attack Vector: Filename with newlines/control characters corrupts log parsing
- [ ] Fix: Sanitize or encode filenames before logging

### 6.7 Concurrent Upload & Race Conditions

**6.7.1 TOCTOU (Time-of-Check-Time-of-Use)**
- [ ] Check for race conditions between validation and use of uploaded file
- [ ] Attack Vector: File is validated, then replaced before processing
- [ ] Fix: Validate and process atomically; use file descriptors not paths

**6.7.2 Duplicate Upload Collision**
- [ ] Check handling of simultaneous uploads with same document ID
- [ ] Attack Vector: Race condition causes partial overwrite or corruption
- [ ] Fix: Use atomic operations; implement locking; generate unique IDs server-side

**6.7.3 Checkpoint Race Conditions**
- [ ] Check for atomic checkpoint file writes during concurrent document processing
- [ ] Attack Vector: Simultaneous checkpoint writes corrupt state
- [ ] Fix: Write-then-rename pattern; file locking; per-document locks

**Focus Areas:**
- `backend/upload/validation.py` - Upload validation logic
- `backend/api/endpoints/upload.py` - Upload endpoints
- `backend/core/checkpoint/` - Checkpoint management
- `backend/services/pdf_image_extractor/` - PDF processing

---

## 7. Image Processing Security

⚠️ **AI-CODING RISK**: Image processing is a high-risk attack surface due to complex parsers handling untrusted input. The codebase may have overlooked image security best practices.

### 7.1 Malicious Image Exploitation (CRITICAL)

**7.1.1 Image Parsing Vulnerabilities (CVE Surface)**
- [ ] Check for outdated Pillow/OpenCV versions with known CVEs
- [ ] Look for use of deprecated or vulnerable image formats (e.g., EPS without sandboxing)
- [ ] Flag missing `Image.MAX_IMAGE_PIXELS` limits
- [ ] Fix: Update libraries, set pixel limits, disable risky formats

**Common Image Processing CVEs:**

| Library | CVE Examples | Impact |
|---------|--------------|--------|
| Pillow | CVE-2022-45199 (DoS), CVE-2023-44271 (DoS) | Memory exhaustion |
| OpenCV | CVE-2019-5064 (heap overflow), CVE-2017-12597 (buffer overflow) | RCE potential |
| Poppler | CVE-2022-38784 (integer overflow), numerous parsing bugs | RCE, DoS |
| libpng | CVE-2019-7317 (use-after-free) | RCE potential |
| libjpeg | CVE-2020-14152 (buffer overflow) | RCE potential |

**7.1.2 Decompression Bombs (Image Zip Bombs)**
- [ ] Identify missing checks for decompression ratio (small file -> huge pixels)
- [ ] Look for images that could expand to gigabytes in memory
- [ ] Common vectors: PNG, TIFF, GIF with high compression ratios
- [ ] Fix: Implement `Image.MAX_IMAGE_PIXELS`, check dimensions before full decode

**7.1.3 SVG/XML Injection (if SVG processing exists)**
- [ ] Flag any SVG parsing without sanitization
- [ ] Look for XXE (XML External Entity) vulnerabilities
- [ ] Check for JavaScript injection in SVG files
- [ ] Fix: Use defusedxml, sanitize SVG, or reject SVG entirely

**7.1.4 Polyglot Files**
- [ ] Identify if file type detection relies only on extension
- [ ] Look for files that could be valid images AND malicious scripts
- [ ] Check for GIFAR, image/HTML polyglots
- [ ] Fix: Validate magic bytes, re-encode images, strip metadata

### 7.2 Resource Exhaustion (DoS Vectors) (CRITICAL)

**7.2.1 Image Dimension Limits (OOM Prevention)**
- [ ] Find image operations without dimension checks
- [ ] Look for missing limits on width, height, and total pixels
- [ ] Flag operations that scale with image size (resize, filter, convolution)
- [ ] Fix: Enforce max dimensions (e.g., 10000x10000), check before processing

**7.2.2 Memory Growth During Processing**
- [ ] Identify operations that create multiple full-size copies in memory
- [ ] Look for missing cleanup of intermediate images
- [ ] Flag long-running operations without memory bounds
- [ ] Fix: Process in tiles/chunks, explicit cleanup, memory limits

**7.2.3 CPU Exhaustion via Complex Operations**
- [ ] Find expensive operations (resize with high-quality filters, complex transforms)
- [ ] Look for operations inside loops without bounds
- [ ] Flag missing timeouts on image processing
- [ ] Fix: Use faster algorithms for untrusted input, add timeouts

**7.2.4 Disk Exhaustion**
- [ ] Identify temporary file creation without size limits
- [ ] Look for missing cleanup of generated images
- [ ] Flag unbounded caching of processed images
- [ ] Fix: Temp file quotas, cleanup on error, cache size limits

### 7.3 Pillow-Specific Security Issues

**7.3.1 Image.MAX_IMAGE_PIXELS Configuration**
- [ ] Default is 178,956,970 pixels (~13400x13400)
- [ ] Check if this is set appropriately for your use case
- [ ] Flag if set to None (disabled)
- [ ] Fix: Set explicit limit based on expected document sizes

**Pillow Security Configuration:**
```python
from PIL import Image

# Set maximum image size (pixels) - prevents decompression bombs
Image.MAX_IMAGE_PIXELS = 89_478_485  # ~9500x9500, adjust based on needs

# Recommended: Restrict to safe formats only
ALLOWED_FORMATS = {'JPEG', 'PNG', 'WEBP', 'GIF'}

def safe_open_image(file_path: str) -> Image.Image:
    """Safely open an image with security checks."""
    img = Image.open(file_path)

    # Verify format
    if img.format not in ALLOWED_FORMATS:
        raise ValueError(f"Unsupported format: {img.format}")

    # Verify dimensions
    if img.width > 10000 or img.height > 10000:
        raise ValueError(f"Image too large: {img.width}x{img.height}")

    # Load into memory (triggers decompression bomb check)
    img.load()

    return img
```

**7.3.2 Format-Specific Risks**
- [ ] EPS/PS: Can execute PostScript (RCE risk)
- [ ] PDF: Pillow's PDF support is limited; check if pdf2image is used instead
- [ ] ICO: Can have multiple embedded images causing expansion
- [ ] Fix: Explicitly whitelist safe formats, reject others

**7.3.3 Pillow Plugin Security**
- [ ] Check for custom image plugins or format handlers
- [ ] Look for use of external decoders (ImageMagick, Ghostscript)
- [ ] Flag insecure ImageMagick policy.xml configuration
- [ ] Fix: Audit plugins, secure ImageMagick policy, prefer pure-Pillow formats

### 7.4 OpenCV-Specific Security Issues

**7.4.1 Buffer Overflow Risks**
- [ ] OpenCV's C++ core can have buffer overflows with malformed images
- [ ] Check for operations on images with unexpected channel counts
- [ ] Flag missing validation of image dimensions before array operations
- [ ] Fix: Validate image properties, use try/except around cv2 calls

**7.4.2 Codec Vulnerabilities**
- [ ] OpenCV uses system codecs (libjpeg, libpng, etc.) which may have vulnerabilities
- [ ] Check for use of cv2.imdecode with untrusted data
- [ ] Flag missing format restrictions
- [ ] Fix: Restrict to safe formats, update system libraries, sandbox processing

**OpenCV Security Configuration:**
```python
import cv2
import numpy as np

MAX_DIMENSION = 10000
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def safe_imread(file_path: str) -> np.ndarray:
    """Safely read an image with security checks."""
    import os

    # Check file size first
    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"File too large: {file_size} bytes")

    # Read image
    img = cv2.imread(file_path)
    if img is None:
        raise ValueError("Failed to decode image")

    # Check dimensions
    height, width = img.shape[:2]
    if width > MAX_DIMENSION or height > MAX_DIMENSION:
        raise ValueError(f"Image too large: {width}x{height}")

    return img
```

**7.4.3 Video Processing Risks (if applicable)**
- [ ] cv2.VideoCapture can process malicious video files
- [ ] Look for unbounded frame extraction
- [ ] Flag missing duration/frame limits
- [ ] Fix: Limit frame count, add timeouts, sandbox video processing

### 7.5 pdf2image/Poppler Security Issues

**7.5.1 Poppler CVE Exposure**
- [ ] Poppler has had numerous CVEs for malformed PDFs
- [ ] Check for version and whether security updates are applied
- [ ] Flag if processing untrusted PDFs without sandboxing
- [ ] Fix: Keep Poppler updated, sandbox PDF processing, use Docker isolation

**7.5.2 Resource Limits for PDF Rendering**
- [ ] PDFs can request extremely high DPI rendering
- [ ] Check for unbounded page counts
- [ ] Flag missing timeouts on PDF conversion
- [ ] Fix: Cap DPI (e.g., 300), limit pages, add timeouts

**7.5.3 Temporary File Security**
- [ ] pdf2image creates temp files for each page
- [ ] Check for secure temp directory usage
- [ ] Flag if temp files are predictable or world-readable
- [ ] Fix: Use tempfile.mkdtemp(), secure permissions, cleanup in finally

### 7.6 Memory Cleanup & Lifecycle Management

**7.6.1 Explicit Memory Release**
- [ ] Check for explicit `.close()` on Image objects
- [ ] Look for `del` or context managers for large images
- [ ] Flag long-lived image objects in global scope
- [ ] Fix: Use context managers, explicit cleanup, weak references for caches

**7.6.2 NumPy Array Cleanup (OpenCV)**
- [ ] OpenCV returns NumPy arrays which can hold large memory
- [ ] Check for explicit `del` of arrays after use
- [ ] Look for arrays kept in lists/dicts without bounds
- [ ] Fix: Explicit deletion, bounded collections, garbage collection hints

**7.6.3 EXIF/Metadata Memory**
- [ ] EXIF data can be surprisingly large (embedded thumbnails, GPS data)
- [ ] Check for metadata stripping before storage
- [ ] Flag if original metadata is preserved unnecessarily
- [ ] Fix: Strip metadata for privacy and memory, preserve only what's needed

### 7.7 Secure Image Handling Patterns

**7.7.1 Re-encoding for Safety**
- [ ] Best practice: Re-encode untrusted images to strip malicious content
- [ ] Check if images are re-saved in a safe format before further processing
- [ ] Flag direct use of untrusted bytes in multiple operations
- [ ] Fix: Decode -> validate -> re-encode to safe format (PNG/JPEG)

**7.7.2 Sandboxed Processing**
- [ ] Check for isolation of image processing (subprocess, container, seccomp)
- [ ] Look for privilege separation between upload and processing
- [ ] Flag if image processing runs with full application privileges
- [ ] Fix: Process images in isolated subprocess/container with limited permissions

**7.7.3 Secure Defaults**
- [ ] Check for explicit security configuration in image libraries
- [ ] Look for commented-out security settings
- [ ] Flag "TODO: add security" comments
- [ ] Fix: Enable all security features, document configuration

**Focus Areas:**
- `backend/services/pdf_image_extractor/` - PDF to image conversion
- `backend/core/docling_pipeline/` - Image processing operations
- Anywhere Pillow, OpenCV, or pdf2image is imported and used

---

## 8. WebSocket Security

**8.1 WebSocket Authentication**
- [ ] Are WebSocket connections authenticated?
- [ ] Token validation on connection handshake
- [ ] Can unauthenticated users connect and receive data?

**8.2 WebSocket Authorization**
- [ ] Per-message authorization checks
- [ ] Can user A subscribe to user B's document processing updates?
- [ ] Room/channel isolation (if implemented)

**8.3 Message Injection**
- [ ] User-controlled message content - is it validated?
- [ ] JSON injection in WebSocket messages
- [ ] Message flooding/DoS protection

**8.4 WebSocket Origin Validation**
- [ ] Origin header checking
- [ ] Cross-Site WebSocket Hijacking (CSWSH)

**Focus Areas:**
- `backend/websocket/handlers.py` - Connection handling
- `backend/websocket/manager.py` - WebSocket manager
- WebSocket authentication middleware

---

## 9. API Security

**9.1 CORS Configuration**
- [ ] Allowed origins - wildcard (`*`) vs specific domains?
- [ ] Credentials allowed with CORS?
- [ ] Overly permissive CORS enabling CSRF

**9.2 Rate Limiting**
- [ ] Rate limiting implemented on endpoints?
- [ ] Brute force protection on authentication
- [ ] DoS protection on expensive operations (PDF processing)

**9.3 API Information Disclosure**
- [ ] Verbose error messages exposing stack traces
- [ ] `/docs`, `/redoc` endpoints in production
- [ ] Debug mode enabled

**9.4 Input Validation**
- [ ] Pydantic model validation - are all inputs validated?
- [ ] Type coercion bypasses
- [ ] Extra fields allowed in Pydantic models (`Extra.allow` risk)
- [ ] Array/object size limits (JSON bomb attacks)

**9.5 HTTP Security Headers**
- [ ] Strict-Transport-Security (HSTS)
- [ ] X-Content-Type-Options: nosniff
- [ ] X-Frame-Options: DENY
- [ ] Referrer-Policy
- [ ] Permissions-Policy

**Focus Areas:**
- `backend/main.py` - CORS, middleware, security headers
- `backend/middleware/rate_limiter.py` - Rate limiting implementation
- Pydantic models in `backend/api/models/`

---

## 10. Dependency & Supply Chain Security

**10.1 Vulnerable Dependencies**
- [ ] Run `pip-audit` - check for known CVEs
- [ ] Check `npm audit` for frontend vulnerabilities
- [ ] Docling dependency tree - transitive vulnerabilities
- [ ] Pillow, OpenCV CVEs (image processing bugs)

**10.2 Dependency Pinning**
- [ ] `requirements.txt` - pinned versions vs `package>=1.0`?
- [ ] `package-lock.json` present and committed?
- [ ] Docker base image pinning

**10.3 Malicious Package Risk**
- [ ] Typosquatting in requirements
- [ ] Unmaintained packages (last update > 2 years ago)
- [ ] Supply chain attack vectors

**Focus Areas:**
- `requirements.txt` or `pyproject.toml`
- `package.json` and `package-lock.json`
- `Dockerfile` base images

---

## 11. Infrastructure & Deployment Security

**11.1 Docker Security**
- [ ] Running as root user in container?
- [ ] Sensitive data in Docker layers
- [ ] Docker socket exposure
- [ ] Secrets in environment variables vs Docker secrets

**11.2 File System Permissions**
- [ ] Checkpoint directory permissions
- [ ] Upload directory permissions
- [ ] Log file permissions
- [ ] SQLite database file permissions

**11.3 Database Security**
- [ ] SQLite file permissions (world-readable?)
- [ ] Database encryption at rest
- [ ] Backup security

**Focus Areas:**
- `Dockerfile` - user configuration, permissions
- File system setup scripts
- Database initialization

---

## Severity Classification

- **CRITICAL**: Immediate exploitation possible, severe impact (RCE, data breach, auth bypass)
- **HIGH**: Exploitable with moderate effort, significant impact (IDOR, XSS, SQL injection)
- **MEDIUM**: Requires specific conditions, moderate impact (info disclosure, weak config)
- **MONITOR**: Potential risk, needs investigation or hardening (dependency updates, best practices)

---

## Finding Template

For each issue found, provide:

```
## [SEVERITY] Finding #N: [Concise Title]

**Location:**
- File: `/path/to/file.py` (lines X-Y)
- Component: [Backend API / Frontend / WebSocket / Docker / etc.]

**Risk Category:** [Authentication / Authorization / Injection / XSS / File Upload / Image Processing / etc.]

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
- **Breakdown:** Authentication (X/10), Authorization (X/10), Input Validation (X/10), File Security (X/10), Image Processing (X/10), Infrastructure (X/10)
- **Biggest Risk:** [The single most critical issue to fix immediately]

---

## Summary & Action Plan

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
- [ ] Implement PDF bomb protection (size/page limits)
- [ ] Configure Pillow MAX_IMAGE_PIXELS limit
- [ ] Add image dimension validation
- [ ] Secure checkpoint file path handling
- [ ] Secure temporary file creation and cleanup
- [ ] Rotate and externalize all secrets
- [ ] Update vulnerable dependencies
- [ ] Implement CSRF protection
- [ ] Add WebSocket authentication
- [ ] Enable audit logging
- [ ] Implement principle of least privilege
- [ ] Sandbox image and PDF processing

### Security Testing Checklist
- [ ] Malicious file type test (executable disguised as PDF)
- [ ] PDF bomb test (decompression ratio, page count)
- [ ] Image bomb test (dimension flood, pixel flood)
- [ ] Path traversal test (`../../../etc/passwd` filename)
- [ ] Oversized file test (exceed upload limits)
- [ ] Malformed file test (corrupted headers)
- [ ] Polyglot file test (PDF/ZIP, image/HTML)
- [ ] Concurrent upload race condition test
- [ ] Filename injection test (XSS, SQL, command)
- [ ] Image metadata injection test
- [ ] Temporary file security test
- [ ] CVE reproduction tests (Pillow, OpenCV, Poppler)

### Recommended Security Tools
- [ ] `python-magic` for file type validation
- [ ] `safety` or `pip-audit` for dependency scanning
- [ ] `bandit` for static security analysis
- [ ] `npm audit` for frontend dependency scanning
- [ ] OWASP ZAP for dynamic testing
- [ ] Image fuzzing test suite
- [ ] Memory profiling for image operations

### Compliance & Standards
- [ ] OWASP Top 10 compliance check
- [ ] GDPR considerations (if processing EU user data)
- [ ] SOC 2 preparation (if enterprise customers)

---

## Instructions for Audit

1. **Start with reconnaissance**: Map attack surface, identify all entry points
2. **Prioritize by risk**: Focus on auth, file uploads, image processing, and data access first
3. **Test assumptions**: Don't assume validation exists - verify in code
4. **Think like an attacker**: How would you exploit this for maximum impact?
5. **Be specific**: Provide exact file paths, line numbers, and exploit code
6. **Provide fixes**: Every finding needs actionable remediation
7. **Consider context**: Balance security with project maturity and use case

**Deliverable**: Comprehensive security audit report with prioritized findings, proof-of-concept exploits where safe, and remediation roadmap.
