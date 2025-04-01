import threading
import grpc
import time
# from proto import heartrate_service_pb2 as pb2
# from proto import heartrate_service_pb2_grpc as pb2_grpc

from generated import heartrate_service_pb2_grpc as pb2_grpc
from generated import heartrate_service_pb2 as pb2

def stream_client(client_id, num_messages=20):
    channel = grpc.insecure_channel('localhost:50051')
    stub = pb2_grpc.HeartRateMonitorStub(channel)
    def request_generator():
        for i in range(num_messages):
            # For diversity, vary BPM slightly per client/message
            yield pb2.HeartRateRequest(
                bpm=70 + client_id,
                timestamp=int(time.time()) + i * 5,
                metadata={}
            )
            time.sleep(0.1)  # simulate a slight delay between messages
    print(f"Client {client_id} starting stream...")
    try:
        for response in stub.StreamHeartRate(request_generator()):
            print(f"Client {client_id} received: {response}")
    except grpc.RpcError as e:
        print(f"Client {client_id} encountered RPC error: {e}")
    channel.close()

threads = []
for client_id in range(10):  # 10 concurrent streaming clients
    t = threading.Thread(target=stream_client, args=(client_id,))
    t.start()
    threads.append(t)

for t in threads:
    t.join()
