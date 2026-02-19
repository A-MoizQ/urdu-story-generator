# ──────────────────────────────────────────────────────────────
# Dockerfile — Urdu Story Generation Microservice
# Multi-stage build: slim final image, proto compilation in build stage
#
# Runs two servers in one container:
#   - gRPC  on port 50051 (for direct gRPC clients / local dev)
#   - HTTP  on port 10000 (SSE gateway for Render LB + Vercel frontend)
# ──────────────────────────────────────────────────────────────

# ========================  BUILD STAGE  ========================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build-time dependencies only
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Copy proto source and compile stubs
COPY proto/story.proto proto/
COPY proto/__init__.py proto/
COPY scripts/generate_proto.sh scripts/

RUN pip install --no-cache-dir grpcio-tools==1.68.1 protobuf==5.29.2 \
    && bash scripts/generate_proto.sh

# ========================  RUNTIME STAGE  ========================
FROM python:3.12-slim

# Non-root user for security
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --create-home appuser

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code (models/ excluded via .dockerignore — those come from builder)
COPY . /app/backend/

# Copy generated proto stubs from builder (overwrite source-only proto dir)
COPY --from=builder /build/proto/ /app/backend/proto/

# Model files (bpe_tokenizer.json + trigram_model.db) are already present
# under /app/backend/models/ from the COPY above.
# trigram_model.db is committed to git and used directly — no conversion needed.

# Ensure the package is importable from /app
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Default env vars (can be overridden at runtime via render.yaml)
ENV GRPC_HOST=0.0.0.0
ENV GRPC_PORT=50051
# Render sets PORT=10000 automatically for web services
ENV HTTP_PORT=10000
ENV MODEL_DIR=/app/backend/models
ENV TOKENIZER_PATH=/app/backend/models/bpe_tokenizer.json
ENV TRIGRAM_MODEL_PATH=/app/backend/models/trigram_model.json
ENV TRIGRAM_DB_PATH=/app/backend/models/trigram_model.db

# Expose both ports
EXPOSE 50051
EXPOSE 10000

# Switch to non-root user
USER appuser

# Health-check: hit the HTTP gateway's /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:10000/health')" || exit 1

# Start both servers via the unified entrypoint
CMD ["python", "-m", "backend.entrypoint"]
