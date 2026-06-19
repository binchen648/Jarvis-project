FROM python:3.12-slim AS builder

WORKDIR /app

# Install Node.js for Tailwind CSS build
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Build Tailwind CSS
COPY package.json tailwind.config.js ./
COPY static/css/tailwind-input.css static/css/
RUN npm install && npm run build

# ── Production stage ─────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN addgroup --system app && adduser --system --ingroup app app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy application code and built CSS
COPY --chown=app:app . .
COPY --from=builder /app/static/css/tailwind.css /app/static/css/tailwind.css

# Create logs directory
RUN mkdir -p /app/logs && chown app:app /app/logs

USER app

EXPOSE 8000

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]
