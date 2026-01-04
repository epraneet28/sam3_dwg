# Image Processing Security Audit Prompt (Production-Ready)

## Role
Act as a Security Engineer specializing in image processing vulnerabilities and memory safety. Perform a deep-dive Image Processing Security Audit on the provided codebase to identify exploitation vectors and resource exhaustion risks.

## Primary Goal
Identify where image processing code (Pillow, OpenCV, pdf2image) can be exploited through malicious inputs, cause denial of service through resource exhaustion, or leak sensitive information—and provide concrete fixes.

## Context
- This code was developed with AI assistance ("vibecoded") and may have overlooked image security best practices.
- Image processing is a high-risk attack surface due to complex parsers handling untrusted input.
- I need you to find vulnerabilities before deploying to production.

## Tech Stack
- Backend: Python 3.12 + FastAPI + Uvicorn
- Image Libraries: Pillow (PIL), OpenCV (cv2), pdf2image
- Document Processing: Docling
- File Storage: Local filesystem with checkpoint system
- Image Sources: PDF page renders, user uploads

## Security Targets
- Prevent remote code execution via malicious images
- Prevent denial of service via resource exhaustion
- Prevent information disclosure via error messages or timing
- Ensure safe handling of all image formats

## How to Provide Code
I will paste/upload the codebase files below. Analyze all provided files systematically.
If any critical context is missing (image processing configuration, file upload handlers, temporary file management), infer what you can from the code and explicitly list assumptions. If you cannot infer, state "Needs Confirmation" and tell me exactly which file/setting is needed.

## Environment & Assumptions (you must do this first)
1) Infer and list:
   - Pillow version and any security-relevant plugins (ImageMagick policy, etc.)
   - OpenCV version and whether GPU acceleration is enabled
   - pdf2image/poppler version and configuration
   - Maximum file sizes enforced at upload
   - Temporary file storage locations and cleanup policies
   - Image format restrictions (if any)
2) If you cannot infer any of the above, provide best-practice defaults and mark as "Needs Confirmation".

## Audit Requirements
Scan the files and generate a report identifying high-confidence instances of the risks below.
Also include "Suspicious Patterns" when something looks risky but requires confirmation (call out exactly what to verify).

---

## 1) Malicious Image Exploitation

### A) Image Parsing Vulnerabilities (CVE Surface)
- Check for outdated Pillow/OpenCV versions with known CVEs.
- Look for use of deprecated or vulnerable image formats (e.g., EPS without sandboxing).
- Flag missing `Image.MAX_IMAGE_PIXELS` limits.
- Suggested Fix: Update libraries, set pixel limits, disable risky formats.

### B) Decompression Bombs (Zip Bombs for Images)
- Identify missing checks for decompression ratio (small file -> huge pixels).
- Look for images that could expand to gigabytes in memory.
- Common vectors: PNG, TIFF, GIF with high compression ratios.
- Suggested Fix: Implement `Image.MAX_IMAGE_PIXELS`, check dimensions before full decode.

### C) SVG/XML Injection (if SVG processing exists)
- Flag any SVG parsing without sanitization.
- Look for XXE (XML External Entity) vulnerabilities.
- Check for JavaScript injection in SVG files.
- Suggested Fix: Use defusedxml, sanitize SVG, or reject SVG entirely.

### D) Polyglot Files
- Identify if file type detection relies only on extension.
- Look for files that could be valid images AND malicious scripts.
- Check for GIFAR, image/HTML polyglots.
- Suggested Fix: Validate magic bytes, re-encode images, strip metadata.

---

## 2) Resource Exhaustion (DoS Vectors)

### A) Image Dimension Limits (OOM Prevention)
- Find image operations without dimension checks.
- Look for missing limits on width, height, and total pixels.
- Flag operations that scale with image size (resize, filter, convolution).
- Suggested Fix: Enforce max dimensions (e.g., 10000x10000), check before processing.

### B) Memory Growth During Processing
- Identify operations that create multiple full-size copies in memory.
- Look for missing cleanup of intermediate images.
- Flag long-running operations without memory bounds.
- Suggested Fix: Process in tiles/chunks, explicit cleanup, memory limits.

### C) CPU Exhaustion via Complex Operations
- Find expensive operations (resize with high-quality filters, complex transforms).
- Look for operations inside loops without bounds.
- Flag missing timeouts on image processing.
- Suggested Fix: Use faster algorithms for untrusted input, add timeouts.

### D) Disk Exhaustion
- Identify temporary file creation without size limits.
- Look for missing cleanup of generated images.
- Flag unbounded caching of processed images.
- Suggested Fix: Temp file quotas, cleanup on error, cache size limits.

---

## 3) OpenCV-Specific Security Issues

### A) Buffer Overflow Risks
- OpenCV's C++ core can have buffer overflows with malformed images.
- Check for operations on images with unexpected channel counts.
- Flag missing validation of image dimensions before array operations.
- Suggested Fix: Validate image properties, use try/except around cv2 calls.

### B) Codec Vulnerabilities
- OpenCV uses system codecs (libjpeg, libpng, etc.) which may have vulnerabilities.
- Check for use of cv2.imdecode with untrusted data.
- Flag missing format restrictions.
- Suggested Fix: Restrict to safe formats, update system libraries, sandbox processing.

### C) Video Processing Risks (if applicable)
- cv2.VideoCapture can process malicious video files.
- Look for unbounded frame extraction.
- Flag missing duration/frame limits.
- Suggested Fix: Limit frame count, add timeouts, sandbox video processing.

---

## 4) Pillow-Specific Security Issues

### A) Image.MAX_IMAGE_PIXELS Configuration
- Default is 178,956,970 pixels (~13400x13400).
- Check if this is set appropriately for your use case.
- Flag if set to None (disabled).
- Suggested Fix: Set explicit limit based on expected document sizes.

### B) Format-Specific Risks
- EPS/PS: Can execute PostScript (RCE risk).
- PDF: Pillow's PDF support is limited; check if pdf2image is used instead.
- ICO: Can have multiple embedded images causing expansion.
- Suggested Fix: Explicitly whitelist safe formats, reject others.

### C) Pillow Plugin Security
- Check for custom image plugins or format handlers.
- Look for use of external decoders (ImageMagick, Ghostscript).
- Flag insecure ImageMagick policy.xml configuration.
- Suggested Fix: Audit plugins, secure ImageMagick policy, prefer pure-Pillow formats.

---

## 5) pdf2image/Poppler Security Issues

### A) Poppler CVE Exposure
- Poppler has had numerous CVEs for malformed PDFs.
- Check for version and whether security updates are applied.
- Flag if processing untrusted PDFs without sandboxing.
- Suggested Fix: Keep Poppler updated, sandbox PDF processing, use Docker isolation.

### B) Resource Limits for PDF Rendering
- PDFs can request extremely high DPI rendering.
- Check for unbounded page counts.
- Flag missing timeouts on PDF conversion.
- Suggested Fix: Cap DPI (e.g., 300), limit pages, add timeouts.

### C) Temporary File Security
- pdf2image creates temp files for each page.
- Check for secure temp directory usage.
- Flag if temp files are predictable or world-readable.
- Suggested Fix: Use tempfile.mkdtemp(), secure permissions, cleanup in finally.

---

## 6) Memory Cleanup & Lifecycle Management

### A) Explicit Memory Release
- Check for explicit `.close()` on Image objects.
- Look for `del` or context managers for large images.
- Flag long-lived image objects in global scope.
- Suggested Fix: Use context managers, explicit cleanup, weak references for caches.

### B) NumPy Array Cleanup (OpenCV)
- OpenCV returns NumPy arrays which can hold large memory.
- Check for explicit `del` of arrays after use.
- Look for arrays kept in lists/dicts without bounds.
- Suggested Fix: Explicit deletion, bounded collections, garbage collection hints.

### C) EXIF/Metadata Memory
- EXIF data can be surprisingly large (embedded thumbnails, GPS data).
- Check for metadata stripping before storage.
- Flag if original metadata is preserved unnecessarily.
- Suggested Fix: Strip metadata for privacy and memory, preserve only what's needed.

---

## 7) Secure Image Handling Patterns

### A) Re-encoding for Safety
- Best practice: Re-encode untrusted images to strip malicious content.
- Check if images are re-saved in a safe format before further processing.
- Flag direct use of untrusted bytes in multiple operations.
- Suggested Fix: Decode -> validate -> re-encode to safe format (PNG/JPEG).

### B) Sandboxed Processing
- Check for isolation of image processing (subprocess, container, seccomp).
- Look for privilege separation between upload and processing.
- Flag if image processing runs with full application privileges.
- Suggested Fix: Process images in isolated subprocess/container with limited permissions.

### C) Secure Defaults
- Check for explicit security configuration in image libraries.
- Look for commented-out security settings.
- Flag "TODO: add security" comments.
- Suggested Fix: Enable all security features, document configuration.

---

## Output Format (Mandatory)

For each issue found, provide:

```
[SEVERITY: CRITICAL | HIGH | MEDIUM | LOW]

Location: FileName : Line Number(s)
Risk Category: Exploitation | DoS | Information Disclosure | Configuration

The Problem:
- 2-4 sentences explaining the vulnerability and attack vector.
- Be specific about exploitation scenario: RCE, OOM, infinite loop, data leak, etc.

Attack Scenario:
- Describe how an attacker would exploit this.
- Include example payload characteristics if applicable.
- Confidence: High | Medium | Low

How to Verify:
- Concrete verification step (craft test image, memory profiling, fuzzing, CVE check).

The Fix:
- Provide the secure code snippet.
- Show before/after if useful.
- Include any configuration changes needed.

Trade-off Consideration:
- Note any performance impact, compatibility issues, or operational changes.
- If acceptable at small scale with trusted inputs, mark as MEDIUM with mitigation strategy.
```

## Severity Classification
- **CRITICAL**: Remote code execution, arbitrary file access, complete system compromise.
- **HIGH**: Denial of service, significant resource exhaustion, privilege escalation.
- **MEDIUM**: Information disclosure, limited DoS, requires specific conditions.
- **LOW**: Defense-in-depth issue, minor information leak, requires insider access.

---

## Security Score Rubric (1-10)

Rate overall security posture based on severity/quantity and systemic risks:
- **9-10**: Production-ready; comprehensive security controls in place.
- **7-8**: Minor gaps; needs 1-2 fixes before handling untrusted input.
- **5-6**: Moderate risk; significant hardening needed.
- **3-4**: High risk; multiple exploitable vulnerabilities.
- **<3**: Do not deploy; fundamental security issues.

---

## Include:
- The score
- Brief justification (2-5 bullets)
- A prioritized Top 3 fixes list (highest risk first)

## Final Section: Summary & Action Plan (Mandatory)
1) Fix Now (before production)
2) Fix Soon (next sprint)
3) Monitor (ongoing security maintenance)

## Also include:
- Estimated time to implement all Fix Now items (range is fine)
- Security infrastructure to add:
  - Dependency scanning (pip-audit, safety)
  - Image fuzzing test suite
  - Memory monitoring for image operations
  - Rate limiting on image processing endpoints
- Recommended test approach:
  - Craft malicious test images (dimension bombs, polyglots, CVE reproductions)
  - Memory profiling under adversarial load
  - Timeout verification for all image operations

## Quick Reference: Common Image Processing CVEs

| Library | CVE Examples | Impact |
|---------|--------------|--------|
| Pillow | CVE-2022-45199 (DoS), CVE-2023-44271 (DoS) | Memory exhaustion |
| OpenCV | CVE-2019-5064 (heap overflow), CVE-2017-12597 (buffer overflow) | RCE potential |
| Poppler | CVE-2022-38784 (integer overflow), numerous parsing bugs | RCE, DoS |
| libpng | CVE-2019-7317 (use-after-free) | RCE potential |
| libjpeg | CVE-2020-14152 (buffer overflow) | RCE potential |

## Pillow Security Configuration Template

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

## OpenCV Security Configuration Template

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
