'''
Establishes a bidirectional stream for continuous heart rate
monitoring, allowing the client to stream measurements and receive immediate
feedback.
'''
from generated import heartrate_service_pb2 as pb2
from src.utils import logger, data_store, validator

class StreamHeartRateHandler:
    def __init__(self):
        self.log = logger.get_logger(__name__)
        self.store = data_store.get_data_store()

    def stream(self, request_iterator, context):
        for request in request_iterator:
            try:
                bpm = request.bpm
                timestamp = request.timestamp

                # Validate heart rate using our validator module
                if not validator.is_valid_heart_rate(bpm):
                    self.log.warning("Received out-of-range heart rate: %d", bpm)
                    yield pb2.HeartRateResponse(
                        success=False,
                        error="Heart rate out of typical range for an adult",
                        alert_triggered=False,
                        alert_type=pb2.AlertType.NONE
                    )
                    continue

                # Save the bpm measurement
                measurement_id = self.store.save_measurement(bpm, timestamp)
                self.log.info("StreamHeartRateHandler: Saved bpm measurement with ID %s for bpm %d at %s", measurement_id, bpm, timestamp)

                # Check for alerts using validator
                alert_triggered = validator.is_low_heart_rate(bpm) or validator.is_high_heart_rate(bpm)
                alert_type = (pb2.AlertType.LOW_HEART_RATE if validator.is_low_heart_rate(bpm)
                           else pb2.AlertType.HIGH_HEART_RATE if validator.is_high_heart_rate(bpm)
                           else pb2.AlertType.NONE)

                self.log.info("StreamHeartRateHandler: Processed bpm %d (measurement id: %s) with alert %s", bpm, measurement_id, alert_triggered)
                yield pb2.HeartRateResponse(
                    success=True,
                    error="",
                    alert_triggered=alert_triggered,
                    alert_type=alert_type
                )
            except Exception as e:
                self.log.error("StreamHeartRateHandler: Error processing BPM measurement: %s", str(e))
                yield pb2.HeartRateResponse(
                    success=False,
                    error="Internal server error processing measurement",
                    alert_triggered=False,
                    alert_type=pb2.AlertType.NONE
                )
                break
