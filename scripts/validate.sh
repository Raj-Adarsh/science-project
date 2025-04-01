#!/bin/bash

# Validation script for the heart rate monitoring service
# Runs a complete validation workflow including:
# - Checking Docker environment
# - Building fresh images
# - Starting services
# - Running health checks
# - Running unit and integration tests

# Exit on any error
set -e

# Setup ports (use alternate ports to avoid conflicts)
GRPC_PORT=${GRPC_PORT:-50052}
METRICS_PORT=${METRICS_PORT:-8081}
REDIS_PORT=${REDIS_PORT:-6380}

echo "===== Running Docker Validation ====="

# Step 1: Check environment
echo "Step 1: Checking Docker environment..."
if ! command -v docker > /dev/null || ! command -v docker compose > /dev/null; then
    echo "Error: Docker and Docker Compose are required."
    exit 1
fi

# Step 2: Check ports
echo "Step 2: Checking ports..."
./scripts/check-ports.sh $GRPC_PORT $METRICS_PORT $REDIS_PORT || {
    echo "Error: Port conflict detected. Please use different ports."
    exit 1
}

# Step 3: Clean up existing containers
echo "Step 3: Cleaning up existing containers..."
docker compose down -v 2>/dev/null || true

# Step 4: Build Docker images
echo "Step 4: Building fresh Docker images..."
docker compose build

# Step 5: Start services
echo "Step 5: Starting services..."
GRPC_PORT=$GRPC_PORT METRICS_PORT=$METRICS_PORT REDIS_PORT=$REDIS_PORT docker compose up -d

# Step 6: Wait for services to initialize
echo "Step 6: Waiting for services to initialize..."
sleep 5

# Step 7: Run health check
echo "Step 7: Verifying service health..."
if [ -f ./docker-health-check.sh ]; then
    if ! GRPC_PORT=$GRPC_PORT METRICS_PORT=$METRICS_PORT REDIS_PORT=$REDIS_PORT ./docker-health-check.sh; then
        echo "❌ Health check failed! Services are not running correctly."
        echo "Showing service logs:"
        docker compose logs
        GRPC_PORT=$GRPC_PORT METRICS_PORT=$METRICS_PORT REDIS_PORT=$REDIS_PORT docker compose down
        exit 1
    fi
else
    echo "Warning: Health check script not found, skipping health verification."
fi

# Step 8: Run unit tests
echo "Step 8: Running unit tests..."
if ! docker compose exec -T heartrate-service python -m unittest discover tests/unit; then
    echo "❌ Unit tests failed!"
    echo "Showing service logs:"
    docker compose logs heartrate-service
    GRPC_PORT=$GRPC_PORT METRICS_PORT=$METRICS_PORT REDIS_PORT=$REDIS_PORT docker compose down
    exit 1
fi

# Step 9: Run integration tests
echo "Step 9: Running integration tests..."
if ! docker compose exec -T heartrate-service python -m unittest discover tests/integration; then
    echo "❌ Integration tests failed!"
    echo "Showing service logs:"
    docker compose logs heartrate-service
    GRPC_PORT=$GRPC_PORT METRICS_PORT=$METRICS_PORT REDIS_PORT=$REDIS_PORT docker compose down
    exit 1
fi

# Step 10: Cleanup
echo "Step 10: Cleaning up resources..."
GRPC_PORT=$GRPC_PORT METRICS_PORT=$METRICS_PORT REDIS_PORT=$REDIS_PORT docker compose down

echo "===== All validations passed! ✅ ====="
echo "Your Docker setup is working correctly."
exit 0
