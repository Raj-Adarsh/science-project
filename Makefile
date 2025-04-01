.PHONY: build up down restart logs client test test-unit test-integration test-performance validate clean pre-check

# Default port values
GRPC_PORT ?= 50051
METRICS_PORT ?= 8080
REDIS_PORT ?= 6379

# Alternate port values
ALT_GRPC_PORT = 50052
ALT_METRICS_PORT = 8081
ALT_REDIS_PORT = 6380

# Build the Docker images
build:
	docker compose up --build

# Pre-check for port conflicts with interactive resolution
pre-check:
	@echo "Checking ports before starting services..."
	@ports_in_use=false; \
	if lsof -i :$(GRPC_PORT) > /dev/null 2>&1; then \
		echo "❌ Port $(GRPC_PORT) (gRPC) is in use"; \
		ports_in_use=true; \
	else \
		echo "✅ Port $(GRPC_PORT) (gRPC) is available"; \
	fi; \
	if lsof -i :$(METRICS_PORT) > /dev/null 2>&1; then \
		echo "❌ Port $(METRICS_PORT) (Metrics) is in use"; \
		ports_in_use=true; \
	else \
		echo "✅ Port $(METRICS_PORT) (Metrics) is available"; \
	fi; \
	if lsof -i :$(REDIS_PORT) > /dev/null 2>&1; then \
		echo "❌ Port $(REDIS_PORT) (Redis) is in use"; \
		ports_in_use=true; \
	else \
		echo "✅ Port $(REDIS_PORT) (Redis) is available"; \
	fi; \
	\
	if [ "$$ports_in_use" = "true" ]; then \
		echo ""; \
		echo "Port conflict detected. How would you like to proceed?"; \
		echo "  1. Attempt to free the ports (kill processes)"; \
		echo "  2. Use alternative ports ($(ALT_GRPC_PORT), $(ALT_METRICS_PORT), $(ALT_REDIS_PORT))"; \
		echo "  3. Cancel operation"; \
		read -p "Enter your choice [1-3]: " choice; \
		\
		if [ "$$choice" = "1" ]; then \
			echo "Attempting to free ports..."; \
			lsof -ti :$(GRPC_PORT) | xargs kill -9 2>/dev/null || echo "No process to kill on port $(GRPC_PORT)"; \
			lsof -ti :$(METRICS_PORT) | xargs kill -9 2>/dev/null || echo "No process to kill on port $(METRICS_PORT)"; \
			lsof -ti :$(REDIS_PORT) | xargs kill -9 2>/dev/null || echo "No process to kill on port $(REDIS_PORT)"; \
			echo "Ports should now be available."; \
		elif [ "$$choice" = "2" ]; then \
			echo "Using alternative ports..."; \
			export GRPC_PORT=$(ALT_GRPC_PORT); \
			export METRICS_PORT=$(ALT_METRICS_PORT); \
			export REDIS_PORT=$(ALT_REDIS_PORT); \
			echo "Services will start on ports: GRPC=$(ALT_GRPC_PORT), Metrics=$(ALT_METRICS_PORT), Redis=$(ALT_REDIS_PORT)"; \
		else \
			echo "Operation cancelled."; \
			exit 1; \
		fi; \
	fi

# Start services with appropriate ports
up: build pre-check
	@echo "Starting services..."
	@# Use whatever ports were decided in pre-check
	GRPC_PORT=$(GRPC_PORT) METRICS_PORT=$(METRICS_PORT) REDIS_PORT=$(REDIS_PORT) docker compose up -d
	@echo "✅ Services started on ports:"
	@echo "  - gRPC server: $(GRPC_PORT)"
	@echo "  - Metrics: $(METRICS_PORT)"
	@echo "  - Redis: $(REDIS_PORT)"
	@echo "You can run 'make client' to interact with the service"
	@echo "You can run 'make logs' to view logs"

# Stop and remove services
down:
	docker compose down

# Restart services
restart: down up

# View logs for all services
logs:
	docker compose logs --follow

# View logs for a specific service
logs-service:
	docker compose logs --follow heartrate-service

logs-redis:
	docker compose logs --follow redis

# Run the client
client:
	docker compose exec heartrate-service python -m src.client

# Run tests
test:
	@echo "Running all tests..."
	@echo "Step 1: Running unit tests..."
	@$(MAKE) test-unit
	@echo "Step 2: Running integration tests..."
	@$(MAKE) test-integration
	@echo "Step 3: Running performance tests..."
	@$(MAKE) test-performance
	@echo "✅ All tests passed successfully!"

# Run specific test suites
test-unit:
	@echo "Running unit tests..."
	@docker compose exec heartrate-service python -m unittest discover -s tests/unit -p 'test_*.py' || { echo "❌ Unit tests failed!"; exit 1; }
	@echo "✅ Unit tests passed successfully!"

test-integration:
	@echo "Running integration tests..."
	@docker compose exec heartrate-service python -m unittest tests.integration.test_heartrate_service_integration || { echo "❌ Integration tests failed!"; exit 1; }
	@echo "✅ Integration tests passed successfully!"

test-performance:
	@echo "Running performance tests..."
	@docker compose exec heartrate-service python -m tests.perf.benchmark || { echo "❌ Performance benchmark tests failed!"; exit 1; }
	@docker compose exec heartrate-service python -m tests.perf.stream_load_test || { echo "❌ Performance stream tests failed!"; exit 1; }
	@docker compose exec heartrate-service python -m tests.perf.ghz_load_test || { echo "❌ Performance ghz load tests failed!"; exit 1; }
	@echo "✅ Performance tests passed successfully!"

# Validate Docker setup
validate: build
	@echo "Running validation workflow..."
	@./scripts/validate.sh || exit 1
	@echo "✅ Validation passed!"

# Clean up resources
clean:
	docker compose down -v
	docker system prune -f
