import unittest
from unittest.mock import MagicMock, patch
import time
import grpc

# from proto import heartrate_service_pb2 as pb2
from generated import heartrate_service_pb2 as pb2

from backend_service.handlers.calculate_exercise_zones import CalculateExerciseZonesHandler

class TestCalculateExerciseZonesHandler(unittest.TestCase):

    def setUp(self):
        """Set up mocks and the handler instance before each test."""
        self.mock_logger = MagicMock()
        self.mock_context = MagicMock()

        # Patch logger used by the handler
        with patch('backend_service.handlers.calculate_exercise_zones.logger.get_logger', return_value=self.mock_logger):
            self.handler = CalculateExerciseZonesHandler()
            self.handler.interval_seconds = 5 # Make interval explicit for tests

    def test_calculate_success(self):
        """Test successful calculation of exercise zones."""
        age = 30 # Max HR = 190
        base_ts = int(time.time())
        measurements = [
            # Zone 1: < 114 (50-60% = 95-114)
            pb2.HeartRateMeasurement(bpm=90, timestamp=base_ts),
            pb2.HeartRateMeasurement(bpm=100, timestamp=base_ts + 5),
            # Zone 2: 114-133 (60-70% = 114-133)
            pb2.HeartRateMeasurement(bpm=120, timestamp=base_ts + 10),
            pb2.HeartRateMeasurement(bpm=130, timestamp=base_ts + 15),
            # Zone 3: >= 133 (70-80% = 133-152, >80% = >152)
            pb2.HeartRateMeasurement(bpm=140, timestamp=base_ts + 20),
            pb2.HeartRateMeasurement(bpm=160, timestamp=base_ts + 25) 
        ]
        # Expected: Z1=10s(1), Z2=5s(2), Z3=0s(2), Total=15s(5 intervals), Avg=(90+..+160)/6=110.00
        request = pb2.ExerciseZoneRequest(age=age, measurements=measurements)

        response = self.handler.calculate(request, self.mock_context)

        self.assertEqual(response.zone1_time, 10)
        self.assertEqual(response.zone2_time, 5)
        self.assertEqual(response.zone3_time, 0)
        self.assertEqual(response.total_duration, 15)
        self.assertAlmostEqual(response.average_heart_rate, 110.0, places=2)

    def test_calculate_invalid_age_zero(self):
        """Test calculation attempt with age zero."""
        request = pb2.ExerciseZoneRequest(age=0, measurements=[pb2.HeartRateMeasurement(bpm=100, timestamp=1)])
        result = self.handler.calculate(request, self.mock_context)

        self.mock_context.set_code.assert_called_once_with(grpc.StatusCode.INVALID_ARGUMENT)
        self.mock_context.set_details.assert_called_once_with("Age must be a positive integer")
        self.assertIsNone(result)

    def test_calculate_invalid_age_negative(self):
        """Test calculation attempt with negative age."""
        request = pb2.ExerciseZoneRequest(age=-5, measurements=[pb2.HeartRateMeasurement(bpm=100, timestamp=1)])
        result  = self.handler.calculate(request, self.mock_context)
        
        self.mock_context.set_code.assert_called_once_with(grpc.StatusCode.INVALID_ARGUMENT)
        self.mock_context.set_details.assert_called_once_with("Age must be a positive integer")
        # Check that None was returned
        self.assertIsNone(result)   

    def test_calculate_no_measurements(self):
        """Test calculation attempt with an empty measurements list."""
        request = pb2.ExerciseZoneRequest(age=40, measurements=[])
        result = self.handler.calculate(request, self.mock_context)
        
        self.mock_context.set_code.assert_called_once_with(grpc.StatusCode.INVALID_ARGUMENT)
        self.mock_context.set_details.assert_called_once_with("No measurements provided")
        self.assertIsNone(result)

    def test_calculate_single_measurement(self):
        """Test calculation with only one measurement."""
        age = 25 # Max HR = 195
        # Zone 1: 97.5-117, Zone 2: 117-136.5, Zone 3: >= 136.5
        measurements = [pb2.HeartRateMeasurement(bpm=120, timestamp=int(time.time()))] # Zone 2
        request = pb2.ExerciseZoneRequest(age=age, measurements=measurements)

        response = self.handler.calculate(request, self.mock_context)

        self.assertEqual(response.zone1_time, 0)
        self.assertEqual(response.zone2_time, 0) # No intervals calculated for single point
        self.assertEqual(response.zone3_time, 0)
        self.assertEqual(response.total_duration, 0) # No duration between points
        self.assertAlmostEqual(response.average_heart_rate, 120.0, places=2)

    def test_calculate_two_measurements(self):
        """Test calculation with two measurements defining one interval."""
        age = 50 # Max HR = 170
        # Zone 1: 85-102, Zone 2: 102-119, Zone 3: >= 119
        ts = int(time.time())
        measurements = [
            pb2.HeartRateMeasurement(bpm=100, timestamp=ts),       # Zone 1
            pb2.HeartRateMeasurement(bpm=110, timestamp=ts + 5)    # Zone 2 (Avg 105 -> Zone 2)
        ]
        request = pb2.ExerciseZoneRequest(age=age, measurements=measurements)

        response = self.handler.calculate(request, self.mock_context)

        self.assertEqual(response.zone1_time, 0)
        self.assertEqual(response.zone2_time, 5) # The interval (avg 105) falls in Zone 2
        self.assertEqual(response.zone3_time, 0)
        self.assertEqual(response.total_duration, 5) # 1 interval * 5 seconds
        self.assertAlmostEqual(response.average_heart_rate, 105.0, places=2)

if __name__ == '__main__':
    unittest.main()
