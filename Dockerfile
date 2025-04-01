# Stage 1: Build dependencies and generate protobuf files
FROM python:3.9-slim AS builder

WORKDIR /build

# Install build dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy proto files and generate protobuf code
COPY proto/ proto/
RUN mkdir -p generated && \
    python -m grpc_tools.protoc \
    -Iproto \
    --python_out=generated \
    --grpc_python_out=generated \
    proto/heartrate_service.proto && \
    touch generated/__init__.py

# Stage 2: Install ghz for testing
FROM python:3.9-slim AS ghz-installer

WORKDIR /tmp

# Install necessary tools for downloading ghz
RUN apt-get update && \
    apt-get install -y curl tar && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Download and install ghz
RUN echo "Downloading ghz..." && \
    curl -fSL -o ghz.tar.gz "https://github.com/bojand/ghz/releases/download/v0.120.0/ghz-linux-x86_64.tar.gz" && \
    echo "Extracting ghz..." && \
    tar -xzf ghz.tar.gz && \
    echo "Moving ghz..." && \
    chmod +x ghz && \
    rm ghz.tar.gz

# Stage 3: Final production image
FROM python:3.9-slim

WORKDIR /app

# Copy only runtime dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    apt-get update && \
    apt-get install -y --no-install-recommends tini && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy generated protobuf files from builder stage
COPY --from=builder /build/generated/ /app/generated/

# Copy proto directory for ghz testing
COPY --from=builder /build/proto/ /app/proto/

# Copy ghz from ghz-installer stage
COPY --from=ghz-installer /tmp/ghz /usr/local/bin/ghz
RUN chmod +x /usr/local/bin/ghz

# Copy application code
COPY src/ /app/src/
COPY tests/ /app/tests/

# Create logs directory
RUN mkdir -p logs

# Set Python path to include generated files
ENV PYTHONPATH=/app/generated:$PYTHONPATH

# Expose ports for gRPC server and Prometheus metrics
EXPOSE 50051 8080

# Use tini as init to handle signals properly
ENTRYPOINT ["/usr/bin/tini", "--"]

# Run the server by default
CMD ["python", "-m", "src.server"]
