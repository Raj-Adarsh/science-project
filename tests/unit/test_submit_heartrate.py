import unittest
from unittest.mock import MagicMock, patch
import time

# from proto import heartrate_service_pb2 as pb2
from generated import heartrate_service_pb2 as pb2

from backend_service.handlers.submit_heartrate import SubmitHeartrateHandler

class TestSubmitHeartrateHandler(unittest.TestCase):
    def setUp(self):
        """Set up mocks and the handler instance before each test."""
        self.mock_store = MagicMock()
        self.mock_logger = MagicMock()
        self.mock_context = MagicMock()

        with patch('backend_service.handlers.submit_heartrate.data_store.get_data_store', return_value=self.mock_store):
            with patch('backend_service.handlers.submit_heartrate.logger.get_logger', return_value=self.mock_logger):
                self.handler = SubmitHeartrateHandler()

    def test_handle_success_normal_bpm(self):
        """Test successful handling of a normal BPM reading."""
        bpm = 75
        timestamp = int(time.time())
        request = pb2.HeartRateRequest(bpm=bpm, timestamp=timestamp)

        self.mock_store.save_measurement.return_value = "mock_measurement_id_123"
        response = self.handler.handle(request, self.mock_context)

        # Assertions
        self.assertTrue(response.success)
        self.assertEqual(response.error, "")
        self.assertFalse(response.alert_triggered)
        self.assertEqual(response.alert_type, pb2.AlertType.NONE) # Or pb2.AlertType.Value("NONE")

        # Verify mocks were called as expected
        self.mock_store.save_measurement.assert_called_once_with(bpm, timestamp)
        self.mock_logger.info.assert_called()
        
    def test_handle_success_low_alert(self):
        """Test successful handling triggering a low BPM alert."""
        bpm = 48
        timestamp = int(time.time())
        request = pb2.HeartRateRequest(bpm=bpm, timestamp=timestamp)
        self.mock_store.save_measurement.return_value = "mock_measurement_id_456"
        response = self.handler.handle(request, self.mock_context)

        self.assertTrue(response.success)
        self.assertEqual(response.error, "")
        self.assertTrue(response.alert_triggered)
        self.assertEqual(response.alert_type, pb2.AlertType.LOW_HEART_RATE)
        self.mock_store.save_measurement.assert_called_once_with(bpm, timestamp)

    def test_handle_success_high_alert(self):
        """Test successful handling triggering a high BPM alert."""
        bpm = 155
        timestamp = int(time.time())
        request = pb2.HeartRateRequest(bpm=bpm, timestamp=timestamp)
        self.mock_store.save_measurement.return_value = "mock_measurement_id_789"
        response = self.handler.handle(request, self.mock_context)

        self.assertTrue(response.success)
        self.assertEqual(response.error, "")
        self.assertTrue(response.alert_triggered)
        self.assertEqual(response.alert_type, pb2.AlertType.HIGH_HEART_RATE)
        self.mock_store.save_measurement.assert_called_once_with(bpm, timestamp)

    def test_handle_failure_out_of_range_low(self):
        """Test rejection of an out-of-range low BPM."""
        bpm = 30
        timestamp = int(time.time())
        request = pb2.HeartRateRequest(bpm=bpm, timestamp=timestamp)
        response = self.handler.handle(request, self.mock_context)

        self.assertFalse(response.success)
        self.assertEqual(response.error, "Heart rate out of typical range for an adult")
        self.assertFalse(response.alert_triggered)
        self.assertEqual(response.alert_type, pb2.AlertType.NONE)

        # Check if the invalid input was rejected
        self.mock_store.save_measurement.assert_not_called()
        self.mock_logger.warning.assert_called_once()

    def test_handle_failure_out_of_range_high(self):
        """Test rejection of an out-of-range high BPM."""
        bpm = 190
        timestamp = int(time.time())
        request = pb2.HeartRateRequest(bpm=bpm, timestamp=timestamp)
        response = self.handler.handle(request, self.mock_context)

        self.assertFalse(response.success)
        self.assertEqual(response.error, "Heart rate out of typical range for an adult")
        self.assertFalse(response.alert_triggered)
        self.assertEqual(response.alert_type, pb2.AlertType.NONE)
        
        self.mock_store.save_measurement.assert_not_called()
        self.mock_logger.warning.assert_called_once()

    def test_handle_exception_in_store(self):
        """Test handling of an unexpected exception during processing."""
        bpm = 70
        timestamp = int(time.time())
        request = pb2.HeartRateRequest(bpm=bpm, timestamp=timestamp)
        self.mock_store.save_measurement.side_effect = Exception("Datastore intialisation failed")
        response = self.handler.handle(request, self.mock_context)

        # Assertions for the exception handling path
        self.assertFalse(response.success)
        self.assertEqual(response.error, "Internal server error processing measurement")
        self.assertFalse(response.alert_triggered)
        self.assertEqual(response.alert_type, pb2.AlertType.NONE)
        self.mock_store.save_measurement.assert_called_once_with(bpm, timestamp)
        self.mock_logger.error.assert_called_once()

if __name__ == '__main__':
    unittest.main()
