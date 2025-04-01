#!/bin/bash
# test.sh - Run unit, integration, and performance tests

# Exit immediately if a command exits with a non-zero status
set -e

# Add the 'generated' directory to PYTHONPATH so that tests can find the generated files
export PYTHONPATH=generated:$PYTHONPATH

# Run all tests discovered in the 'tests' directory
echo "Running all tests discovered in the 'tests' directory..."
python -m unittest discover tests
echo "-------------------------------------------------"

# Run all unit tests (pattern: test_*.py) in tests/unit
echo "Running all unit tests in tests/unit..."
python -m unittest discover -s tests/unit -p 'test_*.py'
echo "-------------------------------------------------"

# Run a specific integration test file
echo "Running specific integration test: tests.integration.test_heartrate_service_integration..."
python -m unittest tests.integration.test_heartrate_service_integration
echo "-------------------------------------------------"

# Run benchmark tests (assuming tests/perf/benchmark.py exists)
echo "Running benchmark tests..."
python -m tests.perf.benchmark
echo "-------------------------------------------------"

# Run stream load test (assuming tests/perf/stream_load_test.py exists)
echo "Running stream load tests..."
python -m tests.perf.stream_load_test
echo "-------------------------------------------------"

# Run ghz load test (assuming tests/perf/ghz_load_test.py exists)
echo "Running ghz load tests..."
python -m tests.perf.ghz_load_test
echo "-------------------------------------------------"

echo "All tests completed."
