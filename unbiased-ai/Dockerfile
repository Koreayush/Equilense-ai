# -------- Phase 1: Build Frontend --------
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci --silent

COPY frontend/ .
RUN npm run build


# -------- Phase 2: Final Image --------
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    curl \
    && rm -rf /var/lib/apt/lists/*

# -------- Backend --------
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# -------- Frontend --------
# Remove default nginx configs and pages
RUN rm -rf /usr/share/nginx/html/* && \
    rm -f /etc/nginx/sites-enabled/default && \
    rm -f /etc/nginx/conf.d/default.conf

# Copy ONLY build output correctly
COPY --from=frontend-build /app/frontend/dist /usr/share/nginx/html

# Copy nginx config
COPY frontend/nginx.conf /etc/nginx/conf.d/combined.conf

# -------- Storage --------
RUN mkdir -p /app/storage/reports/dataset /app/storage/reports/model
RUN chmod -R 755 /app/storage

# -------- Startup Script --------
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# -------- Health Check --------
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# -------- Start both services --------
EXPOSE 80

CMD ["/app/start.sh"]