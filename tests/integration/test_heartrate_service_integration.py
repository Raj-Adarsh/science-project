import unittest
import grpc
import time
from concurrent import futures
import threading

# from proto import heartrate_service_pb2 as pb2
# from proto import heartrate_service_pb2_grpc as pb2_grpc
from generated import heartrate_service_pb2_grpc as pb2_grpc
from generated import heartrate_service_pb2 as pb2
from backend_service.server import serve
from backend_service.handlers.heartrate_servicer import HeartRateMonitorServicer
from backend_service.utils.data_store import get_data_store

# Configuration
TEST_PORT = 50052
TEST_ADDRESS = f'localhost:{TEST_PORT}'

class TestHeartRateServiceIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Start the gRPC server in a background thread once for all tests."""
        cls.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        pb2_grpc.add_HeartRateMonitorServicer_to_server(HeartRateMonitorServicer(), cls.server)
        cls.server.add_insecure_port(f'[::]:{TEST_PORT}')

        # Start the server in a separate thread
        cls.server_thread = threading.Thread(target=cls.server.start, daemon=True)
        cls.server_thread.start()
        # Give the server a moment to start up
        time.sleep(1)
        print(f"Test server started on port {TEST_PORT}")

    @classmethod
    def tearDownClass(cls):
        """Stop the gRPC server after all tests."""
        print("Stopping test server...")
        cls.server.stop(grace=1).wait() # Graceful shutdown
        print("Test server stopped.")

    def setUp(self):
        """Create a client stub before each test."""
        self.channel = grpc.insecure_channel(TEST_ADDRESS)
        self.stub = pb2_grpc.HeartRateMonitorStub(self.channel)
        get_data_store().clear_all_measurements()

    def tearDown(self):
        """Close the client channel after each test."""
        self.channel.close()

    def test_submit_heartrate_integration(self):
        """Test the SubmitHeartRate RPC via integration."""
        timestamp = int(time.time())
        request = pb2.HeartRateRequest(bpm=85, timestamp=timestamp)
        response = self.stub.SubmitHeartRate(request)

        self.assertTrue(response.success)
        self.assertEqual(response.error, "")
        self.assertFalse(response.alert_triggered)
        self.assertEqual(response.alert_type, pb2.AlertType.NONE)

        # Optional: Verify data was actually stored (requires access to data store)
        store = get_data_store()
        measurements = store.get_recent_measurements(1)
        self.assertEqual(len(measurements), 1)
        self.assertEqual(measurements[0].bpm, 85)

    def test_submit_heartrate_integration_invalid(self):
        """Test SubmitHeartRate RPC with invalid input."""
        timestamp = int(time.time())
        request = pb2.HeartRateRequest(bpm=20, timestamp=timestamp) # Invalid BPM
        response = self.stub.SubmitHeartRate(request)

        self.assertFalse(response.success)
        self.assertEqual(response.error, "Heart rate out of typical range for an adult")

    def test_stream_heartrate_integration(self):
        """Test the StreamHeartRate RPC via integration."""
        base_timestamp = int(time.time())
        requests_data = [
            (72, base_timestamp),       # Normal
            (48, base_timestamp + 5),   # Low Alert
            (35, base_timestamp + 10),  # Invalid
            (155, base_timestamp + 15), # High Alert
            (190, base_timestamp + 20), # Invalid
            (78, base_timestamp + 25)   # Normal
        ]
        requests = [pb2.HeartRateRequest(bpm=d[0], timestamp=d[1]) for d in requests_data]

        responses = list(self.stub.StreamHeartRate(iter(requests)))

        self.assertEqual(len(responses), len(requests_data))

        # Resp 1 (72)
        self.assertTrue(responses[0].success)
        self.assertFalse(responses[0].alert_triggered)
        # Resp 2 (48)
        self.assertTrue(responses[1].success)
        self.assertTrue(responses[1].alert_triggered)
        self.assertEqual(responses[1].alert_type, pb2.AlertType.LOW_HEART_RATE)
        # Resp 3 (35)
        self.assertFalse(responses[2].success)
        self.assertEqual(responses[2].error, "Heart rate out of typical range for an adult")
        # Resp 4 (155)
        self.assertTrue(responses[3].success)
        self.assertTrue(responses[3].alert_triggered)
        self.assertEqual(responses[3].alert_type, pb2.AlertType.HIGH_HEART_RATE)
        # Resp 5 (190)
        self.assertFalse(responses[4].success)
        self.assertEqual(responses[4].error, "Heart rate out of typical range for an adult")
        # Resp 6 (78)
        self.assertTrue(responses[5].success)
        self.assertFalse(responses[5].alert_triggered)

    def test_get_heartrate_status_integration(self):
        """Test the GetHeartRateStatus RPC after submitting data."""
        # Submit some data first
        ts1 = int(time.time()) - 10
        ts2 = int(time.time()) - 5
        self.stub.SubmitHeartRate(pb2.HeartRateRequest(bpm=60, timestamp=ts1))
        self.stub.SubmitHeartRate(pb2.HeartRateRequest(bpm=160, timestamp=ts2)) # High alert

        request = pb2.StatusRequest(recent_count=5)
        response = self.stub.GetHeartRateStatus(request)

        self.assertTrue(response.alert_active) # Because 160 is > 150
        self.assertEqual(response.alert_type, pb2.AlertType.HIGH_HEART_RATE)
        self.assertGreaterEqual(len(response.recent_measurements), 2)
        found_60 = any(m.bpm == 60 and m.timestamp == ts1 for m in response.recent_measurements)
        found_160 = any(m.bpm == 160 and m.timestamp == ts2 for m in response.recent_measurements)
        self.assertTrue(found_60)
        self.assertTrue(found_160)
        self.assertGreater(response.stats.average_bpm, 0)
        self.assertEqual(response.stats.min_bpm, 60)
        self.assertEqual(response.stats.max_bpm, 160)


    def test_calculate_exercise_zones_integration(self):
        """Test the CalculateExerciseZones RPC via integration."""
        age = 35
        base_timestamp = int(time.time()) - 60 # Start 60 seconds ago
        # Assuming 5-second intervals for simplicity in calculation check
        measurements = [
            pb2.HeartRateMeasurement(bpm=70, timestamp=base_timestamp),      # Zone 1 (below 50% max)
            pb2.HeartRateMeasurement(bpm=100, timestamp=base_timestamp + 5), # Zone 1 (50-60% max)
            pb2.HeartRateMeasurement(bpm=120, timestamp=base_timestamp + 10),# Zone 2 (60-70% max)
            pb2.HeartRateMeasurement(bpm=140, timestamp=base_timestamp + 15),# Zone 3 (70-80% max)
            pb2.HeartRateMeasurement(bpm=160, timestamp=base_timestamp + 20),# Zone 3 (above 80% max)
            pb2.HeartRateMeasurement(bpm=115, timestamp=base_timestamp + 25) # Zone 2
        ]

        request = pb2.ExerciseZoneRequest(age=age, measurements=measurements)
        response = self.stub.CalculateExerciseZones(request)

        # Assertions based on interval calculation logic
        self.assertEqual(response.zone1_time, 5)
        self.assertEqual(response.zone2_time, 0)
        self.assertEqual(response.zone3_time, 5)
        # Total duration is sum of time in zones based on intervals
        self.assertEqual(response.total_duration, 10)
        # Average HeartRate remains the same calculation based on all points
        self.assertAlmostEqual(response.average_heart_rate, 107.5, places=2)

    def test_calculate_exercise_zones_integration_invalid_age(self):
        """Test CalculateExerciseZones RPC with invalid age."""
        request = pb2.ExerciseZoneRequest(age=0, measurements=[pb2.HeartRateMeasurement(bpm=80, timestamp=int(time.time()))])
        with self.assertRaises(grpc.RpcError) as cm:
            self.stub.CalculateExerciseZones(request)
        
        self.assertEqual(cm.exception.code(), grpc.StatusCode.INVALID_ARGUMENT)
        self.assertEqual(cm.exception.details(), "Age must be a positive integer")

    def test_calculate_exercise_zones_integration_no_measurements(self):
        """Test CalculateExerciseZones RPC with no measurements."""
        request = pb2.ExerciseZoneRequest(age=30, measurements=[])
        with self.assertRaises(grpc.RpcError) as cm:
            self.stub.CalculateExerciseZones(request)

        self.assertEqual(cm.exception.code(), grpc.StatusCode.INVALID_ARGUMENT)
        self.assertEqual(cm.exception.details(), "No measurements provided")

if __name__ == '__main__':
    unittest.main()
