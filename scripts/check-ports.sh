#!/bin/bash

# Simple port checking script for the heart rate monitoring service
# Usage: ./check-ports.sh [grpc_port] [metrics_port] [redis_port]

# Set default ports if not provided
GRPC_PORT=${1:-50051}
METRICS_PORT=${2:-8080}
REDIS_PORT=${3:-6379}

echo "Checking required ports:"
echo "  - gRPC: $GRPC_PORT"
echo "  - Metrics: $METRICS_PORT"
echo "  - Redis: $REDIS_PORT"

# Flag to track if any port is in use
PORTS_IN_USE=false

# Check gRPC port
if lsof -i :"$GRPC_PORT" > /dev/null 2>&1; then
    echo "❌ Port $GRPC_PORT (gRPC) is already in use"
    PORTS_IN_USE=true
else
    echo "✅ Port $GRPC_PORT (gRPC) is available"
fi

# Check metrics port
if lsof -i :"$METRICS_PORT" > /dev/null 2>&1; then
    echo "❌ Port $METRICS_PORT (Metrics) is already in use"
    PORTS_IN_USE=true
else
    echo "✅ Port $METRICS_PORT (Metrics) is available"
fi

# Check Redis port
if lsof -i :"$REDIS_PORT" > /dev/null 2>&1; then
    echo "❌ Port $REDIS_PORT (Redis) is already in use"
    PORTS_IN_USE=true
else
    echo "✅ Port $REDIS_PORT (Redis) is available"
fi

# Return status
if [ "$PORTS_IN_USE" = "true" ]; then
    echo "Some required ports are in use."
    exit 1
else
    echo "All required ports are available."
    exit 0
fi
