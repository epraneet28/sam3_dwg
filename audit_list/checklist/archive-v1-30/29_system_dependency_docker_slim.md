# System Dependency Audit (Docker-Slim) Prompt

## Role
Act as a Senior DevOps Engineer and Container Security Specialist. Perform a deep-dive System Dependency Audit on the Dockerfile and build configuration to ensure the application runs correctly in a Python-slim container environment.

## Primary Goal
Identify missing system libraries, binary dependencies, and runtime requirements that AI-generated Dockerfiles often overlook when using slim base images. Ensure the container will function identically to the development environment.

## Context
- This is a document processing application using Python 3.11-slim-bookworm as the base image.
- AI-assisted development ("vibe coding") often assumes libraries are pre-installed when they are not.
- The application uses OpenCV, Pillow, pdf2image, and Docling which have significant native library requirements.
- Failures often manifest only at runtime, not during container build.

## Tech Stack
- **Base Image**: Python 3.11-slim-bookworm
- **Backend**: Python 3.12 + FastAPI + Uvicorn
- **Document Processing**: Docling (ML-based document understanding)
- **Image Processing**: OpenCV, Pillow, pdf2image
- **PDF Handling**: poppler-utils, pdf2image
- **Database**: SQLite3
- **External Integration**: Label Studio SDK
- **Frontend Build**: Node.js (for Vite/React build)

## Critical System Dependencies by Package

### OpenCV (`opencv-python` / `opencv-python-headless`)
Required system libraries:
- `libgl1` or `libgl1-mesa-glx` (OpenGL)
- `libglib2.0-0` (GLib)
- `libsm6` (X11 Session Management)
- `libxext6` (X11 extensions)
- `libxrender1` (X Render Extension)
- `libgomp1` (OpenMP runtime - for parallel processing)

### pdf2image
Required system libraries:
- `poppler-utils` (pdftoppm, pdfinfo binaries)

### Pillow
Required system libraries:
- `libjpeg62-turbo` or `libjpeg-dev` (JPEG support)
- `libpng16-16` or `libpng-dev` (PNG support)
- `libtiff6` or `libtiff-dev` (TIFF support)
- `libwebp7` or `libwebp-dev` (WebP support)
- `zlib1g` (compression)
- `libfreetype6` (font rendering)
- `liblcms2-2` (color management)

### python-magic / libmagic
Required system libraries:
- `libmagic1` (file type detection)

### Docling & ML Models
Required system libraries:
- `libgomp1` (OpenMP for PyTorch/transformers)
- `libstdc++6` (C++ standard library)
- Potentially GPU libraries if using CUDA

### General Python Build Dependencies
Build-time only (can be removed after pip install):
- `gcc`, `g++` (C/C++ compiler)
- `python3-dev` (Python headers)
- `libffi-dev` (Foreign Function Interface)
- `build-essential` (meta-package for build tools)

---

## Audit Requirements

Scan the Dockerfile, docker-compose files, and requirements.txt to identify issues in the following categories:

---

## 1) Missing Runtime Libraries

### A) OpenCV Library Dependencies
- Check if `libgl1-mesa-glx` or `libgl1` is installed.
- Check if `libglib2.0-0` is installed.
- Check if OpenMP (`libgomp1`) is installed for parallel operations.
- **Failure Mode**: `ImportError: libGL.so.1: cannot open shared object file`
- **Suggested Fix**: Add to Dockerfile:
  ```dockerfile
  RUN apt-get update && apt-get install -y --no-install-recommends \
      libgl1-mesa-glx \
      libglib2.0-0 \
      libsm6 \
      libxext6 \
      libxrender1 \
      libgomp1 \
      && rm -rf /var/lib/apt/lists/*
  ```

### B) Poppler Utilities for pdf2image
- Check if `poppler-utils` is installed (provides `pdftoppm`, `pdfinfo`).
- **Failure Mode**: `PDFInfoNotInstalledError: Unable to get page count. Is poppler installed and in PATH?`
- **Suggested Fix**: Add to Dockerfile:
  ```dockerfile
  RUN apt-get update && apt-get install -y --no-install-recommends \
      poppler-utils \
      && rm -rf /var/lib/apt/lists/*
  ```

### C) Pillow Image Format Support
- Check if image format libraries are installed (JPEG, PNG, TIFF, WebP).
- **Failure Mode**: `IOError: decoder jpeg not available` or similar
- **Suggested Fix**: Add to Dockerfile:
  ```dockerfile
  RUN apt-get update && apt-get install -y --no-install-recommends \
      libjpeg62-turbo \
      libpng16-16 \
      libtiff6 \
      libwebp7 \
      zlib1g \
      libfreetype6 \
      liblcms2-2 \
      && rm -rf /var/lib/apt/lists/*
  ```

### D) libmagic for File Type Detection
- Check if `libmagic1` is installed for python-magic.
- **Failure Mode**: `ImportError: failed to find libmagic`
- **Suggested Fix**: Add to Dockerfile:
  ```dockerfile
  RUN apt-get update && apt-get install -y --no-install-recommends \
      libmagic1 \
      && rm -rf /var/lib/apt/lists/*
  ```

---

## 2) Build-Time vs Runtime Dependency Separation

### A) Multi-Stage Build Pattern
- Check if the Dockerfile uses multi-stage builds to separate build and runtime dependencies.
- **Risk**: Including build tools in final image increases size and attack surface.
- **Suggested Fix**: Use multi-stage build:
  ```dockerfile
  # Build stage
  FROM python:3.11-slim-bookworm AS builder
  RUN apt-get update && apt-get install -y --no-install-recommends \
      gcc g++ python3-dev libffi-dev build-essential
  COPY requirements.txt .
  RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

  # Runtime stage
  FROM python:3.11-slim-bookworm AS runtime
  COPY --from=builder /wheels /wheels
  RUN pip install --no-cache-dir /wheels/*
  ```

### B) Development Dependencies in Production
- Check if `pytest`, `black`, `ruff`, `mypy` are in production requirements.
- **Risk**: Unnecessary packages increase image size and potential vulnerabilities.
- **Suggested Fix**: Separate `requirements.txt` and `requirements-dev.txt`.

### C) Unused Build Artifacts
- Check if `/root/.cache/pip` is cleaned after pip install.
- Check if apt lists are removed after apt-get install.
- **Suggested Fix**:
  ```dockerfile
  RUN pip install --no-cache-dir -r requirements.txt
  RUN apt-get clean && rm -rf /var/lib/apt/lists/*
  ```

---

## 3) Missing Fonts & Locale Configuration

### A) Font Availability for Document Rendering
- Check if fonts are installed for Pillow text rendering and document processing.
- **Failure Mode**: `OSError: cannot open resource` when rendering text.
- **Suggested Fix**:
  ```dockerfile
  RUN apt-get update && apt-get install -y --no-install-recommends \
      fonts-liberation \
      fonts-dejavu-core \
      fontconfig \
      && rm -rf /var/lib/apt/lists/* \
      && fc-cache -f -v
  ```

### B) Locale Configuration
- Check if locale is properly configured (important for text processing).
- **Failure Mode**: `UnicodeDecodeError` or encoding issues.
- **Suggested Fix**:
  ```dockerfile
  ENV LANG=C.UTF-8
  ENV LC_ALL=C.UTF-8
  ```

---

## 4) SQLite Runtime Requirements

### A) SQLite3 Binary and Libraries
- Check if SQLite3 is available (usually included in Python, but check for CLI tools).
- **Note**: Python's sqlite3 module is built-in, but CLI tools may be needed for debugging.
- **Suggested Fix** (if CLI needed):
  ```dockerfile
  RUN apt-get update && apt-get install -y --no-install-recommends \
      sqlite3 \
      && rm -rf /var/lib/apt/lists/*
  ```

---

## 5) Network & SSL Dependencies

### A) SSL/TLS Certificate Bundle
- Check if CA certificates are installed for HTTPS requests.
- **Failure Mode**: `ssl.SSLCertVerificationError: certificate verify failed`
- **Suggested Fix**:
  ```dockerfile
  RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates \
      && rm -rf /var/lib/apt/lists/*
  ```

### B) curl/wget for Health Checks
- Check if curl is available for container health checks.
- **Suggested Fix**:
  ```dockerfile
  RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
      && rm -rf /var/lib/apt/lists/*
  HEALTHCHECK CMD curl --fail http://localhost:8000/health || exit 1
  ```

---

## 6) ML/AI Model Dependencies (Docling-specific)

### A) PyTorch/Transformers Runtime Libraries
- Check if C++ standard library is up to date for PyTorch.
- Check if OpenMP is available for model inference parallelism.
- **Failure Mode**: `libstdc++.so.6: version 'GLIBCXX_3.4.29' not found`
- **Suggested Fix**:
  ```dockerfile
  RUN apt-get update && apt-get install -y --no-install-recommends \
      libstdc++6 \
      libgomp1 \
      && rm -rf /var/lib/apt/lists/*
  ```

### B) Model Download at Runtime
- Check if the Dockerfile pre-downloads models or if they're downloaded at runtime.
- **Risk**: First request takes minutes while models download.
- **Suggested Fix**: Pre-download models during build:
  ```dockerfile
  RUN python -c "from docling.document_converter import DocumentConverter; DocumentConverter()"
  ```

---

## 7) File System & Permission Issues

### A) Non-Root User Configuration
- Check if the container runs as non-root for security.
- **Risk**: Running as root increases container escape risk.
- **Suggested Fix**:
  ```dockerfile
  RUN useradd --create-home --shell /bin/bash appuser
  USER appuser
  WORKDIR /home/appuser/app
  ```

### B) Writable Directories
- Check if checkpoint, upload, and temp directories are created with correct permissions.
- **Failure Mode**: `PermissionError: [Errno 13] Permission denied`
- **Suggested Fix**:
  ```dockerfile
  RUN mkdir -p /app/checkpoints /app/uploads /app/temp \
      && chown -R appuser:appuser /app
  ```

### C) Volume Mount Points
- Check if volume mount points exist in the image.
- **Risk**: Volumes mounted over non-existent directories can cause issues.
- **Suggested Fix**: Create mount point directories in Dockerfile.

---

## 8) Process Management & Signals

### A) Proper Signal Handling
- Check if the application handles SIGTERM for graceful shutdown.
- Check if `exec` form is used in CMD/ENTRYPOINT.
- **Risk**: Container doesn't shut down gracefully, causing data loss.
- **Suggested Fix**:
  ```dockerfile
  # Use exec form, not shell form
  CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
  # NOT: CMD uvicorn main:app --host 0.0.0.0 --port 8000
  ```

### B) PID 1 and Zombie Processes
- Check if tini or dumb-init is used as PID 1.
- **Risk**: Zombie processes accumulate without proper init system.
- **Suggested Fix**:
  ```dockerfile
  RUN apt-get update && apt-get install -y --no-install-recommends tini
  ENTRYPOINT ["/usr/bin/tini", "--"]
  CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```

---

## 9) Version Pinning & Reproducibility

### A) Base Image Version Pinning
- Check if base image uses a specific digest or tag (not `latest`).
- **Risk**: Builds become non-reproducible as base image changes.
- **Suggested Fix**:
  ```dockerfile
  # Use specific tag
  FROM python:3.11.7-slim-bookworm
  # Or use digest for maximum reproducibility
  FROM python:3.11-slim-bookworm@sha256:abc123...
  ```

### B) System Package Version Pinning
- Check if apt packages are version-pinned.
- **Note**: This is often impractical; use specific base image version instead.

### C) Python Package Version Pinning
- Check if requirements.txt has pinned versions with hashes.
- **Suggested Fix**: Use `pip-compile` to generate locked requirements.

---

## 10) Security Hardening

### A) Unnecessary Package Removal
- Check for packages that shouldn't be in production (compilers, debug tools).
- **Suggested Fix**: Don't install unnecessary packages; use `--no-install-recommends`.

### B) Read-Only Root Filesystem Compatibility
- Check if the application can run with read-only root filesystem.
- **Risk**: Attackers can't modify container if filesystem is read-only.
- **Suggested Fix**: Use tmpfs for writable directories:
  ```yaml
  # docker-compose.yml
  read_only: true
  tmpfs:
    - /tmp
    - /app/temp
  ```

### C) Security Scanning Integration
- Check if Dockerfile has LABEL for security scanning tools.
- **Suggested Fix**:
  ```dockerfile
  LABEL org.opencontainers.image.source="https://github.com/org/repo"
  LABEL org.opencontainers.image.description="Document processing pipeline"
  ```

---

## Output Format (Mandatory)

For each issue found, provide:

```
[SEVERITY: CRITICAL | HIGH | MEDIUM | LOW]

Location: Dockerfile : Line Number(s) or requirements.txt

Dependency Category: Runtime Library | Build Tool | Font/Locale | Security | Configuration

The Problem:
- 2-4 sentences explaining what's missing and when the failure occurs.
- Be specific: build-time error vs runtime error vs first-request error.

Failure Mode:
- Exact error message or behavior when this dependency is missing.
- Example: "ImportError: libGL.so.1: cannot open shared object file"

How to Verify:
- Command to test if dependency is present.
- Example: `docker run --rm image python -c "import cv2; print(cv2.__version__)"`
- Example: `docker run --rm image which pdftoppm`

The Fix:
- Provide the exact Dockerfile changes needed.
- Show the apt-get install command or multi-stage build pattern.
- Include cleanup steps to minimize image size.

Image Size Impact:
- Estimate the size increase from adding this dependency.
- Example: "libgl1-mesa-glx adds ~50MB"
```

## Severity Classification

- **CRITICAL**: Application will crash or fail to start without this dependency.
- **HIGH**: Core functionality broken (e.g., can't process PDFs, can't use OpenCV).
- **MEDIUM**: Some features degraded (e.g., missing font support, no color management).
- **LOW**: Nice-to-have for debugging/operations (e.g., curl for health checks).

---

## Verification Checklist

Run these commands against the built container to verify dependencies:

```bash
# OpenCV check
docker run --rm IMAGE python -c "import cv2; print(cv2.__version__)"

# pdf2image check
docker run --rm IMAGE which pdftoppm
docker run --rm IMAGE python -c "from pdf2image import convert_from_path; print('OK')"

# Pillow format support check
docker run --rm IMAGE python -c "from PIL import features; print(features.check('jpg'), features.check('png'))"

# libmagic check
docker run --rm IMAGE python -c "import magic; print(magic.Magic().from_buffer(b'test'))"

# Font check
docker run --rm IMAGE fc-list | head -5

# Locale check
docker run --rm IMAGE python -c "import locale; print(locale.getlocale())"

# SSL check
docker run --rm IMAGE python -c "import ssl; print(ssl.OPENSSL_VERSION)"

# SQLite check
docker run --rm IMAGE python -c "import sqlite3; print(sqlite3.sqlite_version)"
```

---

## Comprehensive Dockerfile Template

Based on audit findings, here's a complete template for this stack:

```dockerfile
# ============================================
# Build Stage
# ============================================
FROM python:3.11-slim-bookworm AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ============================================
# Runtime Stage
# ============================================
FROM python:3.11-slim-bookworm AS runtime

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # OpenCV dependencies
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    # pdf2image dependencies
    poppler-utils \
    # Pillow dependencies
    libjpeg62-turbo \
    libpng16-16 \
    libtiff6 \
    libwebp7 \
    zlib1g \
    libfreetype6 \
    liblcms2-2 \
    # libmagic
    libmagic1 \
    # Fonts
    fonts-liberation \
    fonts-dejavu-core \
    fontconfig \
    # SSL/TLS
    ca-certificates \
    # Process management
    tini \
    # Health checks
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -f -v

# Set locale
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Install Python packages
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Set up application
WORKDIR /app
COPY --chown=appuser:appuser . .

# Create writable directories
RUN mkdir -p /app/checkpoints /app/uploads /app/temp \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1

# Use tini as init
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Vibe Score Rubric (Container Readiness 1-10)

Rate container readiness based on dependency completeness:

- **9-10**: All dependencies present, multi-stage build, security hardened, runs as non-root.
- **7-8**: Core dependencies present, minor security improvements needed.
- **5-6**: Some runtime errors expected, missing libraries for specific features.
- **3-4**: Container will fail on common operations (PDF processing, image handling).
- **<3**: Container fails to start or crashes on import.

---

## Include:
- The score
- Brief justification (2-5 bullets)
- Prioritized list of missing dependencies (highest impact first)

## Final Section: Summary & Action Plan (Mandatory)

1) **Fix Now** (container won't work without these)
2) **Fix Soon** (features will fail without these)
3) **Improvement** (security/performance enhancements)

## Also include:
- Total estimated image size increase from all dependencies
- Commands to verify each dependency is working
- Docker build test command:
  ```bash
  docker build -t app:test . && \
  docker run --rm app:test python -c "
  import cv2
  from pdf2image import convert_from_path
  from PIL import Image
  import magic
  import sqlite3
  print('All dependencies OK')
  "
  ```
