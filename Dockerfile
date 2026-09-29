FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (for Tier 3 scraping)
RUN pip install playwright && playwright install --with-deps chromium

# Application code
COPY . .

# Create data directories
RUN mkdir -p /app/data /app/output

# Environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000 8501

# Default: run the API server
CMD ["python", "-m", "uvicorn", "scrybe.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
