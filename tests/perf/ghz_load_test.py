import subprocess

def run_ghz_load_test():
    cmd = [
        "ghz",
        "--insecure",
        "--proto", "proto/heartrate_service.proto",
        "--call", "heartrate.HeartRateMonitor.SubmitHeartRate",
        "-n", "10000",
        "-c", "10",
        "-d", '{"bpm": 75, "timestamp": 1625247600}',
        "localhost:50051"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:")
    print(result.stdout)
    print("STDERR:")
    print(result.stderr)

if __name__ == "__main__":
    run_ghz_load_test()
