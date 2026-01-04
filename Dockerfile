# SAM3 Drawing Zone Segmenter
# Multi-stage build for optimized image size

# Stage 1: Builder
FROM python:3.10-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for better caching
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Stage 2: Runtime with CUDA support
FROM nvidia/cuda:12.1-runtime-ubuntu22.04

# Install Python and runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    python3.10-venv \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.10 /usr/bin/python

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/dist-packages

# Copy application code
COPY src/ ./src/
COPY exemplars/ ./exemplars/
COPY pyproject.toml ./

# Install the package in editable mode (for correct imports)
RUN pip install --no-cache-dir -e .

# Create directories for models and data
RUN mkdir -p /app/models /app/exemplars

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SAM3_MODEL_PATH=/app/models/sam3.pt \
    SAM3_EXEMPLARS_DIR=/app/exemplars \
    SAM3_HOST=0.0.0.0 \
    SAM3_PORT=8001

# Expose the API port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run the server
CMD ["python", "-m", "uvicorn", "src.sam3_segmenter.main:app", "--host", "0.0.0.0", "--port", "8001"]
