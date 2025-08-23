#!/bin/bash

# PlotTwist Docker Startup Script
# This script ensures proper startup order and handles database initialization

set -e  # Exit on any error

echo "🚀 Starting PlotTwist Application..."
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

print_success "Docker is running ✓"

# Stop any existing containers
print_status "Stopping any existing PlotTwist containers..."
docker-compose -f docker-compose.fullstack.yml down --remove-orphans 2>/dev/null || true

# Clean up any existing volumes if requested
if [ "$1" = "--fresh" ]; then
    print_warning "Fresh start requested. Removing all data..."
    docker-compose -f docker-compose.fullstack.yml down -v 2>/dev/null || true
    docker volume prune -f 2>/dev/null || true
fi

# Build containers
print_status "Building Docker images..."
docker-compose -f docker-compose.fullstack.yml build --no-cache

# Start database first
print_status "Starting PostgreSQL database..."
docker-compose -f docker-compose.fullstack.yml up -d db

# Wait for database to be ready
print_status "Waiting for database to initialize... (this may take up to 60 seconds)"
timeout=60
counter=0

while [ $counter -lt $timeout ]; do
    if docker-compose -f docker-compose.fullstack.yml exec -T db pg_isready -U plottwist -d plottwist -h localhost > /dev/null 2>&1; then
        print_success "Database is ready! ✓"
        break
    fi
    
    if [ $counter -eq 30 ]; then
        print_warning "Database is taking longer than usual to start..."
    fi
    
    sleep 2
    counter=$((counter + 2))
    printf "."
done

if [ $counter -ge $timeout ]; then
    print_error "Database failed to start within $timeout seconds"
    echo ""
    echo "Checking database logs:"
    docker-compose -f docker-compose.fullstack.yml logs db
    exit 1
fi

echo ""
print_success "Database startup completed!"

# Start backend
print_status "Starting backend API..."
docker-compose -f docker-compose.fullstack.yml up -d backend

# Wait for backend to be ready
print_status "Waiting for backend to start..."
timeout=60
counter=0

while [ $counter -lt $timeout ]; do
    if curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        print_success "Backend is ready! ✓"
        break
    fi
    
    if [ $counter -eq 30 ]; then
        print_warning "Backend is taking longer than usual to start..."
    fi
    
    sleep 2
    counter=$((counter + 2))
    printf "."
done

if [ $counter -ge $timeout ]; then
    print_error "Backend failed to start within $timeout seconds"
    echo ""
    echo "Checking backend logs:"
    docker-compose -f docker-compose.fullstack.yml logs backend
    exit 1
fi

echo ""
print_success "Backend startup completed!"

# Seed database with sample data
print_status "Seeding database with sample books..."
if docker-compose -f docker-compose.fullstack.yml exec -T backend python -m app.utils.seeder; then
    print_success "Database seeded with 500+ books! ✓"
else
    print_warning "Database seeding failed, but application will still work"
fi

# Start frontend
print_status "Starting frontend application..."
docker-compose -f docker-compose.fullstack.yml up -d frontend

# Wait for frontend to be ready
print_status "Waiting for frontend to start..."
timeout=120  # Frontend takes longer to build
counter=0

while [ $counter -lt $timeout ]; do
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        print_success "Frontend is ready! ✓"
        break
    fi
    
    if [ $counter -eq 60 ]; then
        print_warning "Frontend is taking longer than usual to start (building React app)..."
    fi
    
    sleep 3
    counter=$((counter + 3))
    printf "."
done

echo ""
if [ $counter -ge $timeout ]; then
    print_warning "Frontend might still be starting. Check logs if needed."
else
    print_success "Frontend startup completed!"
fi

# Show final status
echo ""
echo "🎉 PlotTwist Application Started Successfully!"
echo "=============================================="
echo ""
echo "📱 Access Points:"
echo "  • Frontend: http://localhost:3000"
echo "  • Backend API: http://localhost:8000"
echo "  • API Documentation: http://localhost:8000/docs"
echo "  • Alternative Docs: http://localhost:8000/redoc"
echo ""
echo "🔍 Service Status:"
docker-compose -f docker-compose.fullstack.yml ps
echo ""
echo "📋 Quick Test Commands:"
echo "  • Health Check: curl http://localhost:8000/api/v1/health"
echo "  • List Books: curl http://localhost:8000/api/v1/books?limit=5"
echo ""
echo "🔧 Management Commands:"
echo "  • View logs: docker-compose -f docker-compose.fullstack.yml logs -f"
echo "  • Stop all: docker-compose -f docker-compose.fullstack.yml down"
echo "  • Restart: ./start-plottwist.sh"
echo "  • Fresh start: ./start-plottwist.sh --fresh"
echo ""
print_success "Enjoy testing PlotTwist! 🚀" 