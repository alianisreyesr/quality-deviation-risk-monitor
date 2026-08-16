#!/bin/bash
# Quality Deviation Risk Monitor - Pipeline Initialization Script
# This script sets up the development environment and loads synthetic data

set -e

echo "🚀 Initializing Quality Deviation Risk Monitor..."

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
fi

# Validate synthetic data file exists
if [ ! -f data/deviations.csv ]; then
    echo "❌ Synthetic data file not found: data/deviations.csv"
    exit 1
fi

echo "✅ Prerequisites validated"

# Build and start services
echo "🔨 Building Docker images..."
if command -v docker-compose &> /dev/null; then
    docker-compose up --build -d
else
    docker compose up --build -d
fi

echo "⏳ Waiting for services to be healthy..."
sleep 10

# Health check
echo "🏥 Running health checks..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is healthy"
else
    echo "⚠️  API health check failed. Services may still be starting."
fi

echo ""
echo "🎉 Pipeline initialization complete!"
echo ""
echo "📊 Access points:"
echo "   - API:       http://localhost:8000"
echo "   - Frontend:  http://localhost:3000"
echo "   - Health:    http://localhost:8000/health"
echo ""
echo "📋 Available endpoints:"
echo "   - GET /health     - System health status"
echo "   - GET /deviations - List all deviations with risk scores"
echo "   - GET /summary    - Risk summary statistics"
echo ""
echo "🛑 To stop services, run:"
echo "   docker-compose down"
echo "   # or: docker compose down"
echo ""
