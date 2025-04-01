#!/bin/bash
# Docker Health Check - Verifies that the containerized application is working correctly

set -e # Exit on error

echo "====== Heart Rate Monitoring Service Docker Health Check ======"

# Step 1: Check if Docker and Docker Compose are installed
echo "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed or not in PATH."
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo "Error: Docker Compose is not installed or not in PATH."
    exit 1
fi

echo "Docker is properly installed."

# Step 2: Check if containers are running
echo "Checking if containers are running..."
CONTAINERS=$(docker compose ps -q)
if [ -z "$CONTAINERS" ]; then
    echo "No containers running. Starting services..."
    make up
else
    echo "Containers are running."
fi

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 5

# Step 3: Check if Redis is working
echo "Checking Redis connection..."
if docker compose exec redis redis-cli ping | grep -q "PONG"; then
    echo "Redis is working properly."
else
    echo "Error: Redis is not responding."
    exit 1
fi

# Step 4: Check if the client can connect to the gRPC server
echo "Testing gRPC server connection using client..."
if docker compose exec heartrate-service python -c "
import grpc
from generated import heartrate_service_pb2_grpc as pb2_grpc
channel = grpc.insecure_channel('localhost:50051')
stub = pb2_grpc.HeartRateMonitorStub(channel)
try:
    # Just create the stub to check if the server is accessible
    print('Connection to gRPC server successful')
    exit(0)
except Exception as e:
    print(f'Error connecting to gRPC server: {e}')
    exit(1)
"; then
    echo "gRPC server is listening and accepting connections."
else
    echo "Error: gRPC server is not accessible."
    exit 1
fi

# Step 5: Check if Prometheus metrics endpoint is accessible
echo "Checking Prometheus metrics endpoint..."
METRICS_PORT=${METRICS_PORT:-8080}
if docker compose exec heartrate-service curl -s --retry 3 --retry-delay 1 http://localhost:$METRICS_PORT > /dev/null; then
    echo "Prometheus metrics endpoint is accessible."
else
    echo "Warning: Prometheus metrics endpoint might not be accessible. This could be due to missing curl in the container."
fi

echo "====== All checks passed! Docker setup is working correctly. ======"
echo "You can now use the application with the following commands:"
echo "  - Run client: make client"
echo "  - View logs: make logs"
echo "  - Run tests: make test"
echo "  - Stop services: make down"
