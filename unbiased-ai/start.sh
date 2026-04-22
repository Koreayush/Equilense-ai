#!/bin/bash

# Start the Python backend in the background
echo "Starting Backend (Uvicorn)..."
uvicorn app.main:app --host 127.0.0.1 --port 8000 &

# Wait for backend to be ready
echo "Waiting for backend..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:8000/health > /dev/null; then
        echo "Backend is up!"
        break
    fi
    sleep 1
done

# Start Nginx in the foreground
echo "Starting Nginx..."
nginx -g "daemon off;"
