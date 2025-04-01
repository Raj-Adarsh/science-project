import grpc
from proto import heartrate_service_pb2_grpc as pb2_grpc
from proto import heartrate_service_pb2 as pb2
import time

def run_submit_heartrate():
    channel = grpc.insecure_channel('localhost:50051')
    stub = pb2_grpc.HeartRateMonitorStub(channel)
    request = pb2.HeartRateRequest(bpm=75, timestamp=int(time.time()), metadata={})
    response = stub.SubmitHeartRate(request)
    print("SubmitHeartRate response:", response)

def run_stream_heartrate():
    channel = grpc.insecure_channel('localhost:50051')
    stub = pb2_grpc.HeartRateMonitorStub(channel)

    # Get current time to base timestamps off
    base_timestamp = int(time.time())

    requests = [
        # Normal readings
        pb2.HeartRateRequest(bpm=72, timestamp=base_timestamp, metadata={}),
        pb2.HeartRateRequest(bpm=80, timestamp=base_timestamp + 5, metadata={}),
        # Low BPM Alert
        pb2.HeartRateRequest(bpm=48, timestamp=base_timestamp + 10, metadata={}),
        # Out-of-range (Low) - Should be rejected
        pb2.HeartRateRequest(bpm=35, timestamp=base_timestamp + 15, metadata={}),
        # Normal reading again
        pb2.HeartRateRequest(bpm=90, timestamp=base_timestamp + 20, metadata={}),
         # High BPM Alert
        pb2.HeartRateRequest(bpm=155, timestamp=base_timestamp + 25, metadata={}),
        # Out-of-range (High) - Should be rejected
        pb2.HeartRateRequest(bpm=190, timestamp=base_timestamp + 30, metadata={}),
        # Another normal reading
        pb2.HeartRateRequest(bpm=78, timestamp=base_timestamp + 35, metadata={})
    ]

    print("--- Sending stream requests ---")
    responses = stub.StreamHeartRate(iter(requests))
    try:
        for i, resp in enumerate(responses):
            print(f"StreamHeartRate response [{i+1}]:", resp)
    except grpc.RpcError as e:
         print(f"Error during stream: {e.code()} - {e.details()}")
    print("--- Stream finished ---")


def run_get_heartrate_status():
    channel = grpc.insecure_channel('localhost:50051')
    stub = pb2_grpc.HeartRateMonitorStub(channel)
    request = pb2.StatusRequest(recent_count=5)
    response = stub.GetHeartRateStatus(request)
    print("GetHeartRateStatus response:", response)

def run_calculate_exercise_zones():
    channel = grpc.insecure_channel('localhost:50051')
    stub = pb2_grpc.HeartRateMonitorStub(channel)

    # Use more realistic timestamps and include alerts based on stream data
    base_timestamp = int(time.time()) - 60 # Start 60 seconds ago
    measurement1 = pb2.HeartRateMeasurement(bpm=70, timestamp=base_timestamp, triggered_alert=False)
    measurement2 = pb2.HeartRateMeasurement(bpm=48, timestamp=base_timestamp + 10, triggered_alert=True) # Low alert
    measurement3 = pb2.HeartRateMeasurement(bpm=90, timestamp=base_timestamp + 20, triggered_alert=False)
    measurement4 = pb2.HeartRateMeasurement(bpm=155, timestamp=base_timestamp + 25, triggered_alert=True) # High alert
    measurement5 = pb2.HeartRateMeasurement(bpm=78, timestamp=base_timestamp + 35, triggered_alert=False)

    request = pb2.ExerciseZoneRequest(age=30, measurements=[measurement1, measurement2, measurement3, measurement4, measurement5])
    response = stub.CalculateExerciseZones(request)
    print("CalculateExerciseZones response:", response)

if __name__ == '__main__':
    print("=== Running SubmitHeartRate ===")
    run_submit_heartrate()
    print("\n=== Running StreamHeartRate ===")
    run_stream_heartrate()
    # Add a small delay to allow stream processing/saving if needed
    time.sleep(1)
    print("\n=== Running GetHeartRateStatus ===")
    run_get_heartrate_status()
    print("\n=== Running CalculateExerciseZones ===")
    run_calculate_exercise_zones()
