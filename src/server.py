import grpc
import time
import threading
from concurrent import futures
from generated import heartrate_service_pb2_grpc as pb2_grpc
from src.handlers.heartrate_servicer import HeartRateMonitorServicer
from src.utils.logger import get_logger
from src.utils import metrics  # Import the metrics module
from grpc_reflection.v1alpha import reflection

def serve():
    logger = get_logger(__name__)
    # Start the prometheus metrics server
    metrics_port = 8080
    metrics_thread = threading.Thread(target=metrics.start_metrics_server, args=(metrics_port,), daemon=True)
    metrics_thread.start()
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_HeartRateMonitorServicer_to_server(HeartRateMonitorServicer(), server)
    server.add_insecure_port('[::]:50051')

    logger.info("Starting gRPC server on port 50051")
    server.start()
    try:
        while True:
            time.sleep(86400)  # Sleep for 24 hours
    except KeyboardInterrupt:
        logger.info("Stopping gRPC server")
        server.stop(0)
        
if __name__ == '__main__':
    serve()
