FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PORT=8080


ENV PYTHONPATH=/app/backend

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc g++ build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY backend /app/backend
COPY frontend /app/frontend

# move frontend into static
RUN mkdir -p /app/backend/app/static && \
    cp -r /app/frontend/* /app/backend/app/static/

EXPOSE 8080


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]