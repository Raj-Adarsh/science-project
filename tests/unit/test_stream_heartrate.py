import unittest
from unittest.mock import MagicMock, patch, call
import time
from generated import heartrate_service_pb2 as pb2
from src.handlers.stream_heartrate import StreamHeartRateHandler

class TestStreamHeartrateHandler(unittest.TestCase):
    def setUp(self):
        """Set up mocks and the handler instance before each test."""
        self.mock_store = MagicMock()
        self.mock_logger = MagicMock()
        self.mock_context = MagicMock() # Mock gRPC context

        with patch('src.handlers.stream_heartrate.data_store.get_data_store', return_value=self.mock_store):
            with patch('src.handlers.stream_heartrate.logger.get_logger', return_value=self.mock_logger):
                self.handler = StreamHeartRateHandler()

    def test_stream_success_and_alerts(self):
        """Test processing a stream of valid requests, including alerts."""
        base_ts = int(time.time())
        mock_requests = [
            pb2.HeartRateRequest(bpm=70, timestamp=base_ts),      # Normal
            pb2.HeartRateRequest(bpm=45, timestamp=base_ts + 5),  # Low Alert
            pb2.HeartRateRequest(bpm=160, timestamp=base_ts + 10), # High Alert
            pb2.HeartRateRequest(bpm=80, timestamp=base_ts + 15), # Normal
        ]
        mock_iterator = iter(mock_requests)

        # Configure mock store to return different IDs
        self.mock_store.save_measurement.side_effect = ["id_70", "id_45", "id_160", "id_80"]
        responses = list(self.handler.stream(mock_iterator, self.mock_context))

        # Assertions
        self.assertEqual(len(responses), 4)
        # Resp 1 (70)
        self.assertTrue(responses[0].success)
        self.assertEqual(responses[0].error, "")
        self.assertFalse(responses[0].alert_triggered)
        self.assertEqual(responses[0].alert_type, pb2.AlertType.NONE)
        # Resp 2 (45)
        self.assertTrue(responses[1].success)
        self.assertEqual(responses[1].error, "")
        self.assertTrue(responses[1].alert_triggered)
        self.assertEqual(responses[1].alert_type, pb2.AlertType.LOW_HEART_RATE)
        # Resp 3 (160)
        self.assertTrue(responses[2].success)
        self.assertEqual(responses[2].error, "")
        self.assertTrue(responses[2].alert_triggered)
        self.assertEqual(responses[2].alert_type, pb2.AlertType.HIGH_HEART_RATE)
        # Resp 4 (80)
        self.assertTrue(responses[3].success)
        self.assertEqual(responses[3].error, "")
        self.assertFalse(responses[3].alert_triggered)
        self.assertEqual(responses[3].alert_type, pb2.AlertType.NONE)

        # Verify store calls
        expected_calls = [
            call(70, base_ts),
            call(45, base_ts + 5),
            call(160, base_ts + 10),
            call(80, base_ts + 15),
        ]
        self.mock_store.save_measurement.assert_has_calls(expected_calls)
        self.assertEqual(self.mock_store.save_measurement.call_count, 4)
        self.assertEqual(self.mock_logger.info.call_count, 8) # 4 saves + 4 processed logs

    def test_stream_invalid_bpm(self):
        """Test handling of out-of-range BPMs in the stream."""
        base_ts = int(time.time())
        mock_requests = [
            pb2.HeartRateRequest(bpm=75, timestamp=base_ts),      # Valid
            pb2.HeartRateRequest(bpm=35, timestamp=base_ts + 5),  # Invalid Low
            pb2.HeartRateRequest(bpm=185, timestamp=base_ts + 10), # Invalid High
        ]
        mock_iterator = iter(mock_requests)
        self.mock_store.save_measurement.return_value = "id_75" # Only one valid save

        responses = list(self.handler.stream(mock_iterator, self.mock_context))

        self.assertEqual(len(responses), 3)

        # Resp 1 (75) - Valid
        self.assertTrue(responses[0].success)
        # Resp 2 (35) - Invalid
        self.assertFalse(responses[1].success)
        self.assertEqual(responses[1].error, "Heart rate out of typical range for an adult")
        # Resp 3 (185) - Invalid
        self.assertFalse(responses[2].success)
        self.assertEqual(responses[2].error, "Heart rate out of typical range for an adult")

        # Verify store was only called for the valid measurement
        self.mock_store.save_measurement.assert_called_once_with(75, base_ts)
        self.assertEqual(self.mock_logger.warning.call_count, 2) # Warnings for invalid BPMs

    def test_stream_exception_in_store(self):
        """Test handling exceptions from the data store during stream processing."""
        base_ts = int(time.time())
        mock_requests = [
            pb2.HeartRateRequest(bpm=80, timestamp=base_ts),      # This one will cause the exception
            pb2.HeartRateRequest(bpm=85, timestamp=base_ts + 5),  # This one should not be processed
        ]
        mock_iterator = iter(mock_requests)

        self.mock_store.save_measurement.side_effect = Exception("Database write error")

        responses = list(self.handler.stream(mock_iterator, self.mock_context))
        # Should get one error response back
        self.assertFalse(responses[0].success)
        self.assertEqual(responses[0].error, "Internal server error processing measurement")
        self.assertFalse(responses[0].alert_triggered)
        self.assertEqual(responses[0].alert_type, pb2.AlertType.NONE)

        # Verify store was called once (and failed)
        self.mock_store.save_measurement.assert_called_once_with(80, base_ts)
        self.mock_logger.error.assert_called_once()

    def test_stream_empty_input(self):
        """Test handling an empty request iterator."""
        mock_requests = []
        mock_iterator = iter(mock_requests)

        responses = list(self.handler.stream(mock_iterator, self.mock_context))

        self.assertEqual(len(responses), 0)
        self.mock_store.save_measurement.assert_not_called()

if __name__ == '__main__':
    unittest.main()
