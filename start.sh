#!/bin/bash
# PV Test Automation - Quick Start Script

set -e

echo "======================================"
echo "PV Test Report Automation System"
echo "Starting deployment..."
echo "======================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file. Please update it with your configuration."
    echo "   Edit .env and run this script again."
    exit 1
fi

echo "📦 Building Docker images..."
docker-compose build

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 15

echo ""
echo "🔍 Checking service status..."
docker-compose ps

echo ""
echo "======================================"
echo "✅ Deployment complete!"
echo "======================================"
echo ""
echo "🌐 Access the application:"
echo "   Web UI:    http://localhost"
echo "   API Docs:  http://localhost/api/docs"
echo ""
echo "🔐 Default Login:"
echo "   Username: admin"
echo "   Password: admin123"
echo "   ⚠️  CHANGE PASSWORD IMMEDIATELY!"
echo ""
echo "📊 Service Admin Panels:"
echo "   MinIO:     http://localhost:9001"
echo "   RabbitMQ:  http://localhost:15672"
echo ""
echo "📋 Useful commands:"
echo "   View logs:       docker-compose logs -f"
echo "   Stop services:   docker-compose down"
echo "   Restart:         docker-compose restart"
echo "   Health check:    python healthcheck.py"
echo ""
echo "📖 Documentation: See README.md and DEPLOYMENT.md"
echo "======================================"
