from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Counter for the number of RPCs handled
rpc_counter = Counter(
    'grpc_server_handled_total',
    'Total number of RPCs handled by the server',
    ['grpc_method', 'grpc_type', 'grpc_status_code']
)

# Histogram for RPC latency
rpc_latency_histogram = Histogram(
    'grpc_server_handling_seconds',
    'Histogram of RPC processing time',
    ['grpc_method', 'grpc_type'],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, float("inf"))
)

# Counter for heart rate alerts
alert_counter = Counter(
    'heartrate_alerts_total',
    'Total number of heart rate alerts triggered',
    ['alert_type']
)

# Gauge for current number of active streaming connections
active_streams_gauge = Gauge(
    'grpc_server_active_streams',
    'Number of active gRPC streaming connections'
)

def start_metrics_server(port=8080):
    """Starts the Prometheus metrics HTTP server."""
    start_http_server(port)
    print(f"Prometheus metrics server started on port {port}")

def increment_active_streams():
    active_streams_gauge.inc()

def decrement_active_streams():
    active_streams_gauge.dec()

def record_rpc_handled(method, rpc_type, status_code):
    rpc_counter.labels(grpc_method=method, grpc_type=rpc_type, grpc_status_code=status_code).inc()

def observe_rpc_latency(method, rpc_type, duration_seconds):
    rpc_latency_histogram.labels(grpc_method=method, grpc_type=rpc_type).observe(duration_seconds)

def record_alert(alert_type):
    alert_counter.labels(alert_type=alert_type).inc()
