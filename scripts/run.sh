# #!/bin/bash
set -e

if [ "$1" == "server" ]; then
    echo "Starting gRPC server..."
    PYTHONPATH=generated python3 -m src.server
elif [ "$1" == "client" ]; then
    echo "Starting gRPC client..."
    PYTHONPATH=generated python3 -m src.client
else
    echo "Usage: ./scripts/run.sh [server|client]"
    exit 1
fi
