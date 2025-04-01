import subprocess
import os
import sys

def run_ghz_load_test():
    # Get gRPC port from environment variable or use default
    grpc_port = os.environ.get('GRPC_PORT', '50051')

    # Determine the proto file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '../..'))
    proto_path = os.path.join(project_root, 'proto/heartrate_service.proto')

    # Make sure proto file exists
    if not os.path.exists(proto_path):
        print(f"Error: Proto file not found at {proto_path}")
        sys.exit(1)

    print(f"Running ghz load test against gRPC server on port {grpc_port}")

    cmd = [
        "ghz",
        "--insecure",
        "--proto", proto_path,
        "--call", "heartrate.HeartRateMonitor.SubmitHeartRate",
        "-n", "10000",
        "-c", "10",
        "-d", '{"bpm": 75, "timestamp": 1625247600}',
        f"localhost:{grpc_port}"
    ]

    print(f"Executing command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("Load test completed successfully")
        print("STDOUT:")
        print(result.stdout)
    else:
        print("Load test failed")
        print("STDERR:")
        print(result.stderr)
        print("STDOUT:")
        print(result.stdout)

if __name__ == "__main__":
    run_ghz_load_test()
