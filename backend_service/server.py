import grpc
import time

from concurrent import futures
from proto import heartrate_service_pb2_grpc as pb2_grpc

from backend_service.handlers.heartrate_servicer import HeartRateMonitorServicer
from backend_service.utils.logger import get_logger

def serve():
    logger = get_logger(__name__)
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
