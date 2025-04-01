import unittest
from unittest.mock import MagicMock, patch
import time
import grpc
from generated import heartrate_service_pb2 as pb2
from src.handlers.get_heartrate_status import GetHeartRateStatusHandler

class TestGetHeartrateStatusHandler(unittest.TestCase):

    def setUp(self):
        """Set up mocks and the handler instance before each test."""
        self.mock_store = MagicMock()
        self.mock_logger = MagicMock()
        self.mock_context = MagicMock()

        with patch('src.handlers.get_heartrate_status.data_store.get_data_store', return_value=self.mock_store):
            with patch('src.handlers.get_heartrate_status.logger.get_logger', return_value=self.mock_logger):
                self.handler = GetHeartRateStatusHandler()
        self.handler.store = self.mock_store


    def test_get_status_success_no_alert(self):
        """Test successful status retrieval with no active alert."""
        request = pb2.StatusRequest(recent_count=5)
        ts = int(time.time())

        # Mock data store responses
        mock_measurements = [
            pb2.HeartRateMeasurement(bpm=70, timestamp=ts - 10),
            pb2.HeartRateMeasurement(bpm=75, timestamp=ts - 5),
            pb2.HeartRateMeasurement(bpm=80, timestamp=ts),
        ]
        mock_stats = pb2.HeartRateStats(average_bpm=75.0, min_bpm=70, max_bpm=80)
        mock_alert_status = (False, pb2.AlertType.NONE)

        self.mock_store.get_recent_measurements.return_value = mock_measurements
        self.mock_store.get_stats.return_value = mock_stats
        self.mock_store.get_alert_status.return_value = (False, pb2.AlertType.NONE)

        # Call the handler
        response = self.handler.get_status(request, self.mock_context)

        # Assertions
        self.assertEqual(len(response.recent_measurements), 3)
        self.assertEqual(response.recent_measurements[0].bpm, 70)
        self.assertEqual(response.recent_measurements[-1].bpm, 80)
        self.assertFalse(response.alert_active)
        self.assertEqual(response.alert_type, pb2.AlertType.NONE)
        self.assertEqual(response.stats.average_bpm, 75.0)
        self.assertEqual(response.stats.min_bpm, 70)
        self.assertEqual(response.stats.max_bpm, 80)

        # Verify mocks
        self.mock_store.get_recent_measurements.assert_called_once_with(5)
        self.mock_store.get_stats.assert_called_once()
        self.mock_store.get_alert_status.assert_called_once()

    def test_get_status_success_with_alert(self):
        """Test successful status retrieval with an active alert."""
        request = pb2.StatusRequest(recent_count=3)
        ts = int(time.time())

        # Mock data store responses indicating a high alert
        mock_measurements = [pb2.HeartRateMeasurement(bpm=160, timestamp=ts)]
        mock_stats = pb2.HeartRateStats(average_bpm=160.0, min_bpm=160, max_bpm=160)
        mock_alert_status = (True, pb2.AlertType.HIGH_HEART_RATE)

        self.mock_store.get_recent_measurements.return_value = mock_measurements
        self.mock_store.get_stats.return_value = mock_stats
        self.mock_store.get_alert_status.return_value = mock_alert_status

        response = self.handler.get_status(request, self.mock_context)

        # Assertions
        self.assertEqual(response.alert_type, pb2.AlertType.HIGH_HEART_RATE)
        self.assertEqual(len(response.recent_measurements), 1)
        self.assertEqual(response.stats.max_bpm, 160)

        # Verify mocks
        self.mock_store.get_recent_measurements.assert_called_once_with(3)
        self.mock_store.get_stats.assert_called_once()
        self.mock_store.get_alert_status.assert_called_once()

    def test_get_status_no_data(self):
        """Test status retrieval when the data store is empty."""
        request = pb2.StatusRequest(recent_count=10)

        # Mock empty/default responses from store
        self.mock_store.get_recent_measurements.return_value = []
        self.mock_store.get_stats.return_value = pb2.HeartRateStats(average_bpm=0.0, min_bpm=0, max_bpm=0)
        self.mock_store.get_alert_status.return_value = (False, pb2.AlertType.NONE)

        response = self.handler.get_status(request, self.mock_context)

        # Assertions for empty state
        self.assertEqual(len(response.recent_measurements), 0)
        self.assertFalse(response.alert_active)
        self.assertEqual(response.alert_type, pb2.AlertType.NONE)
        self.assertEqual(response.stats.average_bpm, 0.0)
        self.assertEqual(response.stats.min_bpm, 0)
        self.assertEqual(response.stats.max_bpm, 0)

        # Verify mocks
        self.mock_store.get_recent_measurements.assert_called_once_with(10)
        self.mock_store.get_alert_status.assert_called_once()

    def test_get_status_exception_in_store(self):
        """Test handling of an exception raised by the data store."""
        request = pb2.StatusRequest(recent_count=5)

        # Configure a store method to raise an exception
        self.mock_store.get_recent_measurements.side_effect = Exception("Data store connection error")

        response = self.handler.get_status(request, self.mock_context)

        # Assertions for the default error response defined in the handler's except block
        self.assertEqual(len(response.recent_measurements), 0)
        self.assertFalse(response.alert_active)
        self.assertEqual(response.alert_type, pb2.AlertType.NONE)
        self.assertEqual(response.stats.average_bpm, 0.0)
        self.assertEqual(response.stats.min_bpm, 0)
        self.assertEqual(response.stats.max_bpm, 0)

        self.mock_store.get_recent_measurements.assert_called_once_with(5)
        self.mock_store.get_stats.assert_not_called()
        self.mock_store.get_alert_status.assert_not_called()
        self.mock_logger.error.assert_called_once()
        self.mock_context.set_details.assert_called_once()
        self.mock_context.set_code.assert_called_once_with(grpc.StatusCode.INTERNAL)

if __name__ == '__main__':
    unittest.main()
