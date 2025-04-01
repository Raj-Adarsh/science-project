import grpc
import timeit
import time
# from proto import heartrate_service_pb2 as pb2
# from proto import heartrate_service_pb2_grpc as pb2_grpc

from generated import heartrate_service_pb2_grpc as pb2_grpc
from generated import heartrate_service_pb2 as pb2

def benchmark_submit_unary(num_calls=100):
    channel = grpc.insecure_channel('localhost:50051')
    stub = pb2_grpc.HeartRateMonitorStub(channel)
    # Create a reusable request
    request = pb2.HeartRateRequest(bpm=75, timestamp=int(time.time()), metadata={})
    def call_submit():
        stub.SubmitHeartRate(request)
    total_time = timeit.timeit(call_submit, number=num_calls)
    avg_time_ms = (total_time / num_calls) * 1000
    print(f"Performed {num_calls} unary calls in {total_time:.3f} seconds.")
    print(f"Average response time per call: {avg_time_ms:.2f} ms")
    channel.close()

if __name__ == '__main__':
    benchmark_submit_unary()
