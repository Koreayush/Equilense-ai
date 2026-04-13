#!/bin/bash

echo "🚀 Starting EquiLens AI Demo..."

echo "📂 Moving to docker folder..."
cd infra/docker || exit

echo "🧹 Cleaning old containers..."
docker-compose down -v

echo "🔨 Building and starting services..."
docker-compose up --build -d

echo "⏳ Waiting for services to boot..."
sleep 10

echo "🌐 Opening application..."

# Windows Git Bash fallback
start http://localhost:3000 2>/dev/null || \
xdg-open http://localhost:3000 2>/dev/null || \
open http://localhost:3000 2>/dev/null || \
echo "👉 Open manually: http://localhost:3000"

echo "✅ Demo is live!"
echo "📊 API Docs: http://localhost:8000/docs"