#!/bin/bash
# PlotTwist Production Health Check Script
# Task 011: Deployment Infrastructure

set -e

# Configuration
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-plottwist}"
LOG_FILE="/var/log/plottwist/health-check.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Health check functions
check_database() {
    log "Checking PostgreSQL database connection..."
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Database connection: OK${NC}"
        return 0
    else
        echo -e "${RED}✗ Database connection: FAILED${NC}"
        return 1
    fi
}

check_backend() {
    log "Checking backend API health..."
    local response=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/v1/health" || echo "000")
    
    if [ "$response" -eq 200 ]; then
        echo -e "${GREEN}✓ Backend API: OK (HTTP $response)${NC}"
        return 0
    else
        echo -e "${RED}✗ Backend API: FAILED (HTTP $response)${NC}"
        return 1
    fi
}

check_frontend() {
    log "Checking frontend application..."
    local response=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL" || echo "000")
    
    if [ "$response" -eq 200 ]; then
        echo -e "${GREEN}✓ Frontend: OK (HTTP $response)${NC}"
        return 0
    else
        echo -e "${RED}✗ Frontend: FAILED (HTTP $response)${NC}"
        return 1
    fi
}

check_backend_endpoints() {
    log "Checking critical backend endpoints..."
    local endpoints=(
        "/api/v1/health"
        "/api/v1/books/"
        "/api/v1/auth/register"
        "/api/v1/auth/login"
    )
    
    local failed=0
    for endpoint in "${endpoints[@]}"; do
        local url="$BACKEND_URL$endpoint"
        local response=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")
        
        if [ "$response" -eq 200 ] || [ "$response" -eq 422 ] || [ "$response" -eq 401 ]; then
            echo -e "${GREEN}✓ $endpoint: OK (HTTP $response)${NC}"
        else
            echo -e "${RED}✗ $endpoint: FAILED (HTTP $response)${NC}"
            ((failed++))
        fi
    done
    
    return $failed
}

check_services() {
    log "Checking system services..."
    local services=("plottwist-backend" "plottwist-frontend" "nginx" "postgresql")
    local failed=0
    
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service"; then
            echo -e "${GREEN}✓ $service: Running${NC}"
        else
            echo -e "${RED}✗ $service: Not running${NC}"
            ((failed++))
        fi
    done
    
    return $failed
}

check_disk_space() {
    log "Checking disk space..."
    local usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$usage" -lt 80 ]; then
        echo -e "${GREEN}✓ Disk space: OK (${usage}% used)${NC}"
        return 0
    elif [ "$usage" -lt 90 ]; then
        echo -e "${YELLOW}⚠ Disk space: Warning (${usage}% used)${NC}"
        return 1
    else
        echo -e "${RED}✗ Disk space: Critical (${usage}% used)${NC}"
        return 2
    fi
}

check_memory() {
    log "Checking memory usage..."
    local mem_usage=$(free | awk 'NR==2{printf "%.1f", $3*100/$2}')
    local mem_int=${mem_usage%.*}
    
    if [ "$mem_int" -lt 80 ]; then
        echo -e "${GREEN}✓ Memory usage: OK (${mem_usage}% used)${NC}"
        return 0
    elif [ "$mem_int" -lt 90 ]; then
        echo -e "${YELLOW}⚠ Memory usage: Warning (${mem_usage}% used)${NC}"
        return 1
    else
        echo -e "${RED}✗ Memory usage: Critical (${mem_usage}% used)${NC}"
        return 2
    fi
}

check_ssl_certificates() {
    log "Checking SSL certificates..."
    local domains=("$FRONTEND_DOMAIN" "$BACKEND_DOMAIN")
    local failed=0
    
    for domain in "${domains[@]}"; do
        if [ -f "/etc/letsencrypt/live/$domain/cert.pem" ]; then
            local expiry=$(openssl x509 -enddate -noout -in "/etc/letsencrypt/live/$domain/cert.pem" | cut -d= -f2)
            local expiry_timestamp=$(date -d "$expiry" +%s)
            local current_timestamp=$(date +%s)
            local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
            
            if [ "$days_until_expiry" -gt 30 ]; then
                echo -e "${GREEN}✓ SSL certificate for $domain: OK ($days_until_expiry days until expiry)${NC}"
            elif [ "$days_until_expiry" -gt 7 ]; then
                echo -e "${YELLOW}⚠ SSL certificate for $domain: Warning ($days_until_expiry days until expiry)${NC}"
                ((failed++))
            else
                echo -e "${RED}✗ SSL certificate for $domain: Critical ($days_until_expiry days until expiry)${NC}"
                ((failed++))
            fi
        else
            echo -e "${RED}✗ SSL certificate for $domain: Not found${NC}"
            ((failed++))
        fi
    done
    
    return $failed
}

# Performance check
check_response_times() {
    log "Checking response times..."
    local endpoints=(
        "$FRONTEND_URL"
        "$BACKEND_URL/api/v1/health"
        "$BACKEND_URL/api/v1/books/"
    )
    
    for endpoint in "${endpoints[@]}"; do
        local response_time=$(curl -s -o /dev/null -w "%{time_total}" "$endpoint" || echo "999")
        local time_ms=$(echo "$response_time * 1000" | bc)
        
        if (( $(echo "$response_time < 1.0" | bc -l) )); then
            echo -e "${GREEN}✓ $endpoint: Fast (${time_ms}ms)${NC}"
        elif (( $(echo "$response_time < 3.0" | bc -l) )); then
            echo -e "${YELLOW}⚠ $endpoint: Slow (${time_ms}ms)${NC}"
        else
            echo -e "${RED}✗ $endpoint: Very slow (${time_ms}ms)${NC}"
        fi
    done
}

# Main health check
main() {
    log "Starting PlotTwist health check..."
    echo "=========================================="
    echo "PlotTwist Production Health Check"
    echo "=========================================="
    
    local total_checks=0
    local failed_checks=0
    
    # Run all checks
    checks=(
        "check_database"
        "check_backend"
        "check_frontend"
        "check_backend_endpoints"
        "check_services"
        "check_disk_space"
        "check_memory"
        "check_ssl_certificates"
        "check_response_times"
    )
    
    for check in "${checks[@]}"; do
        echo ""
        $check || ((failed_checks++))
        ((total_checks++))
    done
    
    echo ""
    echo "=========================================="
    if [ $failed_checks -eq 0 ]; then
        echo -e "${GREEN}✓ All checks passed! System is healthy.${NC}"
        log "Health check completed: All systems operational"
        exit 0
    else
        echo -e "${RED}✗ $failed_checks out of $total_checks checks failed.${NC}"
        log "Health check completed: $failed_checks issues found"
        exit 1
    fi
}

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Run health check
main "$@" 