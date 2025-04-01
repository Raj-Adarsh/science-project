#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

PROTO_DIR="proto"  # Directory containing .proto files
OUTPUT_DIR="generated"  # Directory to store generated Python files
PROTO_FILE="heartrate_service.proto"

echo "Compiling .proto files..."
mkdir -p $OUTPUT_DIR

python -m grpc_tools.protoc \
    -I$PROTO_DIR \
    --python_out=$OUTPUT_DIR \
    --grpc_python_out=$OUTPUT_DIR \
    $PROTO_DIR/$PROTO_FILE

echo "Protobuf and gRPC Python files generated successfully!"
