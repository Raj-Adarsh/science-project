#!/bin/bash

PROTO_DIR="."
OUT_DIR="."
PROTO_FILE="heartrate_service.proto"

python -m grpc_tools.protoc \
    -I. \
    --python_out=. \
    --grpc_python_out=. \
    proto/$PROTO_FILE
