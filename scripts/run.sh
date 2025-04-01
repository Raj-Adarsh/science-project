#Automatic process
# #!/bin/bash
# # Exit immediately if a command exits with a non-zero status
# set -e

# echo "Starting gRPC server in the background..."
# PYTHONPATH=generated python3 -m backend_service.server &

# # Capture the PID of the background process (server)
# SERVER_PID=$!

# # Wait a few seconds to ensure the server is up and running (optional)
# sleep 5

# echo "Starting gRPC client..."
# PYTHONPATH=generated python3 -m backend_service.client

# # Kill the server process after the client finishes (optional)
# echo "Stopping gRPC server..."
# kill $SERVER_PID


#Controlled process - Let's run the server and client separately
#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

if [ "$1" == "server" ]; then
    echo "Starting gRPC server..."
    PYTHONPATH=generated python3 -m backend_service.server
elif [ "$1" == "client" ]; then
    echo "Starting gRPC client..."
    PYTHONPATH=generated python3 -m backend_service.client
else
    echo "Usage: ./scripts/run.sh [server|client]"
    exit 1
fi
