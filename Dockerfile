# ── Stage 1: Build the React Frontend ──────────────────────────
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --production=false
COPY frontend/ .
RUN npm run build

# ── Stage 2: Python Runtime ───────────────────────────────────
FROM python:3.11-slim AS runtime
WORKDIR /app

# System dependencies for playwright & lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Tier 3 scraping)
RUN pip install playwright && playwright install --with-deps chromium

# Application code
COPY scrybe/ ./scrybe/
COPY config/ ./config/
COPY cli.py .
COPY .env.example .

# Copy pre-built frontend dist from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create data & output directories
RUN mkdir -p /app/data /app/output

# Environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default: run the unified API + SPA server
CMD ["python", "-m", "uvicorn", "scrybe.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
